import logging
from logging.handlers import RotatingFileHandler
import os


def setup_logging(app=None, log_file='logs/blackspace.log'):
    if not os.path.exists('logs'):
        os.makedirs('logs')

    handler = RotatingFileHandler(log_file, maxBytes=10 * 1024 * 1024, backupCount=5)
    formatter = logging.Formatter(
        '%(asctime)s %(levelname)s [%(name)s] %(message)s'
    )
    handler.setFormatter(formatter)
    handler.setLevel(logging.INFO)

    logger = logging.getLogger()
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        logger.addHandler(handler)

    if app:
        app.logger.handlers = logger.handlers
        app.logger.setLevel(logger.level)

    return logger
