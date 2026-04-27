import json
import os
from app import db
from app.models import Movie, Episode

def sync_movies_from_json(app):
    """
    Reads movies from data/movies.json and syncs them to the database.
    Updates existing movies (by title), creates new ones, and DELETES those not in JSON.
    """
    json_path = os.path.join(app.root_path, '..', 'data', 'movies.json')
    
    if not os.path.exists(json_path):
        app.logger.warning("%s not found. Skipping movie sync.", json_path)
        return

    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            movies_data = json.load(f)
            
        app.logger.info("Found %d movies in JSON. Syncing...", len(movies_data))

        # 1. Get all titles from JSON
        json_titles = {m.get('title') for m in movies_data}

        # 2. Find movies in DB that are NOT in JSON and delete them
        existing_movies = Movie.query.all()
        for movie in existing_movies:
            if movie.title not in json_titles:
                app.logger.info("Deleting movie not in JSON: %s", movie.title)
                db.session.delete(movie)
        
        # Flush deletions
        db.session.flush()

        # 3. Update or Create movies from JSON
        for m_data in movies_data:
            # Try to find existing movie by title
            movie = Movie.query.filter_by(title=m_data.get('title')).first()
            
            if not movie:
                # Create new movie
                movie = Movie()
                db.session.add(movie)
                app.logger.info("Creating new movie: %s", m_data.get('title'))
            
            # Update fields
            movie.title = m_data.get('title')
            movie.genre = m_data.get('genre')
            movie.category = m_data.get('category')
            movie.type = m_data.get('type')
            movie.year = m_data.get('year')
            movie.url = m_data.get('url')
            movie.poster = m_data.get('poster')
            movie.description = m_data.get('description')
            movie.is_new = m_data.get('isNew', False) # JSON uses camelCase isNew
            movie.director = m_data.get('director')
            movie.cast = m_data.get('cast')
            
            # Flush to ensure movie has an ID before adding episodes
            db.session.flush()

            # Handle Episodes
            # Strategy: Delete existing episodes and re-add from JSON to ensure sync
            if movie.episodes:
                for ep in movie.episodes:
                    db.session.delete(ep)
            
            episodes_data = m_data.get('episodes', [])
            if episodes_data:
                for ep_data in episodes_data:
                    episode = Episode(
                        movie_id=movie.id,
                        episode_number=ep_data.get('episode'),
                        title=ep_data.get('title'),
                        url=ep_data.get('url'),
                        description=ep_data.get('description')
                    )
                    db.session.add(episode)

        db.session.commit()
        app.logger.info("Movies synced successfully!")

    except Exception as e:
        db.session.rollback()
        app.logger.exception("Error syncing movies")
