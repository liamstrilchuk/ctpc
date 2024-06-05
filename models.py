from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
import sqlalchemy as sa

db = SQLAlchemy()

class User(UserMixin, db.Model):
	__tablename__ = "users"

	id = sa.Column(sa.Integer, primary_key=True)
	username = sa.Column(sa.String(100), nullable=False, unique=True)
	password = sa.Column(sa.String(100), nullable=False)
	school = sa.Column(sa.String(100), nullable=False)
	role = sa.Column(sa.String(100), nullable=False)
	
	def __repr__(self):
		return f"<User {self.username}>"