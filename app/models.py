from app import db
from flask_login import UserMixin
from datetime import datetime

# Many-to-many table for favorites
favorites = db.Table('favorites',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('movie_id', db.Integer, db.ForeignKey('movie.id'), primary_key=True)
)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    avatar = db.Column(db.String(255), default="/static/images/default_avatar.svg")
    is_admin = db.Column(db.Boolean, default=False)
    
    # Favorites relationship
    favorite_movies = db.relationship('Movie', secondary=favorites, backref=db.backref('favorited_by', lazy='dynamic'))
    # Watch history relationship
    watch_history = db.relationship('WatchHistory', backref='user', lazy=True, cascade="all, delete-orphan")

class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    genre = db.Column(db.String(100))
    category = db.Column(db.String(100))  # e.g., 'Phim chiếu rạp', 'phim bộ'
    type = db.Column(db.String(50))  # 'Phim lẻ', 'Phim bộ'
    year = db.Column(db.Integer)
    url = db.Column(db.String(500))  # Main video URL or Trailer
    poster = db.Column(db.String(500))
    description = db.Column(db.Text)
    is_new = db.Column(db.Boolean, default=False)
    director = db.Column(db.String(255))
    cast = db.Column(db.String(500))
    
    # Relationships
    episodes = db.relationship('Episode', backref='movie', lazy=True, cascade="all, delete-orphan")
    comments = db.relationship('Comment', backref='movie', lazy=True, cascade="all, delete-orphan")

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'genre': self.genre,
            'category': self.category,
            'type': self.type,
            'year': self.year,
            'poster': self.poster,
            'description': self.description,
            'isNew': self.is_new,
            'url': self.url,
            'director': self.director,
            'cast': self.cast,
            'episodes': [ep.to_dict() for ep in self.episodes] if self.episodes else []
        }

class WatchHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    movie_id = db.Column(db.Integer, db.ForeignKey('movie.id'), nullable=False)
    watched_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    movie = db.relationship('Movie')

    def to_dict(self):
        return {
            'id': self.id,
            'movie': self.movie.to_dict(),
            'watched_at': self.watched_at.strftime('%d/%m/%Y %H:%M')
        }

class Episode(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    movie_id = db.Column(db.Integer, db.ForeignKey('movie.id'), nullable=False)
    episode_number = db.Column(db.Integer, nullable=False)
    title = db.Column(db.String(255))
    url = db.Column(db.String(500), nullable=False)
    description = db.Column(db.Text)

    def to_dict(self):
        return {
            'episode': self.episode_number,
            'title': self.title,
            'url': self.url,
            'description': self.description
        }

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Foreign Keys
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    movie_id = db.Column(db.Integer, db.ForeignKey('movie.id'), nullable=False)  # Changed from movie_title string
    
    # Relationships
    user = db.relationship('User', backref=db.backref('comments', lazy=True))
    
    def to_dict(self):
        return {
            'id': self.id,
            'movie_id': self.movie_id,
            'username': self.user.username,
            'avatar': self.user.avatar,
            'content': self.content,
            'created_at': self.created_at.strftime('%d/%m/%Y %H:%M')
        }
