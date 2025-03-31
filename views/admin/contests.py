from flask import Blueprint, redirect, render_template, request

from models import AbstractTestCase, AbstractTestCaseGroup, Competition, Contest, \
	ContestType, Problem, ProblemTopic, School, SchoolBoard, SchoolCode, Submission, Topic, db
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

	return render_template(
		"admin/admin-contests.html",
		competition=competition,
		total_points=total_points
	)


@contests.route("/admin/competitions")
@admin_required
def competitions_view():
	competitions = Competition.query.all()

	return render_template("admin/admin-competitions.html", competitions=competitions)


@contests.route("/admin/schools/<short_name>")
@admin_required
@check_object_exists(Competition, "/admin/competitions", key_name="short_name")
def schools_view(competition):
	students_by_school = {}
	in_person_teams_by_school = {}

	for school in competition.schools:
		students_by_school[school.id] = 0
		in_person_teams_by_school[school.id] = 0

		for user in school.members:
			if user.role.name == "student":
				students_by_school[school.id] += 1

		for team in school.teams:
			if team.in_person:
				in_person_teams_by_school[school.id] += 1
	
	return render_template(
		"admin/admin-schools.html",
		competition=competition,
		students_by_school=students_by_school,
		in_person_teams_by_school=in_person_teams_by_school
	)


@contests.route("/admin/invite-teams/<int:school_id>", methods=["GET", "POST"])
@admin_required
@check_object_exists(School, "/admin/competitions")
def invite_teams(school):
	if request.method == "GET":
		return render_template("admin/invite-teams.html", school=school)
	
	new_count = request.form.get("new_count")
	try:
		new_count = int(new_count)

		if new_count < 0:
			raise Exception()
	except:
		return render_template("admin/invite-teams.html", school=school, error="Invalid number")
	
	current_in_person = 0
	for team in school.teams:
		if team.in_person:
			current_in_person += 1

	if new_count < current_in_person:
		return render_template(
			"admin/invite-teams.html",
			school=school,
			error="New count cannot be less than number of currently assigned in person teams"
		)
	
	school.in_person_spots = new_count
	db.session.commit()

	return redirect(f"/admin/schools/{school.competition.short_name}")


@contests.route("/admin/school-codes/<short_name>")
@admin_required
@check_object_exists(Competition, "/admin/competitions", key_name="short_name")
def school_codes(competition):
	return render_template(
		"admin/school-codes.html",
		competition=competition,
		codes=SchoolCode.query.filter_by(competition_id=competition.id)
	)


@contests.route("/admin/cutoff-dates/<short_name>", methods=["GET", "POST"])
@admin_required
@check_object_exists(Competition, "/admin/competitions", key_name="short_name")
def cutoff_dates(competition):
	if request.method == "GET":
		return render_template("admin/cutoff-dates.html")
	
	async_start = to_unix_timestamp(request.form.get("async_start"))
	async_end = to_unix_timestamp(request.form.get("async_end"))

	if (async_start is None and async_end is not None) or \
		(async_start is not None and async_end is not None and async_end < async_start):
		return render_template("admin/cutoff-dates.html", error="Invalid async dates")
	
	competition.full_profile_cutoff = to_unix_timestamp(request.form.get("full_profile_cutoff"))
	competition.registration_cutoff = to_unix_timestamp(request.form.get("registration_cutoff"))
	competition.async_start = async_start
	competition.async_end = async_end

	db.session.commit()
	return redirect("/admin/competitions")


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
		return render_template(
			"confirm-delete.html",
			type="school code",
			text=f"for {code.school_name}"
		)
	
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
		return render_template(
			"admin/add-school.html",
			boards=boards,
			error="There is no board with that name"
		)
	
	existing_school = School.query \
		.filter_by(name=school_name, school_board=board, competition_id=competition.id) \
		.first()

	if existing_school is not None:
		return render_template(
			"admin/add-school.html",
			boards=boards,
			error="There is already a school in that board with that name"
		)
		
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
		return render_template(
			"admin/add-competition.html",
			editing=True,
			name=competition.name,
			short_name=competition.short_name,
			competition=competition
		)
	
	name = request.form["name"]
	short_name = request.form["short_name"]

	if not name or not short_name:
		return render_template(
			"admin/add-competition.html",
			error="Invalid name",
			competition=competition
		)
	
	existing_competition = Competition.query.filter_by(short_name=short_name).first()
	if existing_competition:
		return render_template(
			"admin/add-competition.html",
			error="Competition already exists",
			competition=competition
		)

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
		return render_template(
			"admin/add-contest.html",
			error="Invalid dates",
			contest_types=contest_types
		)
	
	ctype_obj = ContestType.query.filter_by(name=contest_type).first()
	if not ctype_obj:
		return render_template(
			"admin/add-contest.html",
			error="Invalid contest type",
			contest_types=contest_types
		)
	
	if not name:
		return render_template(
			"admin/add-contest.html",
			error="Invalid name",
			contest_types=contest_types
		)
	
	try:
		float(point_multiplier)
	except:
		return render_template(
			"admin/add-contest.html",
			error="Invalid point multiplier",
			contest_types=contest_types
		)
	
	handle_objects.add_contest(
		name=name,
		contest_type_id=ctype_obj.id,
		start_date=start_date,
		end_date=end_date,
		competition_id=competition.id,
		point_multiplier=point_multiplier
	)

	return redirect("/admin/competitions")


@contests.route("/admin/duplicate-contest/<int:contest_id>")
@admin_required
@check_object_exists(Contest, "/admin/contests")
def duplicate_contest(contest):
	new_contest = handle_objects.add_contest(
		name=f"{contest.name} (Duplicated)",
		contest_type_id=contest.contest_type_id,
		start_date=contest.start_date,
		end_date=contest.end_date,
		competition_id=contest.competition.id,
		point_multiplier=0
	)

	for problem in contest.problems:
		new_problem = handle_objects.add_problem(
			problem.name,
			problem.description,
			new_contest.id
		)

		for atcg in problem.test_case_groups:
			new_atcg = handle_objects.add_abstract_test_case_group(
				atcg.point_value,
				new_problem.id,
				atcg.is_sample
			)
			new_problem.point_value += new_atcg.point_value
			db.session.commit()

			for atc in atcg.test_cases:
				handle_objects.add_abstract_test_case(
					atc.input,
					atc.expected_output,
					atc.explanation,
					new_atcg.id
				)

	return redirect(f"/admin/contests/{contest.competition.short_name}")


@contests.route("/admin/edit-contest/<int:contest_id>", methods=["GET", "POST"])
@admin_required
@check_object_exists(Contest, "/admin/contests")
def edit_contest(contest):
	contest_types = ContestType.query.all()

	if request.method == "GET":
		return render_template(
			"admin/add-contest.html",
			editing=True,
			name=contest.name,
			contest_types=contest_types,
			contest=contest,
			point_multiplier=contest.point_multiplier
		)
	
	name = request.form["name"]
	contest_type = request.form["contest_type"]
	start_date = to_unix_timestamp(request.form["start"])
	end_date = to_unix_timestamp(request.form["end"])
	point_multiplier = request.form["point_multiplier"]

	if not start_date or not end_date or start_date >= end_date:
		return render_template(
			"admin/add-contest.html",
			error="Invalid dates",
			contest_types=contest_types,
			contest=contest
		)
	
	ctype_obj = ContestType.query.filter_by(name=contest_type).first()
	if not ctype_obj:
		return render_template(
			"admin/add-contest.html",
			error="Invalid contest type",
			contest_types=contest_types,
			contest=contest
		)
	
	if not name:
		return render_template(
			"admin/add-contest.html",
			error="Invalid name",
			contest_types=contest_types,
			contest=contest
		)
	
	handle_objects.edit_contest(contest, name, ctype_obj.id, \
		start_date, end_date, point_multiplier)
	
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
	
	handle_objects.add_problem(problem_name, description, contest.id)

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
		return render_template(
			"admin/add-problem.html",
			contest=problem.contest,
			problem=problem,
			error="Invalid name"
		)

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
	
	handle_objects.add_abstract_test_case_group(point_value, problem.id, is_sample)

	return redirect(f"/admin/problems/{problem.id}")


@contests.route("/admin/edit-test-case-group/<int:group_id>", methods=["GET", "POST"])
@admin_required
@check_object_exists(AbstractTestCaseGroup, "/admin/contests")
def edit_test_case_group(group):
	if request.method == "GET":
		return render_template(
			"admin/add-test-case-group.html",
			problem=group.problem,
			group=group
		)
	
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
	explanation_data = request.form.get("explanation")

	input_file = request.files["inputfile"]
	output_file = request.files["outputfile"]

	if (not input_data and not input_file.filename) or \
		(not output_data and not output_file.filename):
		return render_template(
			"admin/add-test-case.html",
			problem=group.problem,
			error="Invalid input or output"
		)
	
	input = input_data if not input_file.filename else input_file.stream.read().decode("ascii")
	output = output_data if not output_file.filename else output_file.stream.read().decode("ascii")
	explanation = explanation_data

	input = input.replace("\r", "")
	output = output.replace("\r", "")

	handle_objects.add_abstract_test_case(input, output, explanation, group.id)

	return redirect(f"/admin/problems/{group.problem.id}")


@contests.route("/admin/edit-test-case/<int:test_case_id>", methods=["GET", "POST"])
@admin_required
@check_object_exists(AbstractTestCase, "/admin/contests")
def edit_test_case(test_case):
	if request.method == "GET":
		return render_template(
			"admin/add-test-case.html",
			problem=test_case.group.problem,
			test_case=test_case
		)
	
	input_data = request.form.get("input")
	output_data = request.form.get("output")
	explanation_data = request.form.get("explanation")

	input_file = request.files["inputfile"]
	output_file = request.files["outputfile"]
	explanation_file = request.files["explanationfile"]

	if (not input_data and not input_file.filename) or \
		(not output_data and not output_file.filename):
		return render_template(
			"admin/add-test-case.html",
			problem=test_case.group.problem,
			test_case=test_case,
			error="Invalid input or output"
		)

	input = input_data if not input_file.filename else input_file.stream.read().decode("ascii")
	output = output_data if not output_file.filename else output_file.stream.read().decode("ascii")
	explanation = explanation_data if not explanation_file.filename else \
		explanation_file.stream.read().decode("ascii")

	test_case.input = input.replace("\r", "")
	test_case.expected_output = output.replace("\r", "")
	test_case.explanation = explanation

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


@contests.route("/admin/problem-topics")
@admin_required
def view_problem_topics():
	topics = Topic.query.all()
	return render_template("admin/problem-topics.html", topics=topics)


@contests.route("/admin/add-topic", methods=["GET", "POST"])
@admin_required
def add_topic():
	if request.method == "GET":
		return render_template("admin/add-topic.html")
	
	name = request.form.get("name")
	bg_color = request.form.get("bg_color")
	text_color = request.form.get("text_color")
	
	handle_objects.add_topic(name, bg_color, text_color)
	
	return redirect("/admin/problem-topics")


@contests.route("/admin/edit-topic/<int:topic_id>", methods=["GET", "POST"])
@admin_required
@check_object_exists(Topic, "/admin/problem-topics")
def edit_topic(topic):
	if request.method == "GET":
		return render_template("admin/add-topic.html", topic=topic)
	
	name = request.form.get("name")
	bg_color = request.form.get("bg_color")
	text_color = request.form.get("text_color")

	topic.name = name
	topic.bg_color = bg_color
	topic.text_color = text_color

	db.session.commit()
	return redirect("/admin/problem-topics")


@contests.route("/admin/delete-topic/<int:topic_id>", methods=["GET", "POST"])
@admin_required
@check_object_exists(Topic, "/admin/problem-topics")
def delete_topic(topic):
	if request.method == "GET":
		return render_template("confirm-delete.html", type="topic", text=f"with id={topic.id}")
	
	handle_objects.delete_topic(topic)
	return redirect("/admin/problem-topics")


@contests.route("/admin/add-problem-topic/<int:problem_id>", methods=["GET", "POST"])
@admin_required
@check_object_exists(Problem, "/admin")
def add_problem_topic(problem):
	if request.method == "GET":
		topics = Topic.query.all()
		not_included = [i for i in topics if not i in problem.topics]

		return render_template("admin/add-problem-topic.html", topics=not_included, problem=problem)
	
	topic_id = request.form.get("topic")
	existing = ProblemTopic.query.filter_by(topic_id=topic_id, problem_id=problem.id).first()

	if existing is not None:
		return redirect(f"/admin/edit-problems/{problem.contest.id}")
	
	handle_objects.add_problem_topic(topic_id, problem.id)

	return redirect(f"/admin/edit-problems/{problem.contest.id}")


@contests.route("/admin/delete-problem-topic/<int:problem_topic_id>")
@admin_required
@check_object_exists(ProblemTopic, "/admin")
def delete_problem_topic(problem_topic):
	contest_id = problem_topic.problem.contest.id
	db.session.delete(problem_topic)
	db.session.commit()

	return redirect(f"/admin/edit-problems/{contest_id}")