from flask import Blueprint
from flask_login import login_required, current_user
import time, markdown

from models import Problem, Submission
from util import check_object_exists

api = Blueprint("api", __name__)

def error(message):
	return { "error": message }

@api.route("/api/test-cases/<int:problem_id>")
@login_required
@check_object_exists(Problem, "/")
def get_test_cases(problem):
	if problem.contest.start_date > time.time() and not current_user.role.name in ["admin", "tester"]:
		return error("Problem is not available")

	groups = problem.test_case_groups
	all_test_cases = []

	for group in groups:
		if not group.is_sample:
			continue

		test_cases = group.test_cases
		
		for test_case in test_cases:
			all_test_cases.append({
				"input": test_case.input,
				"expected_output": test_case.expected_output
			})

	return { "test_cases": all_test_cases }

@api.route("/api/problem/<int:problem_id>")
@login_required
@check_object_exists(Problem, "/")
def get_problem(problem):
	if problem.contest.start_date > time.time() and not current_user.role.name in ["admin", "tester"]:
		return error("Problem is not available")
	
	raw_content = problem.description
	return { "content": markdown.markdown(raw_content), "title": problem.name }

@api.route("/api/submissions/<int:problem_id>")
@login_required
@check_object_exists(Problem, "/")
def get_submissions(problem):
	submissions = Submission.query \
		.filter_by(user_id=current_user.id) \
		.filter_by(problem_id=problem.id) \
		.filter_by(is_practice=False) \
		.order_by(Submission.timestamp.desc()) \
		.all()
	
	cleaned_submissions = []

	for sub in submissions:
		groups = []
		for tcg in sub.test_case_groups:
			groups.append({
				"test_cases": [],
				"points_earned": tcg.points_earned,
				"point_value": tcg.abstract_group.point_value,
				"is_sample": tcg.abstract_group.is_sample
			})

			for tc in tcg.test_cases:
				groups[-1]["test_cases"].append({
					"status": tc.status.name
				})

		cleaned_submissions.append({
			"status": sub.status.name,
			"test_case_groups": groups,
			"time": sub.timestamp,
			"points_earned": sub.points_earned,
			"point_value": sub.problem.point_value,
			"language": sub.language.name,
			"id": sub.id
		})

	return cleaned_submissions