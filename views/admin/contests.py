from flask import Blueprint, redirect, render_template, request

from models import AbstractTestCase, AbstractTestCaseGroup, Competition, Contest, ContestType, Problem, School, SchoolBoard, SchoolCode, Submission, db
from util import admin_required, to_unix_timestamp, check_object_exists
import handle_objects

contests = Blueprint("contests", __name__, template_folder="templates")

@contests.route("/admin/contests/<short_name>")
@admin_required
@check_object_exists(Competition, "/admin/competitions", key_name="short_name")
def contests_view(competition):
	total_points = 0
	for contest in competition.contests:
		for problem in contest.problems:
			total_points += problem.point_value * contest.point_multiplier

	return render_template("admin/admin-contests.html", competition=competition, total_points=total_points)

@contests.route("/admin/competitions")
@admin_required
def competitions_view():
	competitions = Competition.query.all()

	return render_template("admin/admin-competitions.html", competitions=competitions)

@contests.route("/admin/schools/<short_name>")
@admin_required
@check_object_exists(Competition, "/admin/competitions", key_name="short_name")
def schools_view(competition):
	return render_template("admin/admin-schools.html", competition=competition)

@contests.route("/admin/school-codes/<short_name>")
@admin_required
@check_object_exists(Competition, "/admin/competitions", key_name="short_name")
def school_codes(competition):
	return render_template(
		"admin/school-codes.html",
		competition=competition,
		codes=SchoolCode.query.filter_by(competition_id=competition.id)
	)

@contests.route("/admin/add-school-code/<short_name>", methods=["GET", "POST"])
@admin_required
@check_object_exists(Competition, "/admin/competitions", key_name="short_name")
def add_school_code(competition):
	if request.method == "GET":
		return render_template(
			"admin/add-school-code.html",
			competition=competition,
			boards=SchoolBoard.query.all()
		)
	
	board_name = request.form["board"]
	school_name = request.form["school"]

	board = SchoolBoard.query.filter_by(name=board_name).first()

	if board is None:
		return render_template(
			"admin/add-school-code.html",
			competition=competition,
			boards=SchoolBoard.query.all(),
			error="There is no board with that name"
		)
	
	existing_code = SchoolCode.query.filter_by(
		competition_id=competition.id,
		school_name=school_name,
		school_board_id=board.id
	).first()

	if existing_code is not None:
		return render_template(
			"admin/add-school.html",
			competition=competition,
			boards=SchoolBoard.query.all(),
			error="There is already a school code with that school name"
		)
	
	handle_objects.add_school_code(board.id, competition.id, school_name)

	return redirect(f"/admin/school-codes/{competition.short_name}")

@contests.route("/admin/delete-school-code/<int:code_id>", methods=["GET", "POST"])
@admin_required
@check_object_exists(SchoolCode, "/admin/competitions")
def delete_school_code(code):
	if request.method == "GET":
		return render_template("confirm-delete.html", type="school code", text=f"for {code.school_name}")
	
	competition_name = code.competition.short_name
	handle_objects.delete_school_code(code)
	return redirect(f"/admin/school-codes/{competition_name}")

@contests.route("/admin/add-school/<competition_short_name>", methods=["GET", "POST"])
@admin_required
@check_object_exists(Competition, "/admin/competitions", key_name="short_name")
def add_school(competition):
	boards = SchoolBoard.query.all()

	if request.method == "GET":
		return render_template("admin/add-school.html", boards=boards)
	
	board_name = request.form["board"]
	school_name = request.form["name"]

	board = SchoolBoard.query.filter_by(name=board_name).first()

	if board is None:
		return render_template("admin/add-school.html", boards=boards, error="There is no board with that name")
	
	existing_school = School.query.filter_by(name=school_name, school_board=board, competition_id=competition.id).first()

	if existing_school is not None:
		return render_template("admin/add-school.html", boards=boards, error="There is already a school in that board with that name")
		
	handle_objects.add_school(school_name, board.id, competition.id)

	return redirect("/admin")

@contests.route("/admin/add-competition", methods=["GET", "POST"])
@admin_required
def add_competition():
	if request.method == "GET":
		return render_template("admin/add-competition.html")
	
	name = request.form["name"]
	short_name = request.form["short_name"]

	if not name or not short_name:
		return render_template("admin/add-competition.html", error="Invalid name")
	
	existing_competition = Competition.query.filter_by(short_name=short_name).first()
	if existing_competition:
		return render_template("admin/add-competition.html", error="Competition already exists")

	handle_objects.add_competition(name, short_name)

	return redirect("/admin/competitions")

@contests.route("/admin/edit-competition/<int:competition_id>", methods=["GET", "POST"])
@admin_required
@check_object_exists(Competition, "/admin/contests")
def edit_competition(competition):
	if request.method == "GET":
		return render_template("admin/add-competition.html", editing=True, name=competition.name, short_name=competition.short_name, competition=competition)
	
	name = request.form["name"]
	short_name = request.form["short_name"]

	if not name or not short_name:
		return render_template("admin/add-competition.html", error="Invalid name", competition=competition)
	
	existing_competition = Competition.query.filter_by(short_name=short_name).first()
	if existing_competition:
		return render_template("admin/add-competition.html", error="Competition already exists", competition=competition)

	handle_objects.edit_competition(competition, name, short_name)

	return redirect("/admin/competitions")

@contests.route("/admin/add-contest/<competition_short_name>", methods=["GET", "POST"])
@admin_required
@check_object_exists(Competition, "/admin/competitions", key_name="short_name")
def add_contest(competition):
	contest_types = ContestType.query.all()

	if request.method == "GET":
		return render_template("admin/add-contest.html", contest_types=contest_types)
	
	name = request.form["name"]
	contest_type = request.form["contest_type"]
	start_date = to_unix_timestamp(request.form["start"])
	end_date = to_unix_timestamp(request.form["end"])
	point_multiplier = request.form["point_multiplier"]

	if not start_date or not end_date or start_date >= end_date:
		return render_template("admin/add-contest.html", error="Invalid dates", contest_types=contest_types)
	
	ctype_obj = ContestType.query.filter_by(name=contest_type).first()
	if not ctype_obj:
		return render_template("admin/add-contest.html", error="Invalid contest type", contest_types=contest_types)
	
	if not name:
		return render_template("admin/add-contest.html", error="Invalid name", contest_types=contest_types)
	
	try:
		float(point_multiplier)
	except:
		return render_template("admin/add-contest.html", error="Invalid point multiplier", contest_types=contest_types)
	
	handle_objects.add_contest(
		name=name,
		contest_type_id=ctype_obj.id,
		start_date=start_date,
		end_date=end_date,
		competition_id=competition.id,
		point_multiplier=point_multiplier
	)

	return redirect("/admin/competitions")

@contests.route("/admin/edit-contest/<int:contest_id>", methods=["GET", "POST"])
@admin_required
@check_object_exists(Contest, "/admin/contests")
def edit_contest(contest):
	contest_types = ContestType.query.all()

	if request.method == "GET":
		return render_template("admin/add-contest.html", editing=True, name=contest.name, contest_types=contest_types, contest=contest, point_multiplier=contest.point_multiplier)
	
	name = request.form["name"]
	contest_type = request.form["contest_type"]
	start_date = to_unix_timestamp(request.form["start"])
	end_date = to_unix_timestamp(request.form["end"])
	point_multiplier = request.form["point_multiplier"]

	if not start_date or not end_date or start_date >= end_date:
		return render_template("admin/add-contest.html", error="Invalid dates", contest_types=contest_types, contest=contest)
	
	ctype_obj = ContestType.query.filter_by(name=contest_type).first()
	if not ctype_obj:
		return render_template("admin/add-contest.html", error="Invalid contest type", contest_types=contest_types, contest=contest)
	
	if not name:
		return render_template("admin/add-contest.html", error="Invalid name", contest_types=contest_types, contest=contest)
	
	handle_objects.edit_contest(contest, name, ctype_obj.id, start_date, end_date, point_multiplier)
	return redirect(f"/admin/contests/{contest.competition.short_name}")

@contests.route("/admin/delete-contest/<int:contest_id>", methods=["GET", "POST"])
@admin_required
@check_object_exists(Contest, "/admin/competitions")
def delete_contest(contest):	
	if request.method == "GET":
		return render_template("confirm-delete.html", type="contest", text=contest.name)
	
	handle_objects.delete_contest(contest)

	return redirect("/admin/competitions")

@contests.route("/admin/delete-competition/<int:competition_id>", methods=["GET", "POST"])
@admin_required
@check_object_exists(Competition, "/admin/competitions")
def delete_competition(competition):
	if request.method == "GET":
		return render_template("confirm-delete.html", type="competition", text=competition.name)
	
	handle_objects.delete_competition(competition)

	return redirect("/admin/competitions")

@contests.route("/admin/edit-problems/<int:contest_id>")
@admin_required
@check_object_exists(Contest, "/admin/contests")
def edit_problems(contest):
	return render_template("admin/admin-problems.html", contest=contest)

@contests.route("/admin/create-problem/<int:contest_id>", methods=["GET", "POST"])
@admin_required
@check_object_exists(Contest, "/admin/contests")
def create_problem(contest):
	if request.method == "GET":
		return render_template("admin/add-problem.html", contest=contest)
	
	problem_name = request.form["name"]
	description = request.form["description"]

	if not problem_name:
		return render_template("admin/add-problem.html", contest=contest, error="Invalid name")
	
	problem = Problem(name=problem_name, description=description, contest_id=contest.id)
	db.session.add(problem)
	db.session.commit()

	return redirect(f"/admin/edit-problems/{contest.id}")

@contests.route("/admin/edit-problem/<int:problem_id>", methods=["GET", "POST"])
@admin_required
@check_object_exists(Problem, "/admin/contests")
def edit_problem(problem):
	if request.method == "GET":
		return render_template("admin/add-problem.html", contest=problem.contest, problem=problem)
	
	problem_name = request.form["name"]
	description = request.form["description"]

	if not problem_name:
		return render_template("admin/add-problem.html", contest=problem.contest, problem=problem, error="Invalid name")

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

	handle_objects.delete_problem(problem)

	return redirect(f"/admin/edit-problems/{contest_id}")

@contests.route("/admin/problems/<int:problem_id>")
@admin_required
@check_object_exists(Problem, "/admin/contests")
def view_test_cases(problem):
	return render_template("admin/test-cases.html", problem=problem)

@contests.route("/admin/add-test-case-group/<int:problem_id>", methods=["GET", "POST"])
@admin_required
@check_object_exists(Problem, "/admin/contests")
def add_test_case_group(problem):
	if request.method == "GET":
		return render_template("admin/add-test-case-group.html", problem=problem)
	
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
		return render_template("admin/add-test-case-group.html", problem=group.problem, group=group)
	
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
	
	handle_objects.delete_abstract_test_case_group(group)

	return redirect(f"/admin/problems/{problem_id}")

@contests.route("/admin/add-test-case/<int:group_id>", methods=["GET", "POST"])
@admin_required
@check_object_exists(AbstractTestCaseGroup, "/admin/contests")
def add_test_case(group):
	if request.method == "GET":
		return render_template("admin/add-test-case.html", problem=group.problem)
	
	input_data = request.form.get("input")
	output_data = request.form.get("output")

	input_file = request.files["inputfile"]
	output_file = request.files["outputfile"]

	if (not input_data and not input_file.filename) or (not output_data and not output_file.filename):
		return render_template("admin/add-test-case.html", problem=group.problem, error="Invalid input or output")
	
	input = input_data if not input_file.filename else input_file.stream.read().decode("ascii")
	output = output_data if not output_file.filename else output_file.stream.read().decode("ascii")

	tc = AbstractTestCase(input=input, expected_output=output, group_id=group.id)
	db.session.add(tc)
	db.session.commit()

	return redirect(f"/admin/problems/{group.problem.id}")

@contests.route("/admin/edit-test-case/<int:test_case_id>", methods=["GET", "POST"])
@admin_required
@check_object_exists(AbstractTestCase, "/admin/contests")
def edit_test_case(test_case):
	if request.method == "GET":
		return render_template("admin/add-test-case.html", problem=test_case.group.problem, test_case=test_case)
	
	input_data = request.form.get("input")
	output_data = request.form.get("output")

	input_file = request.files["inputfile"]
	output_file = request.files["outputfile"]

	if (not input_data and not input_file.filename) or (not output_data and not output_file.filename):
		return render_template("admin/add-test-case.html", problem=test_case.group.problem, test_case=test_case, error="Invalid input or output")

	input = input_data if not input_file.filename else input_file.stream.read().decode("ascii")
	output = output_data if not output_file.filename else output_file.stream.read().decode("ascii")

	test_case.input = input
	test_case.expected_output = output

	db.session.commit()

	return redirect(f"/admin/problems/{test_case.group.problem.id}")

@contests.route("/admin/delete-test-case/<int:test_case_id>", methods=["GET", "POST"])
@admin_required
@check_object_exists(AbstractTestCase, "/admin/contests")
def delete_test_case(test_case):
	if request.method == "GET":
		return render_template("confirm-delete.html", type="test case", text=test_case.id)
	
	problem_id = test_case.group.problem.id

	handle_objects.delete_test_case(test_case)

	return redirect(f"/admin/problems/{problem_id}")