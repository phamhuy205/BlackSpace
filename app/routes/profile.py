import os
from flask import Blueprint, render_template, request, jsonify, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app.models import Movie, WatchHistory
from app import db

bp = Blueprint("profile", __name__)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@bp.route("/profile")
@login_required
def profile():
    history_entries = WatchHistory.query.filter_by(user_id=current_user.id).order_by(WatchHistory.watched_at.desc()).all()
    seen_ids = set()
    history = []
    for entry in history_entries:
        if entry.movie_id not in seen_ids:
            history.append(entry)
            seen_ids.add(entry.movie_id)
            if len(history) >= 10:
                break
                
    return render_template("profile.html", user=current_user, favorites=current_user.favorite_movies, history=history)

@bp.route("/api/profile/update", methods=["POST"])
@login_required
def update_profile():
    # Handle both JSON and Form Data
    if request.is_json:
        data = request.get_json()
        new_username = data.get("username")
        new_avatar = data.get("avatar")
    else:
        new_username = request.form.get("username")
        new_avatar = request.form.get("avatar") # This would be the URL if provided
        
        # Handle file upload
        if 'avatar_file' in request.files:
            file = request.files['avatar_file']
            if file and file.filename != '' and allowed_file(file.filename):
                filename = secure_filename(f"user_{current_user.id}_{file.filename}")
                upload_path = os.path.join(current_app.static_folder, 'uploads', 'avatars')
                
                # Create directory if it doesn't exist
                if not os.path.exists(upload_path):
                    os.makedirs(upload_path)
                
                file.save(os.path.join(upload_path, filename))
                new_avatar = f"/static/uploads/avatars/{filename}"

    if new_username:
        current_user.username = new_username
    if new_avatar:
        current_user.avatar = new_avatar
        
    db.session.commit()
    return jsonify({"success": True, "username": current_user.username, "avatar": current_user.avatar})
