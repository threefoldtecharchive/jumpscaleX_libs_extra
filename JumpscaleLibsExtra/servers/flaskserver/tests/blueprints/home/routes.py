from flask import render_template
from blueprints.home import blueprint
from Jumpscale import j


@blueprint.route("/", methods=["GET"])
def route_index():
    # j.shell()
    return render_template("index.html")
