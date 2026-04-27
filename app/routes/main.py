from datetime import datetime

from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from sqlalchemy import func
from app.models import Movie, Comment, WatchHistory
from app import db

bp = Blueprint("main", __name__)

@bp.route("/")
def home():
    all_movies = Movie.query.all()
    # Featured movie is Avengers: Endgame (or the first one if not found)
    featured_movie = Movie.query.filter_by(title="Avengers: Endgame").first()
    if not featured_movie and all_movies:
        featured_movie = all_movies[0]
    
    # Exclude featured movie from the main list
    movies_list = [m.to_dict() for m in all_movies if m.id != (featured_movie.id if featured_movie else None)]
    
    return render_template("index.html", 
                           featured_movie=featured_movie.to_dict() if featured_movie else None,
                           movies=movies_list, 
                           user=current_user)

@bp.route("/search")
def search():
    """Tìm kiếm phim"""
    query = request.args.get('q', '').strip()
    if not query:
        return render_template("index.html", movies=[], user=current_user, page_title="Kết quả tìm kiếm")
    
    # Search in title, cast, and director
    search_pattern = f"%{query}%"
    movies = Movie.query.filter(
        (Movie.title.ilike(search_pattern)) | 
        (Movie.cast.ilike(search_pattern)) | 
        (Movie.director.ilike(search_pattern)) |
        (Movie.genre.ilike(search_pattern))
    ).all()
    
    return render_template("index.html", 
                           movies=[m.to_dict() for m in movies], 
                           user=current_user, 
                           page_title=f"Kết quả cho: '{query}'")

@bp.route("/api/suggestions")
def suggestions():
    """API trả về gợi ý tìm kiếm nhanh"""
    query = request.args.get('q', '').strip()
    if len(query) < 2:
        return jsonify([])
    
    # Lấy top 5 phim khớp với từ khóa
    movies = Movie.query.filter(Movie.title.ilike(f"%{query}%")).limit(5).all()
    results = []
    for m in movies:
        results.append({
            "title": m.title,
            "poster": m.poster,
            "url": f"/info/{m.title}"
        })
    return jsonify(results)

@bp.route("/info/<title>")
def info(title):
    """Trang thông tin chi tiết phim"""
    movie = Movie.query.filter(func.lower(Movie.title) == title.lower()).first()
    if not movie:
        return render_template("404.html"), 404
    
    # Check if movie is favorited by current user
    is_favorite = False
    if current_user.is_authenticated:
        is_favorite = movie in current_user.favorite_movies

    # Mock actors data (in real app, fetch from actor.json or db)
    import json
    import os
    actors_data = []
    actor_json_path = os.path.join(os.getcwd(), 'data', 'actor.json')
    if os.path.exists(actor_json_path):
        with open(actor_json_path, 'r', encoding='utf-8') as f:
            all_actors = json.load(f)
            # Filter actors/director based on movie.cast and movie.director strings
            movie_cast = [name.strip() for name in (movie.cast or "").split(",")]
            movie_directors = [name.strip() for name in (movie.director or "").split(",")]
            
            actors_data = [a for a in all_actors if a['name'] in movie_cast or a['name'] in movie_directors]

    return render_template("info.html", movie=movie.to_dict(), actors=actors_data, is_favorite=is_favorite)

@bp.route("/phim-moi")
def phim_moi():
    """Hiển thị phim mới"""
    movies = Movie.query.filter_by(is_new=True).all()
    return render_template("index.html", movies=[m.to_dict() for m in movies], user=current_user, page_title="Phim Mới")

@bp.route("/phim-chieu-rap")
def phim_chieu_rap():
    """Hiển thị phim chiếu rạp"""
    movies = Movie.query.filter(func.lower(Movie.category) == "phim chiếu rạp").all()
    return render_template("index.html", movies=[m.to_dict() for m in movies], user=current_user, page_title="Phim Chiếu Rạp")

@bp.route("/the-loai/<genre>")
def the_loai(genre):
    """Hiển thị phim theo thể loại"""
    movies = Movie.query.filter(func.lower(Movie.genre) == genre.lower()).all()
    return render_template("index.html", movies=[m.to_dict() for m in movies], user=current_user, page_title=f"Thể loại: {genre}")

@bp.route("/phim-le")
def phim_le():
    """Hiển thị phim lẻ"""
    movies = Movie.query.filter(func.lower(Movie.type) == "phim lẻ").all()
    return render_template("index.html", movies=[m.to_dict() for m in movies], user=current_user, page_title="Phim Lẻ")

@bp.route("/phim-bo")
def phim_bo():
    """Hiển thị phim bộ"""
    movies = Movie.query.filter(func.lower(Movie.type) == "phim bộ").all()
    return render_template("index.html", movies=[m.to_dict() for m in movies], user=current_user, page_title="Phim Bộ")

@bp.route("/category/<category>")
def category_page(category):
    movies = Movie.query.filter(func.lower(Movie.category) == category.lower()).all()
    return render_template("index.html", movies=[m.to_dict() for m in movies], user=current_user, page_title=category)

@bp.route("/type/<type>")
def type_page(type):
    movies = Movie.query.filter(func.lower(Movie.type) == type.lower()).all()
    return render_template("index.html", movies=[m.to_dict() for m in movies], user=current_user, page_title=type)

from app.utils.video_utils import get_embed_url

@bp.route("/watch/<title>")
def watch(title):
    # Lấy thông tin phim
    movie = Movie.query.filter(func.lower(Movie.title) == title.lower()).first()
    if not movie:
        return render_template("404.html"), 404
    
    # Xử lý tập phim (nếu là phim bộ)
    ep_number = request.args.get('ep', type=int)
    current_episode = None
    
    if movie.type == 'Phim bộ' and movie.episodes:
        if ep_number:
            current_episode = next((e for e in movie.episodes if e.episode_number == ep_number), movie.episodes[0])
        else:
            current_episode = movie.episodes[0]
            
    # Chuyển đổi link sang dạng embed để tránh lỗi Drive/DoodStream
    movie_data = movie.to_dict()
    if current_episode:
        movie_data['current_url'] = get_embed_url(current_episode.url)
        movie_data['current_ep'] = current_episode.episode_number
    else:
        movie_data['current_url'] = get_embed_url(movie.url)
        movie_data['current_ep'] = None

    # Record watch history if user is logged in
    if current_user.is_authenticated:
        history = WatchHistory.query.filter_by(user_id=current_user.id, movie_id=movie.id).order_by(WatchHistory.watched_at.desc()).first()
        if not history or (datetime.utcnow() - history.watched_at).total_seconds() > 600:
            new_history = WatchHistory(user_id=current_user.id, movie_id=movie.id)
            db.session.add(new_history)
            db.session.commit()
        
    return render_template("watch.html", movie=movie_data)

@bp.route("/api/favorite/toggle", methods=["POST"])
@login_required
def toggle_favorite():
    data = request.get_json()
    movie_id = data.get("movie_id")
    if not movie_id:
        return jsonify({"error": "Movie ID is required"}), 400
    
    movie = Movie.query.get(movie_id)
    if not movie:
        return jsonify({"error": "Movie not found"}), 404
    
    if movie in current_user.favorite_movies:
        current_user.favorite_movies.remove(movie)
        is_favorite = False
    else:
        current_user.favorite_movies.append(movie)
        is_favorite = True
    
    db.session.commit()
    return jsonify({"success": True, "is_favorite": is_favorite})

@bp.route("/api/movie/<title>")
def get_movie(title):
    """API endpoint để lấy thông tin phim"""
    movie = Movie.query.filter(func.lower(Movie.title) == title.lower()).first()
    if movie:
        return jsonify(movie.to_dict())
    return jsonify({"error": "Phim không tồn tại"}), 404

@bp.route("/api/comments/<int:movie_id>", methods=["GET"])
def get_comments(movie_id):
    """API endpoint để lấy bình luận của phim"""
    comments = Comment.query.filter_by(movie_id=movie_id).order_by(Comment.created_at.desc()).all()
    return jsonify([comment.to_dict() for comment in comments])

@bp.route("/api/comments", methods=["POST"])
@login_required
def add_comment():
    """API endpoint để thêm bình luận"""
    data = request.get_json()
    movie_id = data.get("movie_id")
    content = data.get("content", "").strip()
    
    if not movie_id or not content:
        return jsonify({"error": "Movie ID và content là bắt buộc"}), 400
    
    # Verify movie exists
    movie = Movie.query.get(movie_id)
    if not movie:
        return jsonify({"error": "Phim không tồn tại"}), 404
    
    comment = Comment(
        movie_id=movie_id,
        user_id=current_user.id,
        content=content
    )
    
    db.session.add(comment)
    db.session.commit()
    
    return jsonify(comment.to_dict()), 201
