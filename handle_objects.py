from models import *

def add_school(name, school_board_id, competition_id):
	school = School(name=name, school_board_id=school_board_id, competition_id=competition_id)
	db.session.add(school)
	db.session.commit()

def add_competition(name, short_name):
	competition = Competition(name=name, short_name=short_name)
	db.session.add(competition)
	db.session.commit()

def edit_competition(competition, name, short_name):
	competition.name = name
	competition.short_name = short_name
	db.session.commit()

def add_contest(name, contest_type_id, start_date, end_date, point_multiplier, competition_id):
	contest = Contest(
		name=name,
		contest_type_id=contest_type_id,
		start_date=start_date,
		end_date=end_date,
		competition_id=competition_id,
		point_multiplier=point_multiplier
	)
	db.session.add(contest)
	db.session.commit()

def edit_contest(contest, name, contest_type_id, start_date, end_date, point_multiplier):
	contest.name = name
	contest.contest_type_id = contest_type_id
	contest.start_date = start_date
	contest.end_date = end_date
	contest.point_multiplier = point_multiplier
	db.session.commit()

def delete_test_case(tc):
	db.session.delete(tc)
	db.session.commit()

def delete_test_case_group(tcg):
	for tc in tcg.test_cases:
		delete_test_case(tc)

	db.session.delete(tcg)
	db.session.commit()

def delete_submission(submission):
	for tcg in submission.test_case_groups:
		delete_test_case_group(tcg)

	db.session.delete(submission)
	db.session.commit()

def delete_abstract_test_case(atc):
	db.session.delete(atc)
	db.session.commit()

def delete_abstract_test_case_group(atcg):
	atcg.problem.point_value -= atcg.point_value

	for atc in atcg.test_cases:
		delete_abstract_test_case(atc)

	db.session.delete(atcg)
	db.session.commit()

def delete_problem(problem):
	for sub in problem.submissions:
		delete_submission(sub)

	for atcg in problem.test_case_groups:
		delete_abstract_test_case_group(atcg)

	db.session.delete(problem)
	db.session.commit()

def delete_contest(contest):
	for problem in contest.problems:
		delete_problem(problem)

	db.session.delete(contest)
	db.session.commit()

def delete_competition(competition):
	for contest in competition.contests:
		delete_contest(contest)

	db.session.delete(competition)
	db.session.commit()

def delete_user(user):
	for sub in user.submissions:
		delete_submission(sub)

	db.session.delete(user)
	db.session.commit()

def delete_team(team):
	for student in team.members:
		student.team_id = None

	db.session.delete(team)
	db.session.commit()