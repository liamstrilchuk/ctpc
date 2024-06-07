from flask import Blueprint, render_template, request, redirect
from flask_login import current_user

from models import User, School, SchoolBoard, UserRole, db
from util import admin_required, generate_random_password, check_object_exists
from setup import bcrypt

manage = Blueprint("manage", __name__, template_folder="templates")

@manage.route("/admin/manage")
@admin_required
def manage_users():
	return render_template("manage-users.html")

@manage.route("/admin/add-board", methods=["GET", "POST"])
@admin_required
def add_board():
	if request.method == "GET":
		return render_template("add-board.html")
	
	board_name = request.form["name"]

	if SchoolBoard.query.filter_by(name=board_name).first() is not None:
		return render_template("add-board.html", error="Board with that name already exists")
	
	board = SchoolBoard(board_name)
	db.session.add(board)
	db.session.commit()
	
	return redirect("/admin")

@manage.route("/admin/add-school", methods=["GET", "POST"])
@admin_required
def add_school():
	boards = SchoolBoard.query.all()

	if request.method == "GET":
		return render_template("add-school.html", boards=boards)
	
	board_name = request.form["board"]
	school_name = request.form["name"]

	board = SchoolBoard.query.filter_by(name=board_name).first()

	if board is None:
		return render_template("add-school.html", boards=boards, error="There is no board with that name")
	
	existing_school = School.query.filter_by(name=school_name, school_board=board).first()

	if existing_school is not None:
		return render_template("add-school.html", boards=boards, error="There is already a school in that board with that name")
		
	school = School(school_name, board.id)
	db.session.add(school)
	db.session.commit()

	return redirect("/admin")

@manage.route("/admin/add-teacher", methods=["GET", "POST"])
@admin_required
def add_teacher():
	if request.method == "GET":
		return render_template("add-teacher.html")
	
	board_name = request.form["board"]
	school_name = request.form["school"]
	teacher_name = request.form["name"]
	username = request.form["username"]

	board = SchoolBoard.query.filter_by(name=board_name).first()

	if board is None:
		return render_template("add-teacher.html", error="Board name not found")
	
	school = School.query.filter_by(name=school_name, school_board=board).first()

	if school is None:
		return render_template("add-teacher.html", error="School name not found")
	
	if not teacher_name or not username:
		return render_template("add-teacher.html", error="Username and teacher name must be provided")
	
	existing_user = User.query.filter_by(username=username).first()

	if existing_user is not None:
		return render_template("add-teacher.html", error="Username already exists")
	
	random_password = generate_random_password()
	user = User(
		username=username,
		password=bcrypt.generate_password_hash(random_password),
		school_id=school.id,
		role_id=UserRole.query.filter_by(role="teacher").first().id
	)

	db.session.add(user)
	db.session.commit()

	return render_template("user-created.html", username=username, password=random_password, admin_created=True)

@manage.route("/admin/manage/<int:school_id>")
@admin_required
@check_object_exists(School, "/admin")
def manage_school(school):
	current_user.school = school
	db.session.commit()

	return redirect("/teacher")

@manage.route("/admin/delete-school/<int:school_id>", methods=["GET", "POST"])
@admin_required
@check_object_exists(School, "/admin")
def delete_school(school):
	if request.method == "GET":
		return render_template("confirm-delete.html", type="school", text=school.name, extra_text="This will also delete all teachers and students in this school.")
	
	users = User.query.filter_by(school=school).all()
	for user in users:
		if user.role.name == "teacher" or user.role.name == "student":
			db.session.delete(user)
	
	db.session.delete(school)
	db.session.commit()

	return redirect("/admin")

@manage.route("/admin/delete-board/<int:board_id>", methods=["GET", "POST"])
@admin_required
@check_object_exists(SchoolBoard, "/admin")
def delete_board(board):
	schools = School.query.filter_by(school_board=board).all()

	if len(schools) > 0:
		return redirect("/admin")
	
	if request.method == "GET":
		return render_template("confirm-delete.html", type="school board", text=board.name)
	
	db.session.delete(board)
	db.session.commit()

	return redirect("/admin")

@manage.route("/admin/delete-user/<string:username>", methods=["GET", "POST"])
@admin_required
def delete_user(username):
	user = User.query.filter_by(username=username).first()

	if user is None:
		return redirect("/admin")
	
	if request.method == "GET":
		return render_template("confirm-delete.html", type="user", text=user.username)
	
	db.session.delete(user)
	db.session.commit()

	return redirect("/admin")