from flask import Blueprint, jsonify

chat_bp = Blueprint("chat", __name__, url_prefix="/api")

@chat_bp.route('/chat', methods=["POST"])
def chat():
    return jsonify({"reply": "Chat endpoint placeholder"})


