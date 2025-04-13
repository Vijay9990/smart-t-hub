import os
from flask import Flask
from pymongo import MongoClient
from Google import Create_Service
import base64
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# ===== Flask App Setup =====
app = Flask(__name__)

# ===== MongoDB Setup (Render Cloud-Ready) =====
mongo_uri = os.environ.get("mongodb+srv://charansanthosh1675:Charan@1675@cluster0.6x3ftyc.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
client = MongoClient(mongo_uri)
db = client["ride-booking"]  # <-- Replace with your actual MongoDB database name

# ===== Gmail API Email Function =====
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

# ===== Sample Route to Test Deployment =====
@app.route('/')
def home():
    return " Flask app is deployed successfully on Render!"

# === NOTE ===
# Do NOT add `app.run(...)` — Render uses gunicorn to serve the app.
