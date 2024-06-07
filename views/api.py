from flask import Blueprint
from flask_login import login_required

from models import SchoolBoard, User, School, UserRole
from util import admin_required

api = Blueprint("api", __name__)

def error(message):
	return { "error": message }

@api.route("/api/users")
@admin_required
def get_users():
	users = User.query.all()
	json_data = []

	for user in users:
		json_data.append({
			"username": user.username,
			"school": user.school,
			"role": user.role
		})

	return { "users": json_data }

@api.route("/api/boards")
@login_required
def get_boards():
	boards = SchoolBoard.query.all()
	json_data = []

	for board in boards:
		json_data.append(board.name)

	return { "boards": json_data }

@api.route("/api/schools")
@login_required
def get_schools():
	schools = School.query.all()
	json_data = []

	for school in schools:
		json_data.append({
			"name": school.name,
			"board": school.school_board.name,
			"id": school.id
		})

	return { "schools": json_data }

@api.route("/api/complete-structure")
@admin_required
def complete_structure():
	boards = SchoolBoard.query.all()
	teachers = User.query.filter_by(role=UserRole.query.filter_by(name="teacher").first()).all()
	json_data = []
	
	for board in boards:
		board_data = {
			"name": board.name,
			"schools": [],
			"id": board.id
		}

		for school in board.schools:
			school_data = {
				"name": school.name,
				"teams": [],
				"teachers": [],
				"id": school.id
			}

			for teacher in teachers:
				if teacher.school == school:
					school_data["teachers"].append(teacher.username)

			for team in school.teams:
				team_data = {
					"name": team.name,
					"members": [],
					"id": team.id
				}

				for member in team.members:
					team_data["members"].append(member.username)

				school_data["teams"].append(team_data)

			board_data["schools"].append(school_data)
		
		json_data.append(board_data)

	return { "structure": json_data }