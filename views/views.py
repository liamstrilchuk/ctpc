from flask import Blueprint
from flask_login import login_required

from . import index, login, teacher, profile

views = Blueprint("views", __name__, template_folder="templates")

@views.route("/")
def index_view():
	return index.index_view()

@views.route("/user/<string:username>")
def profile_view(username):
	return profile.profile_view(username)

@views.route("/login", methods=["GET", "POST"])
def login_view():
	return login.login_view()

@views.route("/logout")
@login_required
def logout_view():
	return login.logout_view()

views.register_blueprint(teacher.teacher)