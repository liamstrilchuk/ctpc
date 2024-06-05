from flask import Flask
from flask_migrate import Migrate

from models import User, db
from views.views import views
from setup import bcrypt, login_manager

def setup_app():
	app = Flask(__name__)
	app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
	app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = True
	app.secret_key = "secret"

	app.jinja_env.auto_reload = True
	app.config["TEMPLATES_AUTO_RELOAD"] = True

	migrate = Migrate()

	db.init_app(app)
	migrate.init_app(app, db)
	bcrypt.init_app(app)
	login_manager.init_app(app)

	return app

app = setup_app()
app.register_blueprint(views)

@login_manager.user_loader
def load_user(user_id):
	return User.query.get(user_id)

if __name__ == "__main__":
	app.run(debug=True)