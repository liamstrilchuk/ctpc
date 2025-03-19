from flask import Blueprint, render_template

from views.admin.manage import manage
from views.admin.contests import contests
from views.admin.leaderboard import leaderboard
from util import admin_required

admin = Blueprint("admin", __name__, template_folder="templates")
admin.register_blueprint(manage)
admin.register_blueprint(contests)
admin.register_blueprint(leaderboard)


@admin.route("/admin")
@admin_required
def admin_view():
	return render_template("admin/admin.html")