import requests
from flask import jsonify, render_template, request


def register_ip_routes(app):
    @app.route("/ip")
    def ip_page():
        return render_template("ip_intelligence.html")

    @app.route("/api/ip")
    def ip_lookup():
        ip = request.args.get("ip")

        if not ip:
            return jsonify({"error": "No IP provided"}), 400

        try:
            response = requests.get(f"http://ip-api.com/json/{ip}")
            data = response.json()
            return jsonify(data)
        except Exception as error:
            return jsonify({"error": str(error)}), 500
