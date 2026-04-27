from app import create_app, db
from app.models import User, Movie, WatchHistory, favorites

app = create_app()
with app.app_context():
    print("Đang cập nhật cơ sở dữ liệu...")
    # Tạo tất cả các bảng chưa tồn tại
    db.create_all()
    print("Cập nhật hoàn tất!")
