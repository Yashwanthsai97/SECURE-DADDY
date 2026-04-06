from flask import render_template


def register_osint_routes(app):
    @app.route("/osint")
    def osint_page():
        return render_template("osint_tools_page.html")
