from flask import Blueprint, render_template, request, jsonify, current_app, session
import json
import os
import re
import google.generativeai as genai

bp = Blueprint("ai", __name__)

def get_model():
    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
    GEMINI_MODEL_NAME = os.environ.get("GEMINI_MODEL_NAME", "gemini-2.0-flash-latest")
    
    if not GEMINI_API_KEY:
        return None
        
    genai.configure(api_key=GEMINI_API_KEY)
    return genai.GenerativeModel(
        model_name=GEMINI_MODEL_NAME,
        system_instruction=(
            "Bạn là trợ lý ảo thân thiện của website Black Space 🎬. "
            "Nhiệm vụ của bạn là tư vấn phim từ dữ liệu được cung cấp. "
            "Bạn có thể chào hỏi và trả lời các câu hỏi chung về website tự nhiên."
        )
    )

def search_movies_by_keyword(message):
    # Import inside function to avoid circular import
    from app.models import Movie
    
    message = message.lower()
    movies = Movie.query.all()
    results = []
    
    is_asking_new = any(word in message for word in ["mới", "mới nhất", "vừa ra", "update"])
    is_asking_series = any(word in message for word in ["phim bộ", "nhiều tập", "series"])
    is_asking_movie = any(word in message for word in ["phim lẻ", "một tập", "movie"])

    stop_words = ["phim", "xem", "tôi", "muốn", "thích", "cần", "tìm", "có", "là", "gì", "nào", "cho", "hỏi"]
    words = [w for w in message.split() if w not in stop_words]
    
    if not words:
        words = message.split()

    for m in movies:
        score = 0
        target_text = f" {m.title} {m.genre} {m.description} {m.type} ".lower()
        target_text = re.sub(r'[^a-zA-Z0-9\sáàảãạăắằẳẵặâấầẩẫậéèẻẽẹêếềểễệíìỉĩịóòỏõọôốồổỗộơớờởỡợúùủũụưứừửữựýỳỷỹỵđ]', ' ', target_text)
        
        if is_asking_new and m.is_new:
            score += 5
        if is_asking_series and m.type and "bộ" in m.type.lower():
            score += 4
        if is_asking_movie and m.type and "lẻ" in m.type.lower():
            score += 4

        for word in words:
            if f" {word} " in target_text:
                score += 3
            elif len(word) > 3 and word in target_text:
                score += 1
            if word in m.title.lower():
                score += 2
        
        if score > 0:
            results.append((score, m))

    results.sort(key=lambda x: x[0], reverse=True)
    top_matches = results[:5]  # Giảm xuống 5 phim để tiết kiệm token
    
    if is_asking_new and len([r for r in top_matches if r[0] > 0]) < 2:
        new_movies = Movie.query.filter_by(is_new=True).limit(3).all()
        seen_ids = [r[1].id for r in top_matches]
        for m in new_movies:
            if m.id not in seen_ids:
                top_matches.append((5, m))

    # Trả về dữ liệu tinh gọn
    return [{
        "t": r[1].title, 
        "g": r[1].genre, 
        "d": (r[1].description[:150] + "...") if r[1].description and len(r[1].description) > 150 else r[1].description,
        "n": r[1].is_new, 
        "tp": r[1].type
    } for r in top_matches]

def build_prompt(message, movies):
    # Nén JSON tối đa
    movies_json = json.dumps(movies, ensure_ascii=False, separators=(',', ':'))
    return f"User: {message}\nData: {movies_json}\nHD: Dựa vào Data, tư vấn ngắn gọn, dùng markdown."

@bp.route("/ai", methods=["GET", "POST"])
def ai_page():
    result = ""
    if request.method == "POST":
        prompt = request.form.get("prompt")
        model = get_model()
        if not prompt:
            result = "Vui lòng nhập câu hỏi."
        elif not model:
            result = "Lỗi: Chưa cấu hình GEMINI_API_KEY."
        else:
            try:
                simple_list = search_movies_by_keyword(prompt)
                full_prompt = build_prompt(prompt, simple_list)
                response = model.generate_content(full_prompt)
                result = getattr(response, "text", "Không có câu trả lời.")
            except Exception as e:
                result = f"Lỗi: {str(e)}"
    return render_template("ai.html", result=result)

@bp.route("/api/ai_chat", methods=["POST"])
@bp.route("/api/ai_suggest", methods=["POST"])
def ai_chat():
    try:
        data = request.get_json()
        message = data.get("message") or data.get("query", "")
        model = get_model()

        if not message:
            return jsonify({"reply": "Chào bạn! Mình có thể giúp gì cho bạn? 😊"}), 200
        if not model:
            return jsonify({"reply": "AI đang bận, thử lại sau nhé!"}), 200

        # Truncate Chat History (Lấy 6 tin nhắn gần nhất từ session)
        history = session.get("chat_history", [])
        
        movies = []
        if any(x in message.lower() for x in ["phim", "mới", "hay", "tìm", "gợi ý"]):
            movies = search_movies_by_keyword(message)

        # Chỉ gửi phần cần thiết (History Context + Message + Minimized Data)
        hist_context = "\n".join([f"{h['r']}: {h['c']}" for h in history])
        prompt = f"{hist_context}\nU: {message}\nData: {json.dumps(movies, ensure_ascii=False, separators=(',', ':'))}\nHD: Ngắn, Markdown."

        response = model.generate_content(
            prompt,
            generation_config={"temperature": 0.7, "max_output_tokens": 500}
        )
        reply = getattr(response, "text", "...")

        # Update and Truncate history
        history.append({"r": "U", "c": message})
        history.append({"r": "A", "c": reply})
        session["chat_history"] = history[-6:]
        
        return jsonify({"reply": reply})
    except Exception as e:
        print("AI ERROR:", e)
        return jsonify({"reply": "Hệ thống AI đang gặp chút sự cố 😅"})
