from flask import Flask, request, jsonify, render_template
from flask_socketio import SocketIO, emit

from main.util.google_auth import GoogleAuth
from src.main.config import Config
from src.main.agents.supervisor import Supervisor

# Initialize Flask and Supervisor
app = Flask(__name__)
app.config.from_object(Config)
socketio = SocketIO(app)
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
    if data.get('is_new_conversation', True):
        # Only process the task if it's a new conversation
        supervisor.process_task(user_responses.pop(data['task_id']))


def wait_for_response(task_id):
    """Wait for a response from the user for a given task ID."""
    while task_id not in user_responses:
        socketio.sleep(0.1)
    response = user_responses.pop(task_id)
    return response


def send_response_callback(task_id, message):
    """Send a message to the client along with task_id."""
    socketio.emit('receive_message', {'task_id': task_id, 'message': message})


def send_task_completed():
    """Send a message to the client indicating current session is over."""
    socketio.emit('task_completed', None)


def send_task_failed():
    """Send a message to the client indicating current session was failed."""
    socketio.emit('task_failed', {
        'message': "Sorry, there seems to be some problem, can you type your question again?"})


@app.route('/chat', methods=['POST'])
def chat():
    # Get task from the JSON payload
    data = request.get_json()
    user_task = data.get("task", "")

    # Check if user wants to exit (for this API, you could modify the behavior)
    if user_task.lower() == 'exit':
        return jsonify({"message": "Exiting assistant."}), 200

    # Process task using Supervisor
    # supervisor = Supervisor(socketio, send_response_callback, wait_for_response)
    # response = supervisor.process_task(user_task)

    # Return JSON response
    return jsonify({
        "response": "You are part of a multi-agent system designed to be a personal assistant for the user. Specifically, you are the **Scheduling Agent** responsible for scheduling and creating meetings on behalf of the user."}), 200


if __name__ == '__main__':
    # app.run(debug=True, port=4400)
    GoogleAuth().authenticate()
    supervisor = Supervisor(send_response_callback, wait_for_response, send_task_completed, send_task_failed)
    socketio.run(app, debug=True, allow_unsafe_werkzeug=True, port=4400)
