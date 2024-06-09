from flask import Blueprint, render_template, redirect, request
from flask_login import login_required, current_user
from time import time

from models import AbstractTestCase, AbstractTestCaseGroup, Contest, LanguageType, Problem, Submission, SubmissionStatus, TestCase, TestCaseGroup, TestCaseStatus, db
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
	
	ordered_submissions = Submission.query.filter_by(user_id=current_user.id).order_by(Submission.points_earned.desc()).all()
	problem_dict = { problem.id: { "points_earned": 0, "has_submission": False } for problem in contest.problems }

	for sub in ordered_submissions:
		if not sub.problem.contest == contest:
			continue

		if problem_dict[sub.problem.id]["has_submission"]:
			continue

		problem_dict[sub.problem.id]["has_submission"] = True
		problem_dict[sub.problem.id]["points_earned"] = sub.points_earned

	user_submissions = Submission.query.filter_by(user_id=current_user.id).all()
	return render_template("contest.html", contest=contest, current_time=time(), user_submissions=user_submissions, problem_dict=problem_dict)

@main.route("/problem/<int:problem_id>")
@login_required
@check_object_exists(Problem, "/contests")
def problem_view(problem):
	if time() < problem.contest.start_date:
		return redirect("/contests")
	
	sample_groups = AbstractTestCaseGroup.query.filter_by(problem_id=problem.id, is_sample=True).all()
	languages = LanguageType.query.all()

	return render_template("problem.html", problem=problem, sample_groups=sample_groups, languages=languages)

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

		db.session.commit()

	return redirect(f"/contest/{problem.contest.id}")

@main.route("/submission/<int:submission_id>")
@login_required
@check_object_exists(Submission, "/contests")
def submission_view(submission):
	if not submission.user == current_user and not current_user.role.name == "admin":
		return redirect("/")

	return render_template("submission.html", submission=submission, current_time=time())