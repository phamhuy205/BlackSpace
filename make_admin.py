import sys
from app import create_app, db
from app.models import User

app = create_app()


def make_admin(username):
    with app.app_context():
        user = User.query.filter_by(username=username).first()
        if user:
            user.is_admin = True
            db.session.commit()
            app.logger.info("User '%s' is now an Admin!", username)
        else:
            app.logger.warning("User '%s' not found. Please register an account first.", username)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        username = input("Enter username to make admin: ")
    else:
        username = sys.argv[1]
    make_admin(username)
