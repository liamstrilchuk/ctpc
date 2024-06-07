from flask import Blueprint, render_template, redirect, request
from flask_login import login_required, current_user
from time import time

from models import Contest, Problem
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

	return render_template("contest.html", contest=contest, current_time=time())

@main.route("/problem/<int:problem_id>")
@login_required
@check_object_exists(Problem, "/contests")
def problem_view(problem):
	if time() < problem.contest.start_date:
		return redirect("/contests")

	return render_template("problem.html", problem=problem)