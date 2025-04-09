from flask import Blueprint, render_template, redirect, request
from flask_login import current_user
from time import time

from models import AsyncStartTime, Contest, Team, User, UserRole, db
from setup import bcrypt
from util import check_object_exists, generate_random_password
import handle_objects

teacher = Blueprint("teacher", __name__, template_folder="templates")


def teacher_required(func):
	def wrapper(*args, **kwargs):
		if not current_user.is_authenticated:
			return redirect("/")

		if not current_user.role.name == "teacher" \
			and not current_user.role.name == "admin" or current_user.school is None:
			return redirect("/")

		return func(*args, **kwargs)
	
	wrapper.__name__ = func.__name__
	
	return wrapper


def can_modify(func):
	def wrapper(*args, **kwargs):
		if current_user.school and current_user.school.competition.registration_cutoff \
			and time() > current_user.school.competition.registration_cutoff \
			and not current_user.role.name == "admin":
			return redirect("/teacher")
		
		return func(*args, **kwargs)
	
	wrapper.__name__ = func.__name__

	return wrapper


def teacher_controls(teacher, student):
	if student is None or not student.school == teacher.school \
		or not student.role.name == "student" or not teacher.role.name in ("teacher", "admin"):
		return False

	return True


def get_active_async_time():
	async_contest_times = AsyncStartTime.query.filter_by(school_id=current_user.school.id).all()

	for act in async_contest_times:
		if time() > act.start_time and time() < act.end_time:
			return act

	return None


@teacher.route("/teacher")
@teacher_required
def teacher_view():
	if current_user.role.name == "teacher" and not current_user.completed_onboarding:
		return redirect("/teacher-onboarding")

	teams = Team.query.filter_by(school=current_user.school).all()
	unassigned = User.query \
		.filter_by(
			school=current_user.school,
			team_id=None,
			role=UserRole.query.filter_by(name="student").first()
		).all()
	
	remaining_in_person_spots = current_user.school.in_person_spots - \
		len(Team.query.filter_by(school=current_user.school, in_person=True).all())

	past_registration_cutoff = False

	if current_user.school and current_user.school.competition.registration_cutoff \
		and time() > current_user.school.competition.registration_cutoff \
		and not current_user.role.name == "admin":
		past_registration_cutoff = True

	async_state = "prior"
	as_start = current_user.school.competition.async_start if current_user.school else None
	as_end = current_user.school.competition.async_end if current_user.school else None

	if (as_start and time() > as_start) and (as_end is None or time() < as_end):
		async_state = "running"

	if as_end and time() > as_end:
		async_state = "complete"

	available_contests = []

	if async_state == "running":
		for contest in current_user.school.competition.contests:
			if not contest.point_multiplier == 0:
				available_contests.append({
					"contest": contest,
					"complete": AsyncStartTime.query \
						.filter_by(contest=contest, school=current_user.school).first() is not None
				})

	return render_template(
		"teacher.html",
		teams=teams,
		unassigned=unassigned,
		remaining_in_person_spots=remaining_in_person_spots,
		past_registration_cutoff=past_registration_cutoff,
		async_state=async_state,
		active_async_time=get_active_async_time(),
		available_contests=available_contests,
		current_time=time()
	)


@teacher.route("/teacher/start/<int:contest_id>", methods=["GET", "POST"])
@teacher_required
@check_object_exists(Contest, "/teacher")
def start_async_contest(contest):
	if current_user.school.synchronous:
		return redirect("/teacher")
	
	if time() < contest.competition.async_start or time() > contest.competition.asnyc_end:
		return redirect("/teacher")
	
	existing_act = AsyncStartTime.query.filter_by(
		school_id=current_user.school.id,
		contest_id=contest.id
	).first()

	if existing_act is not None:
		return redirect("/teacher")
	
	act = get_active_async_time()

	if act is not None:
		return redirect("/teacher")
	
	if request.method == "GET":
		return render_template("teacher-confirm-start.html", contest=contest)
	
	contest_length = contest.end_date - contest.start_date
	act = AsyncStartTime(
		school_id=current_user.school.id,
		contest_id=contest.id,
		start_time=int(time()),
		end_time=int(time() + contest_length)
	)
	db.session.add(act)
	db.session.commit()

	return redirect("/teacher")


@teacher.route("/teacher/end-early", methods=["GET", "POST"])
@teacher_required
def end_early():
	active_async_time = get_active_async_time()

	if active_async_time is None:
		return redirect("/teacher")
	
	if request.method == "GET":
		return render_template("teacher-end-early.html", act=active_async_time)
	
	active_async_time.end_time = int(time())
	db.session.commit()
	return redirect("/teacher")


@teacher.route("/teacher/assign-in-person/<int:team_id>")
@teacher_required
@check_object_exists(Team, "/teacher")
def assign_in_person(team):
	if not team.school == current_user.school:
		return redirect("/teacher")

	remaining_in_person_spots = current_user.school.in_person_spots \
		- len(Team.query.filter_by(school=current_user.school, in_person=True).all())

	if not team.in_person and remaining_in_person_spots == 0:
		return redirect("/teacher")
	
	team.in_person = not team.in_person
	db.session.commit()

	return redirect("/teacher")


@teacher.route("/teacher-onboarding", methods=["GET", "POST"])
@teacher_required
def teacher_onboarding():
	if not current_user.role.name == "teacher":
		return redirect("/teacher")
	
	if current_user.school is None:
		return redirect("/")
	
	if time() > current_user.school.competition.async_start:
		return redirect("/teacher")
	
	if request.method == "GET":
		return render_template("teacher-onboard.html")
	
	in_person = request.form.get("in-person") == "on"
	sync = request.form.get("sync") == "yes"

	current_user.school.consider_in_person = in_person
	current_user.school.synchronous = sync
	current_user.completed_onboarding = True
	db.session.commit()

	return render_template("teacher-postregister.html", in_person=in_person, sync=sync)


@teacher.route("/teacher/create-team", methods=["GET", "POST"])
@teacher_required
@can_modify
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
@can_modify
def register_student():
	if request.method == "GET":
		return render_template("register-student.html")
	
	first = request.form["name"]
	last = request.form["surname"]

	if not first or not last:
		return render_template("register-student.html", error="Please fill out all fields")

	first_clean, last_clean = "", ""
	for c in first.lower():
		if c in "abcdefghijklmnopqrstuvwxyz":
			first_clean += c

	for c in last.lower():
		if c in "abcdefghijklmnopqrstuvwxyz":
			last_clean += c

	if not first_clean and not last_clean:
		last_clean = "user"

	username_start = first_clean[:3] + last_clean[:5]
	try:
		user, password = handle_objects.add_student(
			username_start,
			school_id=current_user.school_id
		)
	except:
		return render_template(
			"register-student.html",
			error="An error occurred when registering user"
		)

	return render_template("user-created.html", username=user.username, password=password)


@teacher.route("/teacher/assign/<string:username>", methods=["GET", "POST"])
@teacher_required
@can_modify
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
	
	if len(team.members) >= 4:
		return render_template(
			"assign-student.html",
			user=user,
			teams=teams,
			error="That team is already full."
		)

	user.team_id = team_id
	db.session.commit()

	return redirect("/teacher")


@teacher.route("/teacher/unassign/<string:username>")
@teacher_required
@can_modify
def unassign_student(username):
	user = User.query.filter_by(username=username).first()
	if not teacher_controls(current_user, user):
		return redirect("/teacher")

	user.team_id = None
	db.session.commit()

	return redirect("/teacher")


@teacher.route("/teacher/delete/<string:username>", methods=["GET", "POST"])
@teacher_required
@can_modify
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

	return render_template(
		"user-created.html",
		username=username,
		password=random_password,
		text="Password reset successfully"
	)


@teacher.route("/teacher/delete-team/<int:team_id>", methods=["GET", "POST"])
@teacher_required
@can_modify
def delete_team(team_id):
	team = Team.query.filter_by(id=team_id).first()
	if team is None or not team.school == current_user.school:
		return redirect("/teacher")

	if request.method == "GET":
		return render_template("confirm-delete.html", text=team.name, type="team")

	handle_objects.delete_team(team)

	return redirect("/teacher")