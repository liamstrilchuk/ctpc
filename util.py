from datetime import datetime
from flask import redirect
from flask_login import current_user
import random

def generate_random_password():
	characters = "1234567890QWERTYUIOPASDFGHJKLZXCVBNMqwertyuiopasdfghjklzxcvbnm"
	length = 12

	return "".join([random.choice(characters) for _ in range(length)])

def to_unix_timestamp(timestamp):
	try:
		dt = datetime.strptime(timestamp, "%Y-%m-%dT%H:%M")

		return int(dt.timestamp())
	except:
		return None

def admin_required(func):
	def wrapper(*args, **kwargs):
		if not current_user.is_authenticated:
			return redirect("/")

		if not current_user.role.name == "admin":
			return redirect("/")

		return func(*args, **kwargs)
	
	wrapper.__name__ = func.__name__
	
	return wrapper

def check_object_exists(classtype, redir_to):
	def decorator(func):
		def wrapper(**kwargs):
			contest = classtype.query.filter_by(id=kwargs[list(kwargs.keys())[0]]).first()

			if not contest:
				return redirect(redir_to)
			
			return func(contest)
		
		wrapper.__name__ = func.__name__
		return wrapper

	return decorator