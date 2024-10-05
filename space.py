from flask import Flask, request, render_template, redirect, session, url_for
from flask_sqlalchemy import SQLAlchemy
import bcrypt
import re
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
import os

app = Flask(_name_)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db = SQLAlchemy(app)
app.secret_key = 'secret_key'

# Gmail SMTP server configuration
SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 587
SMTP_USERNAME = 'nihadgurbanov858585@gmail.com'
SMTP_PASSWORD = 'omggdilmuvbludpv'

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)

    def _init_(self, name, email, password):
        self.name = name
        self.email = email
        self.password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    def check_password(self, password):
        return bcrypt.checkpw(password.encode('utf-8'), self.password.encode('utf-8'))

with app.app_context():
    db.create_all()

def login_required(f):
    def wrap(*args, **kwargs):
        if 'email' not in session:
            return redirect(url_for('login', error='You must be logged in to view this page.'))
        return f(*args, **kwargs)
    wrap._name_ = f._name_
    return wrap

def validate_password(password):
    if len(password) < 8:
        return False, 'Password must be at least 8 characters long.'
    if not re.search(r'\d', password):
        return False, 'Password must contain at least one number.'
    return True, ''

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']

        valid, message = validate_password(password)
        if not valid:
            return render_template('register.html', error=message)

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            return render_template('register.html', error='Email already registered.')

        new_user = User(name=name, email=email, password=password)
        db.session.add(new_user)
        db.session.commit()
        return redirect('/login')

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            session['email'] = user.email
            return redirect('/phishingtypes')
        else:
            return render_template('login.html', error='Invalid email or password.')

    return render_template('login.html', error=request.args.get('error'))

@app.route('/phishingtypes')
@login_required
def phishingtypes():
    user = User.query.filter_by(email=session['email']).first()
    return render_template('phishingtypes.html', user=user)

@app.route('/profile')
@login_required
def profile():
    user = User.query.filter_by(email=session['email']).first()
    return render_template("profile.html", user=user)

@app.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        current_password = request.form['current_password']
        new_password = request.form['new_password']
        confirm_new_password = request.form['confirm_new_password']

        user = User.query.filter_by(email=session['email']).first()

        if not user.check_password(current_password):
            return render_template('change_password.html', user=user, error='Current password is incorrect.')

        valid, message = validate_password(new_password)
        if not valid:
            return render_template('change_password.html', user=user, error=message)

        if new_password != confirm_new_password:
            return render_template('change_password.html', user=user, error='New passwords do not match.')

        user.password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        db.session.commit()
        return redirect(url_for('profile', success='Password successfully changed.'))

    user = User.query.filter_by(email=session['email']).first()
    return render_template('change_password.html', user=user)

@app.route('/change-email', methods=['POST'])
@login_required
def change_email():
    new_email = request.form['new_email']

    existing_user = User.query.filter_by(email=new_email).first()
    if existing_user:
        user = User.query.filter_by(email=session['email']).first()
        return render_template('change_password.html', user=user, error='New email already registered.')

    user = User.query.filter_by(email=session['email']).first()
    user.email = new_email
    db.session.commit()
    session['email'] = user.email  # Update session with the new email
    return redirect(url_for('profile', success='Email successfully changed.'))

@app.route('/dashboard')
@login_required
def dashboard():
    user = User.query.filter_by(email=session['email']).first()
    return render_template('dashboard.html', user=user)

@app.route('/quiz')
def quiz():
    return render_template('quiz.html')

@app.route('/logout')
def logout():
    session.pop('email', None)
    return render_template('login.html', error=request.args.get('error'))

@app.route('/send-email', methods=['GET', 'POST'])
@login_required
def send_email():
    if request.method == 'POST':
        recipient = request.form['recipient']
        subject = request.form['subject']
        message = request.form['message']
        html_content = request.form.get('html-content')  # New field for HTML content
        image_file = request.files.get('image')

        if image_file:
            image_path = image_file.read()  # Read image file content
        else:
            image_path = None

        msg = MIMEMultipart()
        msg['From'] = SMTP_USERNAME
        msg['To'] = recipient
        msg['Subject'] = subject

        if html_content:
            msg.attach(MIMEText(html_content, 'html'))
        else:
            msg.attach(MIMEText(message, 'plain'))

        # Attach image if provided
        if image_path:
            img = MIMEImage(image_path, name=os.path.basename(image_file.filename))
            msg.attach(img)

        try:
            with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
                server.starttls()
                server.login(SMTP_USERNAME, SMTP_PASSWORD)
                server.sendmail(SMTP_USERNAME, recipient, msg.as_string())
            return '''
                <!DOCTYPE html>
                <html lang="en">
                <head>
                    <meta charset="UTF-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    <title>Email Sent</title>
                </head>
                <body>
                    <h1>Email Sent</h1>
                    <p>Email has been sent successfully.</p>
                    <a href="/dashboard">Back to Dashboard</a>
                </body>
                </html>
            '''
        except Exception as e:
            return f'''
                <!DOCTYPE html>
                <html lang="en">
                <head>
                    <meta charset="UTF-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    <title>Failed to Send Email</title>
                </head>
                <body>
                    <h1>Failed to Send Email</h1>
                    <p>Failed to send email: {e}</p>
                    <a href="/send-email">Try Again</a>
                </body>
                </html>
            '''

    return '''
        <!DOCTYPE html>
<html lang="en">
<head>
    <title>Send Email</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body {
            background-color: #f0f8ff;
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 0;
        }
        .container {
            max-width: 600px;
            margin: 50px auto;
            background: #ffffff;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
        }
        h2 {
            text-align: center;
            color: #333;
        }
        .form-group {
            margin-bottom: 20px;
        }
        .form-group label {
            display: block;
            margin-bottom: 8px;
            font-weight: bold;
            color: #333;
        }
        .form-group input[type="email"],
        .form-group input[type="text"],
        .form-group textarea,
        .form-group input[type="file"] {
            width: 100%;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 4px;
            box-sizing: border-box;
        }
        .form-group textarea {
            resize: vertical;
        }
        .btn {
            display: block;
            width: 100%;
            padding: 12px;
            background-color: #007bff;
            color: #ffffff;
            border: none;
            border-radius: 4px;
            font-size: 16px;
            cursor: pointer;
            text-align: center;
            text-decoration: none;
        }
        .btn-primary {
            background-color: #28a745;
        }
        .btn-secondary {
            background-color: #6c757d;
        }
        .btn:hover {
            opacity: 0.9;
        }
        .btn-secondary {
            background-color: #6c757d;
        }
        .btn-secondary:hover {
            background-color: #5a6268;
        }
    </style>
</head>
<body>
<div class="container">
    <h2>Send Email</h2>
    <form action="/send-email" method="post" enctype="multipart/form-data">
        <div class="form-group">
            <label for="recipient">Recipient Email:</label>
            <input type="email" id="recipient" name="recipient" required>
        </div>
        <div class="form-group">
            <label for="subject">Subject:</label>
            <input type="text" id="subject" name="subject" required>
        </div>
        <div class="form-group">
            <label for="message">Plain Text Message:</label>
            <textarea id="message" name="message" rows="4"></textarea>
        </div>
        <div class="form-group">
            <label for="html-content">HTML Content:</label>
            <textarea id="html-content" name="html-content" rows="4"></textarea>
        </div>
        <div class="form-group">
            <label for="image">Attach Image:</label>
            <input type="file" id="image" name="image" accept="image/*">
        </div>
        <button type="submit" class="btn btn-primary">Send Email</button>
    </form>
    <br>
    <a href="/dashboard" class="btn btn-secondary">Back to Dashboard</a>
</div>
</body>
</html>
    '''

if _name_ == '_main_':
    app.run(debug=True, port=5001)
____________________________________________________________________________________________________
Connect his code this the code below so my code runs with Azure instead of Flask as database
____________________________________________________________________________________________________
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient

# Replace with your connection string
connection_string = "DefaultEndpointsProtocol=https;AccountName=satelliteazer;AccountKey=eFIA4fU7oBT8GnEfBX7x7ybabRnpiQsrciLpK0A0XAEd2niYcsiFj/kc/sVcz0wv55hk5q3q1ZUy+AStLntw1A==;EndpointSuffix=core.windows.net"

# Create BlobServiceClient
blob_service_client = BlobServiceClient.from_connection_string(connection_string)

# Create or access the container
container_name = "geospatial-data"
container_client = blob_service_client.get_container_client(container_name)

# Upload a file (replace with your file path)
blob_name = "map.geojson"
file_path = r"C:\Users\vaqif\Desktop\hackathonazer\map.geojson"

with open(file_path, "rb") as data:
    container_client.upload_blob(name=blob_name, data=data)

print(f"Uploaded {blob_name} to {container_name}")
