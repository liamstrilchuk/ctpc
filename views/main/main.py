from flask import Blueprint, render_template, redirect, request
from flask_login import login_required, current_user, login_user
from time import time
import requests, markdown, re

from models import AbstractTestCaseGroup, Competition, Contest, ContestType, LanguageType, Problem, Submission, SubmissionStatus, Team, TestCase, TestCaseGroup, TestCaseStatus, User, db
from util import check_object_exists, logout_required
import handle_objects

main = Blueprint("main", __name__, template_folder="templates")

@main.route("/team")
@login_required
def team_view():
	if not current_user.role.name == "student":
		return redirect("/")
	
	return render_template("contest/team.html", team=current_user.team)

@main.route("/competitions")
@login_required
def competitions_view():
	competitions = Competition.query.all()
	return render_template("contest/competitions.html", competitions=competitions, current_time=time())

@main.route("/competitions/<competition_id>")
@login_required
@check_object_exists(Competition, "/competitions", key_name="short_name")
def contests_view(competition):
	return render_template("contest/contests.html", contests=competition.contests, current_time=time(), competition=competition)

@main.route("/contest/<int:contest_id>")
@login_required
@check_object_exists(Contest, "/competitions")
def contest_view(contest):
	if time() < contest.start_date and not current_user.role.name in ["admin", "tester"]:
		return redirect("/competitions")

	if contest.contest_type_id == ContestType.query.filter_by(name="individual").first().id or not current_user.team:
		user_submissions = Submission.query \
			.join(Problem, Submission.problem_id == Problem.id) \
			.filter(Problem.contest_id == contest.id) \
			.filter(Submission.user_id == current_user.id) \
			.filter(Submission.is_practice == False)
	else:
		user_submissions = Submission.query \
			.join(Problem, Submission.problem_id == Problem.id) \
			.filter(Problem.contest_id == contest.id) \
			.join(User, Submission.user_id == User.id) \
			.join(Team, User.team_id == Team.id) \
			.filter(Team.id == current_user.team_id) \
			.filter(Submission.is_practice == False)
	
	ordered_submissions = user_submissions.order_by(Submission.points_earned.desc()).all()
	problem_dict = { problem.id: { "points_earned": 0, "has_submission": False } for problem in contest.problems }

	for sub in ordered_submissions:
		if not sub.problem.contest == contest:
			continue

		if problem_dict[sub.problem.id]["has_submission"]:
			continue

		problem_dict[sub.problem.id]["has_submission"] = True
		problem_dict[sub.problem.id]["points_earned"] = sub.points_earned

	return render_template(
		"contest/contest.html",
		contest=contest,
		current_time=time(),
		user_submissions=user_submissions.order_by(Submission.timestamp.desc()).all(),
		problem_dict=problem_dict
	)

@main.route("/problem/<int:problem_id>")
@login_required
@check_object_exists(Problem, "/competitions")
def problem_view(problem):
	if time() < problem.contest.start_date and not current_user.role.name in ["admin", "tester"]:
		return redirect("/competitions")
	
	sample_groups = AbstractTestCaseGroup.query.filter_by(problem_id=problem.id, is_sample=True).all()
	languages = LanguageType.query.all()

	html_content = markdown.markdown(problem.description)

	return render_template("contest/problem.html", problem=problem, problem_html=html_content, sample_groups=sample_groups, languages=languages)

@main.route("/submit/<int:problem_id>", methods=["POST"])
@login_required
@check_object_exists(Problem, "/competitions")
def submit(problem):
	if time() < problem.contest.start_date and not current_user.role.name in ["admin", "tester"]:
		return redirect("/competitions")
	
	last_user_submission = Submission.query \
		.filter_by(user_id=current_user.id) \
		.filter_by(is_practice=False) \
		.order_by(Submission.timestamp.desc()) \
		.first()
	
	if last_user_submission and time() - last_user_submission.timestamp < 60:
		return redirect(f"/problem/{problem.id}")
	
	language_id = request.form["language"]
	code = request.form["code"]
	return_id = "return_id" in request.form

	language = LanguageType.query.filter_by(short_name=language_id).first()

	if not language:
		return redirect(f"/problem/{problem.id}")

	submission = Submission(
		user_id=current_user.id,
		problem_id=problem.id,
		language_id=language.id,
		code=code,
		timestamp=int(time()),
		status_id=SubmissionStatus.query.filter_by(name="Pending").first().id,
		is_practice=False
	)
	
	db.session.add(submission)
	db.session.commit()

	all_testcases = []

	for tcg in problem.test_case_groups:
		test_case_group = TestCaseGroup(
			abstract_group_id=tcg.id,
			submission_id=submission.id
		)

		db.session.add(test_case_group)
		db.session.commit()

		for tc in tcg.test_cases:
			test_case = TestCase(
				abstract_test_case_id=tc.id,
				group_id=test_case_group.id,
				status_id=TestCaseStatus.query.filter_by(name="Pending").first().id
			)

			db.session.add(test_case)
			all_testcases.append(test_case)

		db.session.commit()

	all_testcases = [
		{
			"input": tc.abstract_test_case.input,
			"expected_output": tc.abstract_test_case.expected_output,
			"id": tc.id
		} for tc in all_testcases
	]

	json_to_grader = {
		"code": submission.code,
		"testcases": all_testcases,
		"language": language.grader_id,
		"submission_id": submission.id
	}

	requests.post("http://127.0.0.1:8000/create-submission", json=json_to_grader)

	return redirect(f"/submission/{submission.id}") if not return_id else { "id": submission.id }

@main.route("/submit-practice/<int:problem_id>", methods=["POST"])
@login_required
@check_object_exists(Problem, "/competitions")
def submit_practice(problem):
	if time() < problem.contest.start_date and not current_user.role.name in ["admin", "tester"]:
		return redirect("/competitions")
	
	data = request.get_json()
	try:
		language = LanguageType.query.filter_by(short_name=data["language"]).first()
		code = data["code"]
		test_cases = data["test_cases"]
		if not type(test_cases) == list or len(test_cases) > 10:
			raise Exception()
		send_to_grader = []

		for tc in test_cases:
			if not "expected_output" in tc or not "input" in tc or len(tc["expected_output"]) > 2000 or len(tc["input"]) > 2000:
				raise Exception()
			
			send_to_grader.append({ "input": tc["input"], "expected_output": tc["expected_output"] })

		submission = Submission(
			user_id=current_user.id,
			problem_id=problem.id,
			language_id=language.id,
			code=code,
			timestamp=int(time()),
			status_id=SubmissionStatus.query.filter_by(name="Pending").first().id,
			is_practice=True
		)

		db.session.add(submission)
		db.session.commit()

		test_case_group = TestCaseGroup(
			submission_id=submission.id,
			abstract_group_id=None
		)

		db.session.add(test_case_group)
		db.session.commit()

		for tc in send_to_grader:
			tc_obj = TestCase(
				abstract_test_case_id=None,
				group_id=test_case_group.id,
				status_id=TestCaseStatus.query.filter_by(name="Pending").first().id
			)
			db.session.add(tc_obj)
			db.session.commit()
			tc["id"] = tc_obj.id

		json_to_grader = {
			"code": code,
			"testcases": send_to_grader,
			"language": language.grader_id,
			"submission_id": submission.id
		}

		response = requests.post("http://127.0.0.1:8000/create-submission", json=json_to_grader)
	except Exception as e:
		print(e)
		return { "id": None }

	return { "id": submission.id }

@main.route("/practice-submission-status/<int:submission_id>")
@login_required
@check_object_exists(Submission, "/")
def practice_submission_status(submission):
	if not submission.user == current_user:
		return redirect("/")
	
	test_case_data = []

	for tcg in submission.test_case_groups:
		for tc in tcg.test_cases:
			test_case_data.append({
				"output": tc.output,
				"status": tc.status.name,
				"time": submission.timestamp
			})

	return test_case_data

@main.route("/last-practice-submission/<int:problem_id>")
@login_required
@check_object_exists(Problem, "/competitions")
def last_practice_submission(problem):
	if time() < problem.contest.start_date and not current_user.role.name in ["tester", "admin"]:
		return []
	
	all_submissions = Submission.query \
		.filter(Submission.user_id == current_user.id) \
		.filter(Submission.problem_id == problem.id) \

	last_practice_submission = all_submissions \
		.filter(Submission.is_practice == True) \
		.order_by(Submission.timestamp.desc()) \
		.first()
	
	last_submission = all_submissions \
		.order_by(Submission.timestamp.desc()) \
		.first()
	
	test_case_data = []
	
	if last_practice_submission:
		for tcg in last_practice_submission.test_case_groups:
			for tc in tcg.test_cases:
				test_case_data.append({
					"output": tc.output,
					"status": tc.status.name,
					"time": last_practice_submission.timestamp
				})

	if last_submission:
		return {
			"test_cases": test_case_data,
			"code": last_submission.code,
			"language": last_submission.language.short_name
		}
	else:
		return {
			"test_cases": [],
			"code": "",
			"language": ""
		}

@main.route("/submission/<int:submission_id>")
@login_required
@check_object_exists(Submission, "/competitions")
def submission_view(submission):
	if not submission.user == current_user and not current_user.role.name == "admin" and not (submission.problem.contest.contest_type.name == "team" and current_user.team and submission.user.team_id == current_user.team.id):
		return redirect("/")

	return render_template("contest/submission.html", submission=submission, current_time=time())

@main.route("/competitions/<competition_id>/register")
@check_object_exists(Competition, "/competitions", key_name="short_name")
def register(competition):
	return render_template("register.html", competition=competition)

@main.route("/competitions/<competition_id>/register/student", methods=["GET", "POST"])
@check_object_exists(Competition, "/competitions", key_name="short_name")
@logout_required
def register_as_student(competition):
	if request.method == "GET":
		return render_template("register-as-student.html", competition=competition)
	
	first = request.form.get("first")
	last = request.form.get("last")
	password = request.form.get("password")
	email = request.form.get("email")

	return register_teacher_or_student(first, last, password, email, competition, "individual-student", "register-as-student.html")

@main.route("/competitions/<competition_id>/register/teacher", methods=["GET", "POST"])
@check_object_exists(Competition, "/competitions", key_name="short_name")
@logout_required
def register_as_teacher(competition):
	if request.method == "GET":
		return render_template("register-as-teacher.html", competition=competition)

	first = request.form.get("first")
	last = request.form.get("last")
	password = request.form.get("password")
	email = request.form.get("email")

	return register_teacher_or_student(first, last, password, email, competition, "teacher", "register-as-teacher.html")

def register_teacher_or_student(first, last, password, email, competition, role, template):
	if not first or not last:
		return render_template(template, competition=competition, error="Invalid name")

	if not email or not re.fullmatch(r"[^@]+@[^@]+\.[^@]+", email):
		return render_template(template, competition=competition, error="Invalid email")
	
	if not password or not len(password) >= 8:
		return render_template(template, competition=competition, error="Password must be at least 8 characters")
	
	username_start = f"{first[:3]}{last[:5]}".lower()
	try:
		user, _ = handle_objects.add_student(username_start, role=role)
	except Exception:
		return render_template(template, competition=competition, error="An error occurred when registering")
	
	login_user(user)
	return redirect(f"/competitions/{competition.name}")

@main.route("/editor/<int:problem_id>")
@login_required
@check_object_exists(Problem, "/competitions")
def editor(problem):
	if time() < problem.contest.start_date and not current_user.role.name in ["tester", "admin"]:
		return redirect("/competitions")

	return render_template("editor.html", problem=problem, languages=LanguageType.query.all())