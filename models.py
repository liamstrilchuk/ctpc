from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
import sqlalchemy as sa

db = SQLAlchemy()

class User(UserMixin, db.Model):
	__tablename__ = "users"

	id = sa.Column(sa.Integer, primary_key=True)
	username = sa.Column(sa.String(100), nullable=False, unique=True)
	password = sa.Column(sa.String(100), nullable=False)
	role = sa.Column(sa.String(100), nullable=False)
	team_id = sa.Column(sa.Integer, sa.ForeignKey("teams.id"), nullable=True)
	school_id = sa.Column(sa.Integer, sa.ForeignKey("schools.id"), nullable=True)
	
	def __repr__(self):
		return f"<User {self.username}>"
	
class School(db.Model):
	__tablename__ = "schools"

	id = sa.Column(sa.Integer, primary_key=True)
	name = sa.Column(sa.String(100), nullable=False)
	school_board_id = sa.Column(sa.Integer, sa.ForeignKey("school_boards.id"), nullable=False)
	teams = db.relationship("Team", backref="school", lazy=True)
	members = db.relationship("User", backref="school", lazy=True)

	def __init__(self, name, school_board_id):
		self.name = name
		self.school_board_id = school_board_id
	
	def __repr__(self):
		return f"<School {self.name}>"
	
class SchoolBoard(db.Model):
	__tablename__ = "school_boards"

	id = sa.Column(sa.Integer, primary_key=True)
	name = sa.Column(sa.String(100), nullable=False)
	schools = db.relationship("School", backref="school_board", lazy=True)

	def __init__(self, name):
		self.name = name
	
	def __repr__(self):
		return f"<SchoolBoard {self.name}>"
	
class Team(db.Model):
	__tablename__ = "teams"

	id = sa.Column(sa.Integer, primary_key=True)
	name = sa.Column(sa.String(100), nullable=False)
	school_id = sa.Column(sa.Integer, sa.ForeignKey("schools.id"), nullable=False)
	members = db.relationship("User", backref="team", lazy=True)

	def __init__(self, name, school_id):
		self.name = name
		self.school_id = school_id
	
	def __repr__(self):
		return f"<Team {self.name}>"
	
class Contest(db.Model):
	__tablename__ = "contests"

	id = sa.Column(sa.Integer, primary_key=True)
	name = sa.Column(sa.String(100), nullable=False)
	contest_type = sa.Column(sa.String(100), nullable=False)
	
	def __repr__(self):
		return f"<Contest {self.name}>"
	
class Problem(db.Model):
	__tablename__ = "problems"

	id = sa.Column(sa.Integer, primary_key=True)
	name = sa.Column(sa.String(100), nullable=False)
	contest_id = sa.Column(sa.Integer, sa.ForeignKey("contests.id"), nullable=False)
	
	def __repr__(self):
		return f"<Problem {self.name}>"
	
class Submission(db.Model):
	__tablename__ = "submissions"

	id = sa.Column(sa.Integer, primary_key=True)
	user_id = sa.Column(sa.Integer, sa.ForeignKey("users.id"), nullable=False)
	problem_id = sa.Column(sa.Integer, sa.ForeignKey("problems.id"), nullable=False)
	language = sa.Column(sa.String(10), nullable=False)
	filename = sa.Column(sa.String(100), nullable=False)
	
	def __repr__(self):
		return f"<Submission {self.id}>"