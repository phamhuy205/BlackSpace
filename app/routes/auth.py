from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import URLSafeTimedSerializer
from flask_mail import Message

from app import db, bcrypt, login_manager, oauth, mail
from app.models import User

bp = Blueprint("auth", __name__)

def generate_verification_token(email):
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    return serializer.dumps(email, salt='google-verify-salt')

def confirm_verification_token(token, expiration=3600):
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    try:
        email = serializer.loads(
            token,
            salt='google-verify-salt',
            max_age=expiration
        )
    except:
        return False
    return email

def send_verification_email(user_email):
    token = generate_verification_token(user_email)
    verify_url = url_for('auth.verify_google', token=token, _external=True)
    msg = Message(
        "Xác nhận đăng nhập Google - BlackSpacePro",
        recipients=[user_email]
    )
    msg.body = f"Chào bạn,\n\nBạn vừa thực hiện đăng nhập bằng Google tại BlackSpacePro lần đầu tiên. Vui lòng nhấn vào liên kết bên dưới để xác nhận và đăng nhập:\n\n{verify_url}\n\nLiên kết này sẽ hết hạn sau 1 giờ."
    mail.send(msg)

@bp.route("/google/login")
def google_login():
    redirect_uri = url_for('auth.google_authorize', _external=True)
    return oauth.google.authorize_redirect(redirect_uri)

@bp.route("/google/authorize")
def google_authorize():
    token = oauth.google.authorize_access_token()
    user_info = token.get('userinfo')
    if not user_info:
        flash("Không thể lấy thông tin từ Google.", "error")
        return redirect(url_for('auth.login'))
    
    email = user_info.get('email')
    user = User.query.filter_by(email=email).first()

    if user:
        # User exists, log them in directly
        login_user(user)
        flash(f"Chào mừng {user.username} quay lại!", "success")
        return redirect(url_for('main.home'))
    else:
        # New user, send verification email
        send_verification_email(email)
        flash("Một liên kết xác nhận đã được gửi đến Gmail của bạn. Vui lòng kiểm tra để hoàn tất đăng nhập lần đầu.", "info")
        return redirect(url_for('auth.login'))

@bp.route("/verify_google/<token>")
def verify_google(token):
    email = confirm_verification_token(token)
    if not email:
        flash("Liên kết xác nhận không hợp lệ hoặc đã hết hạn.", "error")
        return redirect(url_for('auth.login'))
    
    user = User.query.filter_by(email=email).first()
    if not user:
        # Create new user
        username = email.split('@')[0]
        # Check if username exists, if so append something
        base_username = username
        counter = 1
        while User.query.filter_by(username=username).first():
            username = f"{base_username}{counter}"
            counter += 1
            
        new_user = User(
            username=username,
            email=email,
            password=generate_password_hash(current_app.secret_key), # Random password
            avatar="/static/images/default_avatar.svg"
        )
        db.session.add(new_user)
        db.session.commit()
        user = new_user
    
    login_user(user)
    flash("Đăng nhập bằng Google thành công!", "success")
    return redirect(url_for('main.home'))

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
