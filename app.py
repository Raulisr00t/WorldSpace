from flask import Flask, request, render_template, redirect, session, url_for
from flask_sqlalchemy import SQLAlchemy
import bcrypt
import re
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db = SQLAlchemy(app)
app.secret_key = 'secret_key'

# Gmail SMTP server configuration
SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 587
SMTP_USERNAME = 'yashmaisr00t@gmail.com'
SMTP_PASSWORD = 'omggdilmuvbludpv'

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)

    def __init__(self, name, email, password):
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
    wrap.__name__ = f.__name__
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
def send_email():
    if request.method == 'POST':
        recipient = request.form['recipient']
        subject = request.form['subject']
        message = request.form['message']
        image_file = request.files.get('image')

        if image_file:
            image_content = image_file.read()  # Read image file content
        else:
            image_content = None

        msg = MIMEMultipart()
        msg['From'] = SMTP_USERNAME
        msg['To'] = recipient
        msg['Subject'] = subject

        msg.attach(MIMEText(message, 'plain'))

        # Attach image if provided
        if image_content:
            img = MIMEImage(image_content, name=os.path.basename(image_file.filename))
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
    <style>
        body {
            margin: 0;
            height: 100vh;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            background-image: url('https://i.ibb.co/Dk9BFGx/yashmaisr00tby4.png');
            background-size: cover;
            background-position: center;
            color: white; /* Change text color for better contrast */
            font-family: Arial, sans-serif; /* Use a clean font */
        }
        h1 {
            font-size: 3em;
            margin-bottom: 20px; /* Add space below the header */
            text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.5); /* Add text shadow for visibility */
        }
        p {
            font-size: 1.5em;
            margin-bottom: 30px; /* Add space below the paragraph */
            text-shadow: 1px 1px 3px rgba(0, 0, 0, 0.5); /* Add text shadow for visibility */
        }
        a {
            text-decoration: none; /* Remove underline */
            background-color: rgba(0, 0, 0, 0.7); /* Semi-transparent background */
            color: white; /* Text color */
            padding: 15px 30px; /* Padding for button */
            border-radius: 5px; /* Rounded corners */
            transition: background-color 0.3s; /* Smooth transition for hover effect */
        }
        a:hover {
            background-color: rgba(0, 0, 0, 0.9); /* Darken on hover */
        }
    </style>
</head>
<body>
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
            background-image: url('https://papers.co/wallpaper/papers.co-ak71-alien-green-earth-space-planet-dark-35-3840x2160-4k-wallpaper.jpg');
            background-size: cover;
            background-position: center;
            background-repeat: no-repeat;
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
            <textarea id="message" name="message" rows="4" required></textarea>
        </div>
        <div class="form-group">
            <label for="image">Attach Image:</label>
            <input type="file" id="image" name="image" accept="image/*">
        </div>
        <button type="submit" class="btn btn-primary">Send Email</button>
    </form>
    <br>
</div>
</body>
</html>
    '''

if __name__ == '__main__':
    app.run(debug=True, port=5001)
