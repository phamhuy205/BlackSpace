from app import create_app, db
from app.utils.db_sync import sync_movies_from_json
   
app = create_app()
with app.app_context():
    print("--- Đang bắt đầu đồng bộ phim từ JSON vào Supabase ---")
    sync_movies_from_json(app)
    print("--- Đồng bộ hoàn tất! ---")