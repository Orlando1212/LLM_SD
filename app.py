from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from dotenv import load_dotenv
import os

app = Flask(__name__)
load_dotenv()

app.secret_key = os.getenv("SECRET_KEY", "supersecreta")

# Configuração de Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

# Usuário Mock
class User(UserMixin):
    def __init__(self, id):
        self.id = id

# Carregar usuário
@login_manager.user_loader
def load_user(user_id):
    return User(user_id)

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        if username == os.getenv("USERNAME") and password == os.getenv("PASSWORD"):
            user = User(username)
            login_user(user)
            return redirect(url_for("dashboard"))
    return render_template("login.html")

@app.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html", username=current_user.id)

@app.route("/submit", methods=["POST"])
@login_required
def submit():
    data = request.form.get("text")
    return jsonify({"message": "Texto recebido", "text": data})

@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(debug=True)