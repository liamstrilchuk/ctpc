from flask import Blueprint, render_template, redirect, request
from flask_login import login_required, current_user
from time import time
import requests, markdown

from models import AbstractTestCaseGroup, Contest, ContestType, LanguageType, Problem, Submission, SubmissionStatus, Team, TestCase, TestCaseGroup, TestCaseStatus, User, db
from util import check_object_exists

main = Blueprint("main", __name__, template_folder="templates")

@main.route("/team")
@login_required
def team_view():
	if not current_user.role.name == "student":
		return redirect("/")
	
	return render_template("team.html", team=current_user.team)

@main.route("/contests")
@login_required
def contests_view():
	contests = Contest.query.all()
	return render_template("contests.html", contests=contests, current_time=time())

@main.route("/contest/<int:contest_id>")
@login_required
@check_object_exists(Contest, "/contests")
def contest_view(contest):
	if time() < contest.start_date:
		return redirect("/contests")

	if contest.contest_type_id == ContestType.query.filter_by(name="individual").first().id or not current_user.team:
		user_submissions = Submission.query \
			.join(Problem, Submission.problem_id == Problem.id) \
			.filter(Problem.contest_id == contest.id) \
			.filter(Submission.user_id == current_user.id)
	else:
		user_submissions = Submission.query \
			.join(Problem, Submission.problem_id == Problem.id) \
			.filter(Problem.contest_id == contest.id) \
			.join(User, Submission.user_id == User.id) \
			.join(Team, User.team_id == Team.id) \
			.filter(Team.id == current_user.team_id)
	
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
		"contest.html",
		contest=contest,
		current_time=time(),
		user_submissions=user_submissions.order_by(Submission.timestamp.desc()).all(),
		problem_dict=problem_dict
	)

@main.route("/problem/<int:problem_id>")
@login_required
@check_object_exists(Problem, "/contests")
def problem_view(problem):
	if time() < problem.contest.start_date:
		return redirect("/contests")
	
	sample_groups = AbstractTestCaseGroup.query.filter_by(problem_id=problem.id, is_sample=True).all()
	languages = LanguageType.query.all()

	html_content = markdown.markdown(problem.description)

	return render_template("problem.html", problem=problem, problem_html=html_content, sample_groups=sample_groups, languages=languages)

@main.route("/submit/<int:problem_id>", methods=["POST"])
@login_required
@check_object_exists(Problem, "/contests")
def submit(problem):
	if time() < problem.contest.start_date:
		return redirect("/contests")
	
	language_id = request.form["language"]
	code = request.form["code"]

	language = LanguageType.query.filter_by(short_name=language_id).first()

	if not language:
		return redirect(f"/problem/{problem.id}")

	submission = Submission(
		user_id=current_user.id,
		problem_id=problem.id,
		language_id=language.id,
		code=code,
		timestamp=int(time()),
		status_id=SubmissionStatus.query.filter_by(name="Pending").first().id
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

	response = requests.post("http://127.0.0.1:8000/create-submission", json=json_to_grader)

	return redirect(f"/submission/{submission.id}")

@main.route("/submission/<int:submission_id>")
@login_required
@check_object_exists(Submission, "/contests")
def submission_view(submission):
	if not submission.user == current_user and not current_user.role.name == "admin" and not (submission.problem.contest.contest_type.name == "team" and current_user.team and submission.user.team_id == current_user.team.id):
		return redirect("/")

	return render_template("submission.html", submission=submission, current_time=time())