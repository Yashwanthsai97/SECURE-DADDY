from flask import jsonify, render_template, request

from metadata_utils import analyze_uploaded_file


def register_metadata_routes(app):
    @app.route("/metadata")
    def metadata_page():
        return render_template("metadata_extractor.html")

    @app.route("/api/metadata/analyze", methods=["POST"])
    def metadata_analyze():
        uploaded_file = request.files.get("file")

        if not uploaded_file:
            return jsonify({"error": "No file was uploaded."}), 400

        try:
            return jsonify(analyze_uploaded_file(uploaded_file))
        except Exception as error:
            return jsonify({"error": f"Metadata analysis failed: {error}"}), 500
