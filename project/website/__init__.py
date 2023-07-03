from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import pymysql
from os import path
from flask_login import LoginManager
import string

db = SQLAlchemy()

u = 'root'
p = ''
s = 'localhost'
port = '3306'
n = 'projectFYP'

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'bzdfbsdfbwbreb'
    app.config['SQLALCHEMY_DATABASE_URI'] = f''
    # f'mysql+pymysql://root:@localhost:3306/projectfyp'
    # f''
    # f''
    app.config['MESSAGE_FLASHING_OPTIONS'] = {'duration': 5}
    db.init_app(app)
        
    from .views import views
    from .auth import auth
    from .admin import admin
    from .manager import manager
    from .employee import employee
    
    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(auth, url_prefix='/')
    app.register_blueprint(admin, url_prefix='/')
    app.register_blueprint(manager, url_prefix='/')
    app.register_blueprint(employee, url_prefix='/')
    
    from .models import User
    
    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)
    
    @login_manager.user_loader
    def load_user(id):
        return User.query.get(id)
    
    return app
