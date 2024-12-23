from flask import Blueprint, render_template, redirect, request
from flask_login import current_user

from models import Team, User, UserRole, db
from setup import bcrypt
from util import generate_random_password
import handle_objects

teacher = Blueprint("teacher", __name__, template_folder="templates")

def teacher_required(func):
	def wrapper(*args, **kwargs):
		if not current_user.is_authenticated:
			return redirect("/")

		if not current_user.role.name == "teacher" and not current_user.role.name == "admin" or current_user.school is None:
			return redirect("/")

		return func(*args, **kwargs)
	
	wrapper.__name__ = func.__name__
	
	return wrapper

def teacher_controls(teacher, student):
	if student is None or not student.school == teacher.school or not student.role.name == "student" or not teacher.role.name in ("teacher", "admin"):
		return False

	return True

@teacher.route("/teacher")
@teacher_required
def teacher_view():	
	teams = Team.query.filter_by(school=current_user.school).all()
	unassigned = User.query.filter_by(school=current_user.school, team_id=None, role=UserRole.query.filter_by(name="student").first()).all()

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
		role_id=UserRole.query.filter_by(name="student").first().id
	)
	db.session.add(user)
	db.session.commit()

	return render_template("user-created.html", username=username.lower(), password=random_password)

@teacher.route("/teacher/assign/<string:username>", methods=["GET", "POST"])
@teacher_required
def assign_student(username):
	user = User.query.filter_by(username=username).first()
	if not teacher_controls(current_user, user):
		return redirect("/teacher")
	
	teams = Team.query.filter_by(school=current_user.school).all()

	if request.method == "GET":
		return render_template("assign-student.html", user=user, teams=teams)

	team_id = request.form["team"]
	if not team_id:
		return redirect("/teacher")
	
	team = Team.query.filter_by(id=team_id).first()
	if team is None or not team.school == current_user.school:
		return redirect("/teacher")
	
	if len(team.members) >= 6:
		return render_template("assign-student.html", user=user, teams=teams, error="That team is already full.")

	user.team_id = team_id
	db.session.commit()

	return redirect("/teacher")

@teacher.route("/teacher/unassign/<string:username>")
@teacher_required
def unassign_student(username):
	user = User.query.filter_by(username=username).first()
	if not teacher_controls(current_user, user):
		return redirect("/teacher")

	user.team_id = None
	db.session.commit()

	return redirect("/teacher")

@teacher.route("/teacher/delete/<string:username>", methods=["GET", "POST"])
@teacher_required
def delete_student(username):
	user = User.query.filter_by(username=username).first()
	if not teacher_controls(current_user, user):
		return redirect("/teacher")
	
	if request.method == "GET":
		return render_template("confirm-delete.html", text=user.username, type="user")

	handle_objects.delete_user(user)

	return redirect("/teacher")

@teacher.route("/teacher/reset-password/<string:username>", methods=["GET", "POST"])
@teacher_required
def reset_password(username):
	user = User.query.filter_by(username=username).first()
	if not teacher_controls(current_user, user) and not current_user.role.name == "admin":
		return redirect("/teacher")

	if request.method == "GET":
		return render_template("confirm-reset.html", user=user)

	random_password = generate_random_password()
	user.password = bcrypt.generate_password_hash(random_password)
	db.session.commit()

	return render_template("user-created.html", username=username, password=random_password, text="Password reset successfully")

@teacher.route("/teacher/delete-team/<int:team_id>", methods=["GET", "POST"])
@teacher_required
def delete_team(team_id):
	team = Team.query.filter_by(id=team_id).first()
	if team is None or not team.school == current_user.school:
		return redirect("/teacher")

	if request.method == "GET":
		return render_template("confirm-delete.html", text=team.name, type="team")

	handle_objects.delete_team(team)

	return redirect("/teacher")