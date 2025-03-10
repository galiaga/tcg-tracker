from flask import Blueprint, render_template

frontend_bp = Blueprint("frontend", __name__)

@frontend_bp.route("/login", methods=["GET"])
def login_page():
    return render_template("login.html")
