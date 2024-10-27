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

def delete_contest(contest):
	db.session.delete(contest)
	db.session.commit()