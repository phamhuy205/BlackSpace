from flask import Blueprint, render_template, request, redirect, url_for, flash, abort, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import Movie, Episode, User, Comment
import json

bp = Blueprint("admin", __name__, url_prefix="/admin")

# Custom decorator to check for admin rights
def admin_required(f):
    from functools import wraps
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin:
            flash("Bạn không có quyền truy cập trang này.", "error")
            return redirect(url_for("main.home"))
        return f(*args, **kwargs)
    return decorated_function

@bp.route("/")
@admin_required
def dashboard():
    movies = Movie.query.order_by(Movie.id.desc()).all()
    users = User.query.order_by(User.id.desc()).all()
    return render_template("admin/dashboard.html", movies=movies, users=users)

# --- QUẢN LÝ PHIM ---

@bp.route("/movie/edit/<int:id>", methods=["POST"])
@admin_required
def edit_movie(id):
    movie = Movie.query.get_or_404(id)
    movie.title = request.form.get("title")
    movie.genre = request.form.get("genre")
    movie.type = request.form.get("type")
    movie.category = request.form.get("category")
    movie.year = request.form.get("year")
    movie.poster = request.form.get("poster")
    movie.url = request.form.get("url")
    movie.description = request.form.get("description")
    movie.is_new = "is_new" in request.form
    
    db.session.commit()
    flash(f"Đã cập nhật phim '{movie.title}' thành công!", "success")
    return redirect(url_for("admin.dashboard"))

@bp.route("/movie/delete/<int:id>", methods=["POST"])
@admin_required
def delete_movie(id):
    movie = Movie.query.get_or_404(id)
    title = movie.title
    db.session.delete(movie)
    db.session.commit()
    flash(f"Đã xóa phim '{title}' thành công!", "success")
    return redirect(url_for("admin.dashboard"))

# --- QUẢN LÝ NGƯỜI DÙNG ---

@bp.route("/user/edit/<int:id>", methods=["POST"])
@admin_required
def edit_user(id):
    user = User.query.get_or_404(id)
    # Không cho phép tự bỏ quyền admin của chính mình qua đây để tránh lock-out
    if user.id == current_user.id and "is_admin" not in request.form:
         flash("Bạn không thể tự bỏ quyền Admin của chính mình!", "error")
         return redirect(url_for("admin.dashboard"))
    
    user.username = request.form.get("username")
    user.email = request.form.get("email")
    user.is_admin = "is_admin" in request.form
    
    db.session.commit()
    flash(f"Đã cập nhật người dùng '{user.username}' thành công!", "success")
    return redirect(url_for("admin.dashboard"))

@bp.route("/user/delete/<int:id>", methods=["POST"])
@admin_required
def delete_user(id):
    if id == current_user.id:
        flash("Bạn không thể tự xóa chính mình!", "error")
        return redirect(url_for("admin.dashboard"))
        
    user = User.query.get_or_404(id)
    username = user.username
    db.session.delete(user)
    db.session.commit()
    flash(f"Đã xóa người dùng '{username}' thành công!", "success")
    return redirect(url_for("admin.dashboard"))

@bp.route("/sync-movies", methods=["POST"])
@admin_required
def sync_movies():
    try:
        from app.utils.db_sync import sync_movies_from_json
        from flask import current_app
        sync_movies_from_json(current_app)
        flash("Đã đồng bộ phim từ file JSON thành công!", "success")
    except Exception as e:
        flash(f"Lỗi khi đồng bộ: {str(e)}", "error")
    return redirect(url_for("admin.dashboard"))
