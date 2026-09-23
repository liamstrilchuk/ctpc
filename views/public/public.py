import json
import os

from flask import Blueprint, render_template

public = Blueprint("public", __name__, template_folder="templates")

TIMELINE_DATA_PATH = os.path.join(os.getcwd(), "data", "timeline.json")


def load_timeline_entries():
	if not os.path.exists(TIMELINE_DATA_PATH):
		return []

	with open(TIMELINE_DATA_PATH, "r") as f:
		entries = json.load(f)

	return sorted(entries, key=lambda entry: entry["date"], reverse=True)


@public.route("/about")
def about_view():
	return render_template("public/about.html")


@public.route("/timeline")
def timeline_view():
	return render_template("public/timeline.html", entries=load_timeline_entries())


@public.route("/contact")
def contact_view():
	return render_template("public/contact.html")


@public.route("/platform")
def platform_view():
	return render_template("public/platform.html")
