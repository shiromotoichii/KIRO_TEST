"""
Flask extensions -  расширения Flask, не зависящие от приложения.
"""
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.login_message = "ログインが必要です。"
login_manager.login_message_category = "warning"