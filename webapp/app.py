from flask import Flask, request, render_template, Response, jsonify, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import subprocess
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_very_secret_key_here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

def create_tables():
    db.create_all()

@app.route('/')
def index():
    if 'logged_in' not in session:
        flash('Please log in to view this page', 'info')
        return redirect(url_for('login'))
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            session['logged_in'] = True
            session['username'] = username
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password', 'error')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    session.pop('username', None)
    flash('Successfully logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        existing_user = User.query.filter_by(username=username).first()
        if existing_user is not None:
            flash('Username already taken', 'error')
            return redirect(url_for('register'))
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        new_user = User(username=username, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        flash('Registration successful, please login.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

def stream_process_output(command):
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    def generate():
        try:
            stdout_lines = []
            for stdout_line in iter(process.stdout.readline, ""):
                stdout_lines.append(stdout_line)
                yield f"data: {stdout_line}\n\n"
            process.stdout.close()
            
            stderr_output = []
            for stderr_line in iter(process.stderr.readline, ""):
                stderr_output.append(stderr_line)
                yield f"data: {stderr_line}\n\n"
            process.stderr.close()
            
            return_code = process.wait()
            if return_code != 0:
                if any("target found" in line.lower() for line in stdout_lines):  # Adjust this condition based on known success indicators
                    yield "data: Command executed successfully.\n\n"
                else:
                    yield f"data: Command failed with return code {return_code}\n\n"
                    yield f"data: {''.join(stderr_output)}\n\n"
            else:
                yield f"data: Command executed successfully.\n\n"
        except Exception as e:
            yield f"data: {str(e)}\n\n"
    return Response(generate(), mimetype='text/event-stream')

@app.route('/run-mfoc', methods=['GET'])
def run_mfoc():
    if 'logged_in' not in session:
        return redirect(url_for('login'))
    output_filename = request.args.get('output_filename')
    if not output_filename:
        return "Filename not provided", 400
    command = f"mfoc -O ./saved_cards/{output_filename}.dmp"
    return stream_process_output(command)

@app.route('/write-card', methods=['POST'])
def write_card():
    if 'logged_in' not in session:
        return redirect(url_for('login'))
    
    source_file = request.form['source_file']
    target_file = request.form['target_file']
    
    source_path = os.path.join('./saved_cards', source_file)
    target_path = os.path.join('./saved_cards', target_file)
    
    # Check if source and target files exist
    if not os.path.exists(source_path):
        return f"Source file {source_file} does not exist.", 400
    if not os.path.exists(target_path):
        return f"Target file {target_file} does not exist.", 400
    
    command = f"/usr/bin/nfc-mfclassic w A {source_path} {target_path}"
    return stream_process_output(command)


@app.route('/scan-nfc', methods=['GET'])
def scan_nfc():
    if 'logged_in' not in session:
        return redirect(url_for('login'))
    command = "nfc-list"
    return stream_process_output(command)

@app.route('/list-dmp-files')
def list_dmp_files():
    if 'logged_in' not in session:
        return redirect(url_for('login'))
    path = './saved_cards'
    if not os.path.exists(path):
        os.makedirs(path)
    files = [f for f in os.listdir(path) if f.endswith('.dmp')]
    return jsonify(files)

if __name__ == '__main__':
    with app.app_context():
        create_tables()
    app.run(host='0.0.0.0', debug=True)
