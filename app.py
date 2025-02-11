from flask import Flask, render_template, request, redirect, url_for, session, jsonify , send_from_directory
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from dotenv import load_dotenv
import os
import fal_client
import requests
import cv2
import numpy as np
from deepface import DeepFace
from moviepy import *
import tensorflow as tf

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


# Desabilitar GPU e forçar uso da CPU
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
tf.config.set_visible_devices([], 'GPU')

# Chave da API Fal.AI
FAL_API_KEY = os.getenv("FAL_API_KEY")
STATIC_DIR = "videos"
if not os.path.exists(STATIC_DIR):
    os.makedirs(STATIC_DIR)

@app.route("/videos/<filename>")
def serve_video(filename):
    return send_from_directory(STATIC_DIR, filename)

@app.route("/submit", methods=["POST"])
@login_required
def submit():
    try:
        data = request.get_json()
        if not data or "text" not in data:
            return jsonify({"error": "O campo 'text' é obrigatório"}), 400

        user_prompt = data["text"]
        print("Prompt recebido:", user_prompt)

        def on_queue_update(update):
            if isinstance(update, fal_client.InProgress):
                for log in update.logs:
                    print(log["message"])

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
                "num_images": 2,
            },
            with_logs=True,
            on_queue_update=on_queue_update,
        )

        print("Resposta da API para imagens:", result)

        if "images" in result and result["images"]:
            image_urls = result["images"]
        else:
            return jsonify({"error": "Falha ao gerar imagens"}), 500

        # Baixar as imagens para o diretório static/
        frame_paths = []
        for idx, image_data in enumerate(image_urls):
            try:
                image_url = image_data["url"]  # Pegando apenas a URL correta
                image_response = requests.get(image_url)
                image_response.raise_for_status()
                image_path = os.path.join(STATIC_DIR, f"frame_{idx}.jpg")
                with open(image_path, "wb") as file:
                    file.write(image_response.content)
                frame_paths.append(image_path)
                print(f"Imagem {idx+1} salva com sucesso em {image_path}.")
            except requests.exceptions.RequestException as e:
                print(f"Erro ao baixar a imagem {idx+1}: {e}")

        # Criar animação usando DeepFace
        frames = []
        for img_path in frame_paths:
            animated_face = DeepFace.analyze(img_path=img_path, actions=['emotion'], enforce_detection=False)
            frame = cv2.imread(img_path)
            text = f"Emoção: {animated_face[0]['dominant_emotion']}"
            cv2.putText(frame, text, (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            frames.append(frame)

        if frames:
            video_filename = "generated_video.mp4"
            video_path = os.path.join(STATIC_DIR, video_filename)

            clip = ImageSequenceClip([cv2.cvtColor(f, cv2.COLOR_BGR2RGB) for f in frames if f is not None], fps=5)
            clip.write_videofile(video_path, codec="libx264", fps=5)

            return jsonify({"video_url": f"/videos/{video_filename}"}), 200

        return jsonify({"error": "Erro ao processar vídeo"}), 500
    except Exception as e:
        print("Erro na função submit:", str(e))
        return jsonify({"error": str(e)}), 500

    
@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
