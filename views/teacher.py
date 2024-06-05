from flask import Blueprint, render_template, redirect, request
from flask_login import current_user

from models import Team, User, db
from setup import bcrypt
from util import generate_random_password

teacher = Blueprint("teacher", __name__, template_folder="templates")

def teacher_required(func):
	def wrapper(*args, **kwargs):
		if not current_user.is_authenticated:
			return redirect("/")

		if not current_user.role == "teacher":
			return redirect("/")

		return func(*args, **kwargs)
	
	wrapper.__name__ = func.__name__
	
	return wrapper

@teacher.route("/teacher")
@teacher_required
def teacher_view():	
	teams = Team.query.filter_by(school=current_user.school).all()
	unassigned = User.query.filter_by(school=current_user.school, team_id=None, role="student").all()

	return render_template("teacher.html", teams=teams, unassigned=unassigned)

@teacher.route("/teacher/create-team", methods=["GET", "POST"])
@teacher_required
def create_team():
	if request.method == "GET":
		return render_template("create-team.html")

	team_name = request.form["name"]

	existing_team = Team.query.filter_by(name=team_name, school=current_user.school).first()
	if existing_team is not None or not team_name:
		return render_template("create-team.html", error="Team with that name already exists")
	
	team = Team(team_name, current_user.school.id)
	db.session.add(team)
	db.session.commit()

	return redirect("/teacher")

@teacher.route("/teacher/register-student", methods=["GET", "POST"])
@teacher_required
def register_student():
	if request.method == "GET":
		return render_template("register-student.html")
	
	first = request.form["name"]
	last = request.form["surname"]

	if not first or not last:
		return render_template("register-student.html", error="Please fill out all fields")

	username = first[:3] + last[:5]
	number = 1

	while True:
		if User.query.filter_by(username=(username + str(number)).lower()).first() is None:
			break

		number += 1

	username += str(number)

	random_password = generate_random_password()
	user = User(
		username=username.lower(),
		password=bcrypt.generate_password_hash(random_password),
		school_id=current_user.school_id,
		role="student"
	)
	db.session.add(user)
	db.session.commit()

	return render_template("user-created.html", username=username.lower(), password=random_password)

@teacher.route("/teacher/assign/<string:username>", methods=["GET", "POST"])
@teacher_required
def assign_student(username):
	user = User.query.filter_by(username=username).first()
	if user is None or not user.school == current_user.school or not user.role == "student":
		return redirect("/teacher")

	if request.method == "GET":
		teams = Team.query.filter_by(school=current_user.school).all()
		return render_template("assign-student.html", user=user, teams=teams)

	team_id = request.form["team"]
	if not team_id:
		return redirect("/teacher")

	user.team_id = team_id
	db.session.commit()

	return redirect("/teacher")