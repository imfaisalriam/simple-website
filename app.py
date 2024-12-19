from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_socketio import SocketIO, send
from datetime import datetime, timedelta
 from werkzeug.urls import url_quote
from urllib.parse import quote as url_quote
import os

# Initialize app and configure database
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'your_default_secret_key')  # Secure production secret key
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'postgresql://localhost/website')  # Use PostgreSQL URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
bcrypt = Bcrypt(app)
db = SQLAlchemy(app)
socketio = SocketIO(app)

# Database models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    author = db.Column(db.String(80), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class ChatMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False)
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Routes
@app.route('/')
def index():
    if 'username' in session:
        posts = Post.query.order_by(Post.created_at.desc()).all()
        return render_template('home.html', username=session['username'], posts=posts)
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = bcrypt.generate_password_hash(request.form['password']).decode('utf-8')
        if User.query.filter_by(username=username).first():
            return 'Username already exists!'
        new_user = User(username=username, password=password)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and bcrypt.check_password_hash(user.password, password):
            session['username'] = username
            return redirect(url_for('index'))
        return 'Invalid credentials!'
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/post', methods=['POST'])
def post():
    if 'username' in session:
        content = request.form['content']
        new_post = Post(content=content, author=session['username'])
        db.session.add(new_post)
        db.session.commit()
        return redirect(url_for('index'))
    return redirect(url_for('login'))

@socketio.on('message')
def handle_message(msg):
    if 'username' in session:
        username = session['username']
        new_message = ChatMessage(username=username, message=msg)
        db.session.add(new_message)
        db.session.commit()
        send({'username': username, 'message': msg, 'time': datetime.now().strftime('%H:%M')}, broadcast=True)

# Helper function to delete old posts and messages
def cleanup():
    cutoff = datetime.utcnow() - timedelta(days=2)
    Post.query.filter(Post.created_at < cutoff).delete()
    ChatMessage.query.filter(ChatMessage.created_at < cutoff).delete()
    db.session.commit()

# Run cleanup before each request
@app.before_request
def before_request():
    cleanup()

if __name__ == '__main__':
    if not os.path.exists('website.db'):
        db.create_all()
    socketio.run(app, debug=True)
