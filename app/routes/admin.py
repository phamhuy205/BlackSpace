from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from app import db
from app.models import Movie, Episode

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
    movies = Movie.query.order_by(Movie.title).all()
    # Add a flag or message to the template context if needed, 
    # but the template can just show the list.
    return render_template("admin/dashboard.html", movies=movies)

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
