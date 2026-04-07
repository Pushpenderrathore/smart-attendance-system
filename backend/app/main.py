from flask import Flask
from flask_cors import CORS
from routes.session    import session_bp
from routes.attendance import attendance_bp
from routes.teacher    import teacher_bp
from routes.auth       import auth_bp

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

app.register_blueprint(auth_bp,        url_prefix="/auth")
app.register_blueprint(session_bp,     url_prefix="/session")
app.register_blueprint(attendance_bp,  url_prefix="/attendance")
app.register_blueprint(teacher_bp,     url_prefix="/teacher")

@app.route("/health")
def health():
    return {"status": "ok", "version": "2.0", "security": "JWT+RateLimit+HashedOTP"}

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
