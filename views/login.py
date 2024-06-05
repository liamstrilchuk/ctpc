from flask import render_template, request, redirect
from flask_login import login_user, current_user, logout_user

from models import User
from setup import bcrypt

def login_view():
	if current_user.is_authenticated:
		return redirect("/")
	
	if request.method == "GET":
		return render_template("login.html")
	
	username = request.form["username"]
	password = request.form["password"]

	user = User.query.filter_by(username=username).first()

	if user is None or not bcrypt.check_password_hash(user.password, password):
		return render_template("login.html", error="Invalid username or password")
	
	login_user(user)
	return redirect("/")

def logout_view():
	logout_user()
	return redirect("/")