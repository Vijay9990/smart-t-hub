# pip install --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib
from Google import Create_Service
import base64
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import os
from flask import Flask
from pymongo import MongoClient

# === Flask Setup ===
app = Flask(__name__)

# === MongoDB Setup using Render-friendly environment variable ===
mongo_uri = os.environ.get("mongodb+srv://charansanthosh1675:Charan@1675@cluster0.6x3ftyc.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
client = MongoClient(mongo_uri)
db = client["ride-booking"]  # Replace with your actual database name

# === Gmail API Email Sending ===
def send_email(subject, message, to):
    CLIENT_SECRET_FILE = 'credentials.json'
    API_NAME = 'gmail'
    API_VERSION = 'v1'
    SCOPES = ['https://mail.google.com/']

    service = Create_Service(CLIENT_SECRET_FILE, API_NAME, API_VERSION, SCOPES)
    
    emailMsg = message
    mimeMessage = MIMEMultipart()
    mimeMessage['to'] = to
    mimeMessage['subject'] = subject
    mimeMessage.attach(MIMEText(emailMsg, 'plain'))

    raw_string = base64.urlsafe_b64encode(mimeMessage.as_bytes()).decode()
    message = service.users().messages().send(userId='me', body={'raw': raw_string}).execute()
    # print(message)

# === Example route (you can add your actual routes below) ===
@app.route('/')
def home():
    return "Your Flask app is working!"

# === Run only if executed directly ===
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))  # default to 5000 for local
    app.run(host='0.0.0.0', port=port, debug=True)
