from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
import google.generativeai as genai
import os

genai.configure(api_key="AIzaSyAXNUMB2Tm5I8zpXTcJgd9LQnrjap5j_uU")  # Secure in env

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

model = genai.GenerativeModel('gemini-1.5-flash')

# Store chat sessions with Gemini chat instances & history
chat_histories = {}

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/chat', methods=['POST'])
def chat_response():
    data = request.json
    session_id = data.get('session_id')
    user_input = data.get('message')

    if not session_id or not user_input:
        return jsonify({"error": "Missing session_id or message"}), 400

    if session_id not in chat_histories:
        chat_histories[session_id] = {
            "chat": model.start_chat(history=[]),
            "history": []
        }

    chat = chat_histories[session_id]["chat"]

    try:
        response = chat.send_message(user_input)
        bot_text = response.text

        # Save history
        chat_histories[session_id]["history"].append({"role": "user", "content": user_input})
        chat_histories[session_id]["history"].append({"role": "assistant", "content": bot_text})

        return jsonify({"response": bot_text})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file part in request"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400

    try:
        filepath = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(filepath)
        return jsonify({"response": f"📎 File '{file.filename}' uploaded successfully."})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)
