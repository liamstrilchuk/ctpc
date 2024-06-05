from flask import render_template

def index_view():
	return render_template("index.html")