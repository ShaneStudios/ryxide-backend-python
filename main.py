import subprocess
import sys
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
# Enable CORS for all domains on all routes.
# For production, you might want to restrict this to your specific frontend URL.
CORS(app)

@app.route('/run', methods=['POST'])
def run_python_code():
    """
    Receives Python code in a JSON payload, executes it using subprocess,
    and returns the captured stdout and stderr.
    """
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400

    data = request.get_json()
    code = data.get('code')

    if code is None:
        return jsonify({"error": "Missing 'code' field in JSON payload"}), 400

    if not isinstance(code, str):
         return jsonify({"error": "'code' field must be a string"}), 400

    # --- Security Note ---
    # Running arbitrary code received from users is inherently risky.
    # This uses subprocess which is slightly safer than exec(), but a
    # production system would need much stronger sandboxing (e.g., Docker).
    # We add a timeout for basic protection against infinite loops.
    # Consider resource limits if this were scaled.
    # ---------------------

    stdout = ""
    stderr = ""
    exit_code = 0
    process = None

    try:
        # Use the same Python executable that's running Flask
        # Timeout set to 10 seconds
        process = subprocess.run(
            [sys.executable, '-c', code],
            capture_output=True,
            text=True,
            timeout=10,  # Timeout in seconds
            check=False # Don't raise exception on non-zero exit code
        )
        stdout = process.stdout
        stderr = process.stderr
        exit_code = process.returncode

    except subprocess.TimeoutExpired:
        stderr = "Execution timed out (max 10 seconds)."
        exit_code = -1 # Indicate timeout
    except Exception as e:
        stderr = f"An unexpected error occurred during execution: {str(e)}"
        exit_code = -1 # Indicate general error

    return jsonify({
        "stdout": stdout,
        "stderr": stderr,
        "exit_code": exit_code
    })

if __name__ == '__main__':
    # Render dynamically assigns the port via the PORT environment variable.
    # Default to 8080 for local development if PORT isn't set.
    port = int(os.environ.get('PORT', 8080))
    # Important: Host needs to be '0.0.0.0' to be accessible within Render's container
    app.run(host='0.0.0.0', port=port)