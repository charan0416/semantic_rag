from flask import Flask, request, jsonify, render_template # Added render_template
from chatbot import get_answer
from ingest import ingest_docs
import os

# Configure template and static folder locations relative to app1.py
app = Flask(__name__, template_folder='templates', static_folder='static')

UPLOAD_FOLDER = "documents"
ALLOWED_EXTENSIONS = {'.pdf', '.docx', '.csv', '.txt','.xlsx', '.xls'}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return os.path.splitext(filename)[1].lower() in ALLOWED_EXTENSIONS

# Route to serve the main HTML page
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    query = data.get("query", "")

    if not query:
        return jsonify({"error": "No query provided"}), 400

    try:
        answer_data = get_answer(query)
        return jsonify({"answer": answer_data})
    except Exception as e:
        app.logger.error(f"Error in /chat endpoint: {e}", exc_info=True)
        return jsonify({"error": "An internal error occurred while processing your chat request."}), 500


@app.route("/ingest", methods=["POST"])
def ingest():
    try:
        ingest_docs()
        return jsonify({"message": "📚 Documents ingested and vector store updated successfully!"})
    except Exception as e:
        app.logger.error(f"Error in /ingest endpoint: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route("/file_upload", methods=["POST"])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file part in the request"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    if file and allowed_file(file.filename):
        # Consider using werkzeug.utils.secure_filename for production
        filename = file.filename
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)

        # Optional: auto-run ingestion
        try:
            ingest_docs()
            return jsonify({"message": f"✅ File '{filename}' uploaded and ingested successfully!"})
        except Exception as e:
            app.logger.error(f"Error in /file_upload during ingestion: {e}", exc_info=True)
            return jsonify({"error": f"Upload succeeded but ingestion failed: {e}"}), 500
    else:
        return jsonify({"error": "Unsupported file type"}), 400


if __name__ == "__main__":
    app.run(debug=True) # Added debug=True for development
