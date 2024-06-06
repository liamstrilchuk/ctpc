from flask import Blueprint, redirect, render_template, request

from models import Contest, Problem, db
from util import admin_required, to_unix_timestamp, check_contest_exists

contests = Blueprint("contests", __name__, template_folder="templates")

@contests.route("/admin/contests")
@admin_required
def contests_view():
	contests = Contest.query.all()

	return render_template("admin-contests.html", contests=contests)

@contests.route("/admin/add-contest", methods=["GET", "POST"])
@admin_required
def add_contest():
	if request.method == "GET":
		return render_template("add-contest.html")
	
	name = request.form["name"]
	contest_type = request.form["contest_type"]
	start_date = to_unix_timestamp(request.form["start"])
	end_date = to_unix_timestamp(request.form["end"])

	if not start_date or not end_date or start_date >= end_date:
		return render_template("add-contest.html", error="Invalid dates")
	
	if not contest_type in ("individual", "team"):
		return render_template("add-contest.html", error="Invalid contest type")
	
	if not name:
		return render_template("add-contest.html", error="Invalid name")
	
	contest = Contest(name=name, contest_type=contest_type, start_date=start_date, end_date=end_date)
	db.session.add(contest)
	db.session.commit()

	return redirect("/admin/contests")

@contests.route("/admin/edit-contest/<int:contest_id>", methods=["GET", "POST"])
@admin_required
@check_contest_exists
def edit_contest(contest):
	if request.method == "GET":
		return render_template("add-contest.html", editing=True, name=contest.name)
	
	name = request.form["name"]
	contest_type = request.form["contest_type"]
	start_date = to_unix_timestamp(request.form["start"])
	end_date = to_unix_timestamp(request.form["end"])

	if not start_date or not end_date or start_date >= end_date:
		return render_template("add-contest.html", error="Invalid dates")
	
	if not contest_type in ("individual", "team"):
		return render_template("add-contest.html", error="Invalid contest type")
	
	if not name:
		return render_template("add-contest.html", error="Invalid name")
	
	contest.name = name
	contest.contest_type = contest_type
	contest.start_date = start_date
	contest.end_date = end_date

	db.session.commit()
	return redirect("/admin/contests")

@contests.route("/admin/delete-contest/<int:contest_id>", methods=["GET", "POST"])
@admin_required
@check_contest_exists
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
@check_contest_exists
def edit_problems(contest):
	return render_template("admin-problems.html", contest=contest)

@contests.route("/admin/create-problem/<int:contest_id>", methods=["GET", "POST"])
@admin_required
@check_contest_exists
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
def edit_problem(problem_id):
	problem = Problem.query.filter_by(id=problem_id).first()

	if not problem:
		return redirect("/admin/contests")
	
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
def delete_problem(problem_id):
	problem = Problem.query.filter_by(id=problem_id).first()

	if not problem:
		return redirect("/admin/contests")
	
	if request.method == "GET":
		return render_template("confirm-delete.html", type="problem", text=problem.name)

	contest_id = problem.contest.id
	
	for tc in problem.test_cases:
		db.session.delete(tc)
	
	db.session.delete(problem)
	db.session.commit()

	return redirect(f"/admin/edit-problems/{contest_id}")