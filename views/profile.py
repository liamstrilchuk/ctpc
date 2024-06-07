from flask import render_template, redirect

from models import User
from util import admin_required

@admin_required
def profile_view(username):
	user = User.query.filter_by(username=username).first()

	if user is None:
		return redirect("/")

	return render_template("profile.html", user=user)