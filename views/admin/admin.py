from flask import Blueprint, redirect, render_template, request
from flask_login import current_user

from models import School, SchoolBoard, User, db
from setup import bcrypt
from util import generate_random_password

admin = Blueprint("admin", __name__, template_folder="templates")

def admin_required(func):
	def wrapper(*args, **kwargs):
		if not current_user.is_authenticated:
			return redirect("/")

		if not current_user.role == "admin":
			return redirect("/")

		return func(*args, **kwargs)
	
	wrapper.__name__ = func.__name__
	
	return wrapper

@admin.route("/admin")
@admin_required
def admin_view():
	return render_template("admin.html")

@admin.route("/admin/add-board", methods=["GET", "POST"])
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

@admin.route("/admin/add-school", methods=["GET", "POST"])
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

@admin.route("/admin/add-teacher", methods=["GET", "POST"])
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
		role="teacher"
	)

	db.session.add(user)
	db.session.commit()

	return render_template("user-created.html", username=username, password=random_password, admin_created=True)