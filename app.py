from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from dotenv import load_dotenv
import os
import fal_client

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

@app.route("/", methods=["GET", "POST"])
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

# Chave da API Fal.AI
FAL_API_KEY = os.getenv("FAL_API_KEY")  # Pegando do .env

@app.route("/submit", methods=["POST"])
@login_required
def submit():
    try:
        data = request.get_json()  # Captura os dados enviados via JSON
        if not data or "text" not in data:
            return jsonify({"error": "O campo 'text' é obrigatório"}), 400

        user_prompt = data["text"]  # Obtém o texto digitado pelo usuário

        def on_queue_update(update):
            if isinstance(update, fal_client.InProgress):
                for log in update.logs:
                    print(log["message"])

        # Chama a API do Fal.AI para gerar imagem
        result = fal_client.subscribe(
            "fal-ai/fooocus/image-prompt",
            arguments={
                "image_prompt_1": {
                    "weight": 1,
                    "stop_at": 1,
                    "type": "PyraCanny",
                    "image_url": None,
                },
                "prompt": user_prompt,
                "image_size": "landscape_4_3",
                "num_images": 1,
            },
            with_logs=True,
            on_queue_update=on_queue_update,
        )

        # Verifica se a API retornou uma imagem válida
        if "images" in result and result["images"]:
            image_url = result["images"][0]["url"]
            return jsonify({"image_url": image_url}), 200

        return jsonify({"error": "Erro ao gerar imagem"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
