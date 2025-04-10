from flask import Blueprint, render_template

from models import Competition, Contest, Submission, User, Problem, Team, School, UserRole
from util import admin_required, check_object_exists

leaderboard = Blueprint("leaderboard", __name__, template_folder="templates")


def contest_leaderboard_data(contest):
	problems = Problem.query.filter_by(contest_id=contest.id).all()
	problem_id_dict = { problems[i].id: i for i in range(len(problems)) }

	if contest.contest_type.name == "individual":
		submitting_users = User.query \
			.join(Submission, Submission.user_id == User.id) \
			.join(Problem, Problem.id == Submission.problem_id) \
			.join(UserRole, UserRole.id == User.role_id) \
			.filter(Problem.contest_id == contest.id) \
			.filter(UserRole.name == "student") \
			.all()
	else:
		submitting_users = Team.query \
			.join(User, User.team_id == Team.id) \
			.join(Submission, Submission.user_id == User.id) \
			.join(Problem, Problem.id == Submission.problem_id) \
			.filter(Problem.contest_id == contest.id) \
			.all()
	
	user_list = {}
	for user in submitting_users:
		list_key = user.username if contest.contest_type.name == "individual" else user.id
		user_list[list_key] = {
			"problems": [{
				"score": 0,
				"attempted": False
			} for _ in problems],
			"total_score": 0,
			"name": user.username if contest.contest_type.name == "individual" \
				else f"{user.name} ({user.school.name})",
			"obj": user,
			"in_person": (user.team is not None and user.team.in_person) \
				if contest.contest_type.name == "individual" else user.in_person
		}

	all_submissions = Submission.query \
		.join(Problem, Problem.id == Submission.problem_id) \
		.join(User, User.id == Submission.user_id) \
		.filter(Problem.contest_id == contest.id) \
		.order_by(Submission.points_earned.asc()) \
		.all()
		
	for submission in all_submissions:
		if contest.contest_type.name == "team" and \
			(submission.user.team is None or submission.user.team.id not in user_list):
			continue

		list_key = submission.user.username if contest.contest_type.name == "individual" \
			else submission.user.team.id
		
		if not list_key in user_list:
			continue
	
		problem_index = problem_id_dict[submission.problem_id]
		user_list[list_key]["problems"][problem_index]["attempted"] = True
		user_list[list_key]["problems"][problem_index]["score"] = submission.points_earned

	for user in user_list:
		total_score = 0
		for problem in user_list[user]["problems"]:
			total_score += problem["score"]
		user_list[user]["total_score"] = total_score

	sorted_users = {
		k: v for k, v in sorted(
			user_list.items(),
			key=lambda item: item[1]["total_score"],
			reverse=True
		)
	}

	return problems, sorted_users


@leaderboard.route("/contest/<int:contest_id>/leaderboard")
@admin_required
@check_object_exists(Contest, "/competitions")
def contest_leaderboard(contest):
	problems, sorted_users = contest_leaderboard_data(contest)
	
	return render_template(
		"contest/contest-leaderboard.html",
		contest=contest,
		problems=problems,
		sorted_users=sorted_users,
		type="contest"
	)


@leaderboard.route("/competitions/<competition_name>/leaderboard")
@admin_required
@check_object_exists(Competition, "/competitions", key_name="short_name")
def competition_leaderboard(competition):
	contests = Contest.query.filter(
		Contest.point_multiplier > 0,
		Contest.competition_id == competition.id
	).all()

	teams = Team.query \
		.join(School, School.id == Team.school_id) \
		.join(Competition, Competition.id == School.competition_id) \
		.filter(Competition.id == competition.id) \
		.all()
	
	team_data = { team.id: {
		"problems": [{
			"score": 0,
			"attempted": True,
			"obj": contest
		} for contest in contests],
		"total_score": 0,
		"name": f"{team.name} ({team.school.name})",
		"in_person": team.in_person
	} for team in teams }

	for i in range(len(contests)):
		contest = contests[i]
		_, user_data = contest_leaderboard_data(contest)

		if contest.contest_type.name == "individual":
			for x in user_data:
				user = user_data[x]
				if user["obj"].team is None or not user["obj"].team.id in team_data:
					continue

				team_data[user["obj"].team.id]["problems"][i]["score"] += user["total_score"]
				team_data[user["obj"].team.id]["total_score"] += user["total_score"] * contest.point_multiplier
		else:
			for x in user_data:
				team = user_data[x]
				if not team["obj"].id in team_data:
					continue

				team_data[team["obj"].id]["problems"][i]["score"] = team["total_score"]
				team_data[team["obj"].id]["total_score"] += team["total_score"] * contest.point_multiplier

	sorted_teams = {
		k: v for k, v in sorted(
			team_data.items(),
			key=lambda item: item[1]["total_score"],
			reverse=True
		)
	}

	return render_template(
		"contest/contest-leaderboard.html",
		contest=competition,
		problems=contests,
		sorted_users=sorted_teams,
		type="competition"
	)