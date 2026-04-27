import sys
from app import create_app, db
from app.models import User
from werkzeug.security import generate_password_hash

app = create_app()


def create_admin_account():
    with app.app_context():
        app.logger.info("--- TẠO TÀI KHOẢN QUẢN TRỊ VIÊN (ADMIN) ---")
        username = input("Nhập Username mới: ").strip()
        email = input("Nhập Email: ").strip()
        password = input("Nhập Password mới: ").strip()

        if not username or not email or not password:
            app.logger.error("Lỗi: Vui lòng nhập đầy đủ thông tin.")
            return

        user = User.query.filter_by(username=username).first()
        if user:
            app.logger.info("Người dùng '%s' đã tồn tại. Cập nhật mật khẩu và cấp quyền Admin.", username)
            user.password = generate_password_hash(password, method="pbkdf2:sha256")
            user.is_admin = True
            user.email = email
        else:
            app.logger.info("Đang tạo tài khoản Admin mới '%s'...", username)
            new_user = User(
                username=username,
                email=email,
                password=generate_password_hash(password, method="pbkdf2:sha256"),
                avatar="/static/images/default_avatar.svg",
                is_admin=True
            )
            db.session.add(new_user)

        db.session.commit()
        app.logger.info("Thành công! Đã tạo/cập nhật admin '%s'.", username)


if __name__ == "__main__":
    create_admin_account()
