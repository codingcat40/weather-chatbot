from flask import Flask, jsonify
from flask_cors import CORS

from config import Config
from routes.chat import chat_bp

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    CORS(app, origins=Config.CORS_ORIGINS)
    
    app.register_blueprint(chat_bp)
    
    @app.route("/api/health", methods=["GET"])
    def health():
        return jsonify({"status": "ok"})
    
    return app
