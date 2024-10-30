from flask import Flask, request, jsonify, render_template
from flask_socketio import SocketIO, emit

from src.main.config import Config
from src.main.agents.supervisor import Supervisor

# Initialize Flask and Supervisor
app = Flask(__name__)
app.config.from_object(Config)
socketio = SocketIO(app)
supervisor = Supervisor(socketio)
user_responses = {}

@app.route('/')
def index():
    return render_template('index.html')


@socketio.on('send_response')
def handle_send_response(message):
    """Receive messages from the server and send them to the client."""
    print("inside handle_send_response")
    emit('receive_message', message, broadcast=True)


@socketio.on('user_response')
def handle_user_response(data):
    """Receive user response and store it."""
    print("inside handle_user_response")
    user_responses[data['task_id']] = data['response']
    print(user_responses)
    supervisor.process_task(user_responses.pop(data['task_id']))


@app.route('/chat', methods=['POST'])
def chat():
    # Get task from the JSON payload
    data = request.get_json()
    # user_task = data.get("task", "")
    #
    # # Check if user wants to exit (for this API, you could modify the behavior)
    # if user_task.lower() == 'exit':
    #     return jsonify({"message": "Exiting assistant."}), 200
    #
    # # Process task using Supervisor
    # supervisor = Supervisor(socketio, send_response_callback, wait_for_response)
    # response = supervisor.process_task(user_task)

    # Return JSON response
    return jsonify({"response": None}), 200


if __name__ == '__main__':
    #app.run(debug=True)
    socketio.run(app, debug=True, allow_unsafe_werkzeug=True)
