import base64
import os

from flask import Flask, render_template
from flask_socketio import SocketIO, emit

from main.agents.impl.rag_agent import RAGAgent
from main.util.google_auth import GoogleAuth
from src.main.config import Config
from src.main.agents.supervisor import Supervisor
from flask_cors import CORS

# Initialize Flask
app = Flask(__name__)
CORS(app)
app.config.from_object(Config)
socketio = SocketIO(app)
user_responses = {}
UPLOAD_FOLDER = os.path.join(app.root_path, 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


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


@socketio.on('upload_pdf')
def handle_pdf_upload(data):
    # Get PDF data and file name from the client
    pdf_data = data['pdf_data']
    pdf_name = data['pdf_name']

    # Ensure the file name ends with .pdf
    if not pdf_name.lower().endswith('.pdf'):
        pdf_name += '.pdf'

    # Extract the base64-encoded content after 'data:application/pdf;base64,'
    pdf_base64 = pdf_data.split(',')[1]

    # Decode base64 to binary PDF data
    pdf_binary = base64.b64decode(pdf_base64)

    # Save the binary data to a file
    file_path = os.path.join(UPLOAD_FOLDER, pdf_name)
    with open(file_path, 'wb') as pdf_file:
        pdf_file.write(pdf_binary)

    print(f"Received and saved PDF: {pdf_name} at {file_path}")

    RAGAgent.update_vectorstore()
    socketio.emit('pdf_uploaded', None)

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


if __name__ == '__main__':
    GoogleAuth().authenticate()
    supervisor = Supervisor(send_response_callback, wait_for_response, send_task_completed, send_task_failed)
    socketio.run(app, debug=True, allow_unsafe_werkzeug=True, port=4400)
