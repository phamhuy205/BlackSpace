from flask import Blueprint, render_template, request, redirect, url_for,flash
from flask_login import login_user, logout_user,login_required
from werkzeug.security import generate_password_hash, check_password_hash

from app import db, bcrypt, login_manager
from app.models import User

bp = Blueprint("auth", __name__)

@bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")
        if User.query.filter_by(username=username).first():
            flash("Tên đăng nhập đã tồn tại!", "error")
            return redirect(url_for("auth.register"))
        if User.query.filter_by(email=email).first():
            flash("Email đã được sử dụng!", "error")
            return redirect(url_for("auth.register"))
        hashed_password = generate_password_hash(password, method="pbkdf2:sha256")
        new_user = User(
            username=username,
            email=email,
            password=hashed_password,
            avatar="/static/images/default_avatar.svg"
        )
        db.session.add(new_user)
        db.session.commit()
        flash("Đăng ký thành công! Hãy đăng nhập.", "success")
        return redirect(url_for("auth.login"))
    return render_template("register.html")
@bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        remember = True if request.form.get("remember") else False

        user = User.query.filter_by(username=username).first()

        if not user or not check_password_hash(user.password, password):
            flash("Sai tên đăng nhập hoặc mật khẩu!", "error")
            return redirect(url_for("auth.login"))

        # ✅ Nếu đăng nhập thành công
        login_user(user, remember=remember)
        flash(f"Chào mừng {username} quay lại!", "success")

        # ✅ Chuyển hướng về trang chủ
        return redirect(url_for("main.home"))

    return render_template("login.html")

@bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Đã đăng xuất thành công!", "info")
    return redirect(url_for("auth.login"))
@login_manager.user_loader
def load_user(user_id):
    # Flask-Login sẽ dùng hàm này để lấy user theo id
    return User.query.get(int(user_id))

@bp.route("/reset_password", methods=["GET", "POST"])
def reset_password():
    if request.method == "POST":
        email = request.form.get("email")
        flash(f"Liên kết đặt lại mật khẩu đã được gửi đến {email}.", "info")
        return redirect(url_for("auth.login"))
    return render_template("reset_password.html")
