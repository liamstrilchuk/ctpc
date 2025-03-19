from flask import Blueprint, render_template, request, redirect
from flask_login import current_user
import time, json, requests

from models import SubmissionStatus, User, School, SchoolBoard, UserRole, Submission, db
from util import admin_required, generate_random_password, check_object_exists
from setup import bcrypt
import handle_objects

manage = Blueprint("manage", __name__, template_folder="templates")


@manage.route("/admin/add-board", methods=["GET", "POST"])
@admin_required
def add_board():
	if request.method == "GET":
		return render_template("admin/add-board.html")
	
	board_name = request.form["name"]

	if SchoolBoard.query.filter_by(name=board_name).first() is not None:
		return render_template("admin/add-board.html", error="Board with that name already exists")
	
	board = SchoolBoard(board_name)
	db.session.add(board)
	db.session.commit()
	
	return redirect("/admin")


@manage.route("/admin/add-teacher/<school_id>", methods=["GET", "POST"])
@admin_required
@check_object_exists(School, "/admin")
def add_teacher(school):
	if request.method == "GET":
		return render_template("admin/add-teacher.html")
	
	teacher_name = request.form["name"]
	username = request.form["username"]

	if not teacher_name or not username:
		return render_template("admin/add-teacher.html", error="Username and teacher name must be provided")
	
	existing_user = User.query.filter_by(username=username).first()

	if existing_user is not None:
		return render_template("admin/add-teacher.html", error="Username already exists")
	
	random_password = generate_random_password()
	user = User(
		username=username,
		password=bcrypt.generate_password_hash(random_password),
		school_id=school.id,
		role_id=UserRole.query.filter_by(name="teacher").first().id
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
	
	for team in school.teams:
		db.session.delete(team)

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
@check_object_exists(User, "/admin", key_name="username")
def delete_user(user):
	if request.method == "GET":
		return render_template("confirm-delete.html", type="user", text=user.username)
	
	if user.username == "admin":
		return redirect("/admin")
	
	handle_objects.delete_user(user)

	return redirect("/admin")


@manage.route("/admin/add-user", methods=["GET", "POST"])
@admin_required
def add_user():
	if request.method == "GET":
		return render_template("admin/add-user.html")
	
	username = request.form.get("username")
	role = request.form.get("role")

	if not username or not role in ["admin", "tester"]:
		return render_template("admin/add-user.html", error="Invalid username or role")
	
	if User.query.filter_by(username=username).first() is not None:
		return render_template("admin/add-user.html", error="Username already exists")
	
	try:
		user, password = handle_objects.add_student(username, role=role)
	except:
		return render_template("admin/add-user.html", error="An error occurred when creating user")
	
	return render_template("user-created.html", username=user.username, password=password, admin_created=True)


@manage.route("/admin/user-management")
@admin_required
def user_management():
	return render_template("admin/user-management.html", users=User.query.all())


@manage.route("/admin/assign-school/<username>", methods=["GET", "POST"])
@admin_required
@check_object_exists(User, "/admin", key_name="username")
def assign_school(user):
	if not user.role.name == "teacher":
		return redirect("/admin")
	
	if request.method == "GET":
		return render_template("admin/assign-school.html", username=user.username, schools=School.query.all())
	
	school = request.form.get("school")
	obj = School.query.filter_by(id=school).first()

	if not school == "unassign" and obj is None:
		return render_template(
			"admin/assign-school.html",
			username=user.username,
			schools=School.query.all(),
			error="Could not find school"
		)
	
	user.school_id = None if school == "unassign" else obj.id
	db.session.commit()

	return redirect("/admin/user-management")


@manage.route("/admin/view-submissions/<username>")
@admin_required
@check_object_exists(User, "/admin", key_name="username")
def view_submissions(user):
	return render_template("admin/view-submissions.html", user=user)


@manage.route("/admin/view-recent-submissions/<int:timeframe>")
@admin_required
def view_recent_submissions(timeframe):
	recent = Submission.query \
		.join(SubmissionStatus) \
		.filter((Submission.timestamp >= time.time() - timeframe) | (SubmissionStatus.name == "Pending")) \
		.order_by(Submission.timestamp.desc()) \
		.all()

	try:
		grader_response = json.loads(requests.get("http://127.0.0.1:8000/status").content)
	except Exception as e:
		print(e)
		grader_response = None

	return render_template(
		"admin/view-recent-submissions.html",
		submissions=recent,
		timeframe=timeframe,
		grader_response=grader_response
	)


@manage.route("/admin/resubmit-pending-submissions")
@admin_required
def resubmit_pending_submissions():
	requests.post("http://127.0.0.1:8000/cancel-all")

	pending_submissions = Submission.query \
		.join(SubmissionStatus) \
		.filter(SubmissionStatus.name == "Pending") \
		.all()
	
	for sub in pending_submissions:
		if sub.is_practice:
			continue

		all_groups = []
		for tcg in sub.test_case_groups:
			all_groups.append([])
			for tc in tcg.test_cases:
				all_groups[-1].append({
					"input": tc.abstract_test_case.input,
					"expected_output": tc.abstract_test_case.expected_output,
					"id": tc.id
				})
			
		json_to_grader = {
			"code": sub.code,
			"testcases": all_groups,
			"language": sub.language.grader_id,
			"submission_id": sub.id,
			"run_all": True
		}

		requests.post("http://127.0.0.1:8000/create-submission", json=json_to_grader)

	return redirect("/admin/view-recent-submissions/900")


@manage.route("/admin/delete-submission/<int:submission_id>", methods=["GET", "POST"])
@admin_required
@check_object_exists(Submission, "/admin/view-recent-submissions/900")
def delete_submission(submission):
	if request.method == "GET":
		return render_template("confirm-delete.html", type="submission", text=f"id={submission.id} by {submission.user.username}")
	
	handle_objects.delete_submission(submission)
	return redirect("/admin/view-recent-submissions/900")