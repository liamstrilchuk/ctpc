from flask import Blueprint, redirect, render_template, request

from models import AbstractTestCase, AbstractTestCaseGroup, Contest, ContestType, Problem, db
from util import admin_required, to_unix_timestamp, check_object_exists

contests = Blueprint("contests", __name__, template_folder="templates")

@contests.route("/admin/contests")
@admin_required
def contests_view():
	contests = Contest.query.all()

	return render_template("admin-contests.html", contests=contests)

@contests.route("/admin/add-contest", methods=["GET", "POST"])
@admin_required
def add_contest():
	contest_types = ContestType.query.all()

	if request.method == "GET":
		return render_template("add-contest.html", contest_types=contest_types)
	
	name = request.form["name"]
	contest_type = request.form["contest_type"]
	start_date = to_unix_timestamp(request.form["start"])
	end_date = to_unix_timestamp(request.form["end"])

	if not start_date or not end_date or start_date >= end_date:
		return render_template("add-contest.html", error="Invalid dates", contest_types=contest_types)
	
	ctype_obj = ContestType.query.filter_by(name=contest_type).first()
	if not ctype_obj:
		return render_template("add-contest.html", error="Invalid contest type", contest_types=contest_types)
	
	if not name:
		return render_template("add-contest.html", error="Invalid name", contest_types=contest_types)
	
	contest = Contest(
		name=name,
		contest_type_id=ctype_obj.id,
		start_date=start_date,
		end_date=end_date
	)
	db.session.add(contest)
	db.session.commit()

	return redirect("/admin/contests")

@contests.route("/admin/edit-contest/<int:contest_id>", methods=["GET", "POST"])
@admin_required
@check_object_exists(Contest, "/admin/contests")
def edit_contest(contest):
	contest_types = ContestType.query.all()

	if request.method == "GET":
		return render_template("add-contest.html", editing=True, name=contest.name, contest_types=contest_types, contest=contest)
	
	name = request.form["name"]
	contest_type = request.form["contest_type"]
	start_date = to_unix_timestamp(request.form["start"])
	end_date = to_unix_timestamp(request.form["end"])

	if not start_date or not end_date or start_date >= end_date:
		return render_template("add-contest.html", error="Invalid dates", contest_types=contest_types, contest=contest)
	
	ctype_obj = ContestType.query.filter_by(name=contest_type).first()
	if not ctype_obj:
		return render_template("add-contest.html", error="Invalid contest type", contest_types=contest_types, contest=contest)
	
	if not name:
		return render_template("add-contest.html", error="Invalid name", contest_types=contest_types, contest=contest)
	
	contest.name = name
	contest.contest_type_id = ctype_obj.id
	contest.start_date = start_date
	contest.end_date = end_date

	db.session.commit()
	return redirect("/admin/contests")

@contests.route("/admin/delete-contest/<int:contest_id>", methods=["GET", "POST"])
@admin_required
@check_object_exists(Contest, "/admin/contests")
def delete_contest(contest):
	if len(contest.problems) > 0:
		return redirect("/admin/contests")
	
	if request.method == "GET":
		return render_template("confirm-delete.html", type="contest", text=contest.name)
	
	db.session.delete(contest)
	db.session.commit()

	return redirect("/admin/contests")

@contests.route("/admin/edit-problems/<int:contest_id>")
@admin_required
@check_object_exists(Contest, "/admin/contests")
def edit_problems(contest):
	return render_template("admin-problems.html", contest=contest)

@contests.route("/admin/create-problem/<int:contest_id>", methods=["GET", "POST"])
@admin_required
@check_object_exists(Contest, "/admin/contests")
def create_problem(contest):
	if request.method == "GET":
		return render_template("create-problem.html", contest=contest)
	
	problem_name = request.form["name"]
	description = request.form["description"]

	if not problem_name:
		return render_template("create-problem.html", contest=contest, error="Invalid name")
	
	problem = Problem(name=problem_name, description=description, contest_id=contest.id)
	db.session.add(problem)
	db.session.commit()

	return redirect(f"/admin/edit-problems/{contest.id}")

@contests.route("/admin/edit-problem/<int:problem_id>", methods=["GET", "POST"])
@admin_required
@check_object_exists(Problem, "/admin/contests")
def edit_problem(problem):
	if request.method == "GET":
		return render_template("create-problem.html", contest=problem.contest, problem=problem)
	
	problem_name = request.form["name"]
	description = request.form["description"]

	if not problem_name:
		return render_template("create-problem.html", contest=problem.contest, problem=problem, error="Invalid name")

	problem.name = problem_name
	problem.description = description

	db.session.commit()

	return redirect(f"/admin/edit-problems/{problem.contest.id}")

@contests.route("/admin/delete-problem/<int:problem_id>", methods=["GET", "POST"])
@admin_required
@check_object_exists(Problem, "/admin/contests")
def delete_problem(problem):
	if request.method == "GET":
		return render_template("confirm-delete.html", type="problem", text=problem.name)

	contest_id = problem.contest.id
	
	for tc in problem.test_cases:
		db.session.delete(tc)
	
	db.session.delete(problem)
	db.session.commit()

	return redirect(f"/admin/edit-problems/{contest_id}")

@contests.route("/admin/problems/<int:problem_id>")
@admin_required
@check_object_exists(Problem, "/admin/contests")
def view_test_cases(problem):
	return render_template("test-cases.html", problem=problem)

@contests.route("/admin/add-test-case-group/<int:problem_id>", methods=["GET", "POST"])
@admin_required
@check_object_exists(Problem, "/admin/contests")
def add_test_case_group(problem):
	if request.method == "GET":
		return render_template("add-test-case-group.html", problem=problem)
	
	point_value = request.form.get("point_value")
	is_sample = request.form.get("is_sample") == "on"

	problem.point_value += int(point_value)
	
	group = AbstractTestCaseGroup(point_value=point_value, problem_id=problem.id, is_sample=is_sample)
	db.session.add(group)
	db.session.commit()

	return redirect(f"/admin/problems/{problem.id}")

@contests.route("/admin/edit-test-case-group/<int:group_id>", methods=["GET", "POST"])
@admin_required
@check_object_exists(AbstractTestCaseGroup, "/admin/contests")
def edit_test_case_group(group):
	if request.method == "GET":
		return render_template("add-test-case-group.html", problem=group.problem, group=group)
	
	point_value = request.form.get("point_value")
	is_sample = request.form.get("is_sample") == "on"

	group.problem.point_value -= group.point_value
	group.problem.point_value += int(point_value)

	group.point_value = point_value
	group.is_sample = is_sample

	db.session.commit()

	return redirect(f"/admin/problems/{group.problem.id}")

@contests.route("/admin/delete-test-case-group/<int:group_id>", methods=["GET", "POST"])
@admin_required
@check_object_exists(AbstractTestCaseGroup, "/admin/contests")
def delete_test_case_group(group):
	if request.method == "GET":
		return render_template("confirm-delete.html", type="test case group", text=group.id)
	
	problem_id = group.problem.id
	group.problem.point_value -= group.point_value

	for tc in group.test_cases:
		db.session.delete(tc)
	
	db.session.delete(group)
	db.session.commit()

	return redirect(f"/admin/problems/{problem_id}")

@contests.route("/admin/add-test-case/<int:group_id>", methods=["GET", "POST"])
@admin_required
@check_object_exists(AbstractTestCaseGroup, "/admin/contests")
def add_test_case(group):
	if request.method == "GET":
		return render_template("add-test-case.html", problem=group.problem)
	
	input_data = request.form.get("input")
	output_data = request.form.get("output")

	if not input_data or not output_data:
		return render_template("add-test-case.html", problem=group.problem, error="Invalid input or output")

	tc = AbstractTestCase(input=input_data, expected_output=output_data, group_id=group.id)
	db.session.add(tc)
	db.session.commit()

	return redirect(f"/admin/problems/{group.problem.id}")

@contests.route("/admin/edit-test-case/<int:test_case_id>", methods=["GET", "POST"])
@admin_required
@check_object_exists(AbstractTestCase, "/admin/contests")
def edit_test_case(test_case):
	if request.method == "GET":
		return render_template("add-test-case.html", problem=test_case.group.problem, test_case=test_case)
	
	input_data = request.form.get("input")
	output_data = request.form.get("output")

	if not input_data or not output_data:
		return render_template("add-test-case.html", problem=test_case.group.problem, test_case=test_case, error="Invalid input or output")

	test_case.input = input_data
	test_case.expected_output = output_data

	db.session.commit()

	return redirect(f"/admin/problems/{test_case.problem.id}")

@contests.route("/admin/delete-test-case/<int:test_case_id>", methods=["GET", "POST"])
@admin_required
@check_object_exists(AbstractTestCase, "/admin/contests")
def delete_test_case(test_case):
	if request.method == "GET":
		return render_template("confirm-delete.html", type="test case", text=test_case.id)
	
	problem_id = test_case.group.problem.id

	db.session.delete(test_case)
	db.session.commit()

	return redirect(f"/admin/problems/{problem_id}")