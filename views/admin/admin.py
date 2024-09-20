from flask import Blueprint, redirect, render_template, request

from models import Contest
from views.admin.manage import manage
from views.admin.contests import contests
from util import admin_required

admin = Blueprint("admin", __name__, template_folder="templates")
admin.register_blueprint(manage)
admin.register_blueprint(contests)

@admin.route("/admin")
@admin_required
def admin_view():
	return render_template("admin/admin.html")