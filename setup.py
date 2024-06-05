from flask_bcrypt import Bcrypt
from flask_login import LoginManager

login_manager = LoginManager()
login_manager.login_view = "views.login_view"

bcrypt = Bcrypt()