import io

from flask import jsonify, render_template, request, send_file
from PyPDF2 import PdfReader, PdfWriter


def register_pdf_routes(app):
    @app.route("/pdftool")
    def pdf_tool_page():
        return render_template("pdf-tool.html")

    @app.route("/api/pdf/unlock", methods=["POST"])
    def pdf_unlock():
        uploaded_file = request.files.get("file")
        password = (request.form.get("password") or "").strip()

        if not uploaded_file:
            return jsonify({"error": "No PDF file was uploaded."}), 400

        if not password:
            return jsonify({"error": "No password was provided."}), 400

        if not uploaded_file.filename.lower().endswith(".pdf"):
            return jsonify({"error": "Only PDF files are supported."}), 400

        try:
            reader = PdfReader(uploaded_file.stream)

            if not reader.is_encrypted:
                return jsonify({"error": "This PDF is not encrypted."}), 400

            decrypt_result = reader.decrypt(password)
            if not decrypt_result:
                return jsonify({"error": "The password was not accepted for this PDF."}), 400

            writer = PdfWriter()

            for page in reader.pages:
                writer.add_page(page)

            if reader.metadata:
                safe_metadata = {}
                for key, value in reader.metadata.items():
                    if value is None:
                        continue
                    safe_metadata[str(key)] = str(value)

                if safe_metadata:
                    writer.add_metadata(safe_metadata)

            output_stream = io.BytesIO()
            writer.write(output_stream)
            output_stream.seek(0)

            original_name = uploaded_file.filename.rsplit(".", 1)[0]
            download_name = f"{original_name}-unlocked.pdf"

            return send_file(
                output_stream,
                as_attachment=True,
                download_name=download_name,
                mimetype="application/pdf",
            )
        except Exception as error:
            return jsonify({"error": f"Unlock failed: {error}"}), 500
