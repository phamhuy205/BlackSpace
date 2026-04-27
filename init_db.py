import os
from app import create_app, db
from dotenv import load_dotenv
load_dotenv()
app = create_app()
with app.app_context():
    uri = app.config["SQLALCHEMY_DATABASE_URI"]
    print(f"Using database URI: {uri}")
    if "sqlite" in uri:
        print("Vẫn đang sử dụng SQLite, hãy kiểm tra lại DATABASE_URL trong .env")
    else:
        try:
                db.create_all()
                print("Database initialized successfully.")
        except Exception as e:
                print(f"Error initializing database: {e}")