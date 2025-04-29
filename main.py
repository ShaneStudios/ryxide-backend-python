import subprocess
import sys
import os
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)

# --- Explicit CORS Configuration ---
# Define the origins allowed to access your backend.
allowed_origins = [
    "https://shanestudios.github.io", # Your GitHub Pages site
    "http://localhost:8080",      # Common local dev server port (adjust if needed)
    "http://127.0.0.1:8080",    # Another local possibility (adjust if needed)
    # Add any other origins you test from (e.g., specific ports)
]
# Apply CORS settings specifically to the /run route
# supports_credentials=True is usually needed if you ever plan to send cookies,
# but might not be strictly necessary here. Keep it for now unless it causes issues.
CORS(app, resources={r"/run": {"origins": allowed_origins}}, supports_credentials=True)
# ----------------------------------

@app.route('/run', methods=['POST', 'OPTIONS']) # Ensure OPTIONS is handled
def run_python_code():
    if request.method == 'OPTIONS':
        # Preflight response handled by Flask-CORS based on the config above
        return jsonify(success=True), 200

    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400

    data = request.get_json()
    code = data.get('code')

    if code is None:
        return jsonify({"error": "Missing 'code' field"}), 400
    if not isinstance(code, str):
         return jsonify({"error": "'code' field must be a string"}), 400

    stdout = ""
    stderr = ""
    exit_code = 0
    process = None

    try:
        process = subprocess.run(
            [sys.executable, '-c', code],
            capture_output=True, text=True, timeout=10, check=False
        )
        stdout = process.stdout
        stderr = process.stderr
        exit_code = process.returncode
    except subprocess.TimeoutExpired:
        stderr = "Execution timed out (max 10 seconds)."
        exit_code = 137
    except Exception as e:
        stderr = f"Execution Error: {str(e)}"
        exit_code = 1
    finally:
        pass # subprocess.run handles cleanup

    return jsonify({
        "stdout": stdout,
        "stderr": stderr,
        "exit_code": exit_code
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    # Host 0.0.0.0 is crucial for Render/Docker environments
    app.run(host='0.0.0.0', port=port)
