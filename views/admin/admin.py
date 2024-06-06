from flask import Blueprint, render_template

from views.admin.manage import manage
from util import admin_required

admin = Blueprint("admin", __name__, template_folder="templates")
admin.register_blueprint(manage)

@admin.route("/admin")
@admin_required
def admin_view():
	return render_template("admin.html")