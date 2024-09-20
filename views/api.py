from flask import Blueprint
from flask_login import login_required
import time

from models import Problem
from util import check_object_exists

api = Blueprint("api", __name__)

def error(message):
	return { "error": message }

@api.route("/api/test_cases/<int:problem_id>")
@login_required
@check_object_exists(Problem, "/")
def get_test_cases(problem):
	if problem.contest.start_date > time.time():
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