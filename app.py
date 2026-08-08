from flask import Flask, request, render_template, jsonify, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
from datetime import datetime
import re
import os

app = Flask(__name__)
app.secret_key = "secret-key"

#this is the backend of the project and it routes the information to the database which is created if the db file isn't seen.

DB_NAME = 'skills.db'

# Database Helpers

def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cur = conn.cursor()

    # Users table
    cur.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE,
        phone TEXT UNIQUE,
        password TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
''')
    # Update existing database
    cur.execute("PRAGMA table_info(users)")
    columns = [column[1] for column in cur.fetchall()]

    if 'email' not in columns:
        cur.execute("ALTER TABLE users ADD COLUMN email TEXT")

    if 'password' not in columns:
        cur.execute("ALTER TABLE users ADD COLUMN password TEXT")

    cur.execute('''
        CREATE UNIQUE INDEX IF NOT EXISTS idx_users_email
        ON users(email)
    ''')

    # Skills table
    cur.execute('''
        CREATE TABLE IF NOT EXISTS skills (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            skill_name TEXT NOT NULL,
            skill_type TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, skill_name, skill_type),
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')

    # Job Applications table
    cur.execute('''
        CREATE TABLE IF NOT EXISTS job_applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            job_title TEXT NOT NULL,
            company TEXT NOT NULL,
            applied_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')

    # SMS Transactions table (for income proof)
    cur.execute('''
        CREATE TABLE IF NOT EXISTS sms_transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            original_sms TEXT NOT NULL,
            amount INTEGER,
            contact TEXT,
            transaction_date TEXT,
            direction TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')

    conn.commit()
    conn.close()
    print("✅ Database initialized successfully!")

# Initialize database
init_db()

#  Helper: Get or Create User

def get_or_create_user(name, phone):
    conn = get_db()
    cur = conn.cursor()
    
    if phone:
        cur.execute('SELECT * FROM users WHERE phone = ?', (phone,))
        row = cur.fetchone()
        if row:
            conn.close()
            return row['id']
    
    cur.execute('SELECT * FROM users WHERE name = ?', (name,))
    row = cur.fetchone()
    if row:
        conn.close()
        return row['id']
    
    cur.execute('INSERT INTO users (name, phone) VALUES (?, ?)', (name, phone))
    conn.commit()
    user_id = cur.lastrowid
    conn.close()
    return user_id

# Route 1: Home / Skill Swap

@app.route('/')
def home():
    conn = get_db()
    cur = conn.cursor()

    cur.execute('''
        SELECT skills.*, users.name, users.phone
        FROM skills
        JOIN users ON skills.user_id = users.id
        WHERE skill_type = 'offer'
        ORDER BY created_at DESC
    ''')
    offered = cur.fetchall()

    cur.execute('''
        SELECT skills.*, users.name, users.phone
        FROM skills
        JOIN users ON skills.user_id = users.id
        WHERE skill_type = 'want'
        ORDER BY created_at DESC
    ''')
    wanted = cur.fetchall()

    conn.close()
    return render_template('index.html', offered=offered, wanted=wanted)

@app.route('/add_skill', methods=['POST'])
def add_skill():
    user_name = request.form['user_name']
    user_phone = request.form.get('user_phone', '')
    skill_name = request.form['skill_name']
    skill_type = request.form['skill_type']

    user_id = get_or_create_user(user_name, user_phone)

    conn = get_db()
    cur = conn.cursor()

    try:
        cur.execute('''
            INSERT INTO skills (user_id, skill_name, skill_type)
            VALUES (?, ?, ?)
        ''', (user_id, skill_name, skill_type))
        conn.commit()
    except sqlite3.IntegrityError:
        pass

    conn.close()
    return redirect(url_for('home'))

#  Route 2: Jobs Dashboard + Macro Report 

@app.route('/dashboard')
def dashboard():
    conn = get_db()
    cur = conn.cursor()

    cur.execute('SELECT COUNT(*) AS c FROM job_applications')
    total_applications = cur.fetchone()['c']

    # Mock total jobs (Pasha will replace with real data)
    total_jobs = 150
    ratio = round(total_applications / total_jobs, 2) if total_jobs else 0

    # Get monthly applications for the chart
    cur.execute('''
        SELECT strftime('%Y-%m', applied_date) as month, COUNT(*) as count
        FROM job_applications
        GROUP BY month
        ORDER BY month DESC
        LIMIT 12
    ''')
    monthly_data = cur.fetchall()

    # Get recent applications
    cur.execute('''
        SELECT job_applications.*, users.name
        FROM job_applications
        JOIN users ON job_applications.user_id = users.id
        ORDER BY applied_date DESC
        LIMIT 10
    ''')
    recent_applications = cur.fetchall()

    conn.close()
    return render_template(
        'dashboard.html',
        applications=total_applications,
        jobs=total_jobs,
        ratio=ratio,
        monthly_data=monthly_data,
        recent=recent_applications
    )

@app.route('/apply_job', methods=['POST'])
def apply_job():
    user_name = request.form['user_name']
    user_phone = request.form.get('user_phone', '')
    job_title = request.form['job_title']
    company = request.form['company']

    user_id = get_or_create_user(user_name, user_phone)

    conn = get_db()
    cur = conn.cursor()
    cur.execute('''
        INSERT INTO job_applications (user_id, job_title, company)
        VALUES (?, ?, ?)
    ''', (user_id, job_title, company))
    conn.commit()
    conn.close()

    return redirect(url_for('dashboard'))

# Route 3: SMS Parser (Income Proof)

@app.route('/sms_parser')
def sms_parser():
    return render_template('sms_parser.html')

@app.route('/parse_sms', methods=['POST'])
def parse_sms():
    user_name = request.form['user_name']
    user_phone = request.form.get('user_phone', '')
    sms_text = request.form['sms_text']

    user_id = get_or_create_user(user_name, user_phone)

    amount_match = re.search(r'(\d+)\s*UGX', sms_text)
    amount = int(amount_match.group(1)) if amount_match else None

    date_match = re.search(r'(\d{4}-\d{2}-\d{2})', sms_text)
    tdate = date_match.group(1) if date_match else None

    name_match = re.search(r'(?:to|from)\s+([A-Za-z0-9_]+)', sms_text)
    contact = name_match.group(1) if name_match else None

    if 'sent' in sms_text.lower():
        direction = 'out'
    elif 'received' in sms_text.lower() or 'received' in sms_text.lower():
        direction = 'in'
    else:
        direction = None

    conn = get_db()
    cur = conn.cursor()
    if amount is not None:
        cur.execute('''
            INSERT INTO sms_transactions 
            (user_id, original_sms, amount, contact, transaction_date, direction)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, sms_text, amount, contact, tdate, direction))
        conn.commit()
    conn.close()

    result = {
        'original_sms': sms_text,
        'amount': amount if amount is not None else 'Not found',
        'date': tdate or 'Not found',
        'contact': contact or 'Not found',
        'direction': direction or 'Unknown'
    }

    return render_template('sms_result.html', result=result, user_name=user_name)

#  Route: User Profile / Identity
@app.route('/identity')
def identity():
    name = request.args.get('name')
    phone = request.args.get('phone')

    conn = get_db()
    cur = conn.cursor()

    if name:
        cur.execute('SELECT * FROM users WHERE name = ?', (name,))
    elif phone:
        cur.execute('SELECT * FROM users WHERE phone = ?', (phone,))
    else:
        return "Please provide ?name= or ?phone=", 400

    user = cur.fetchone()

    if not user:
        return "User not found", 404

    user_id = user['id']

    # Get skills
    cur.execute('SELECT * FROM skills WHERE user_id = ? ORDER BY created_at DESC', (user_id,))
    skills = cur.fetchall()

    # Get SMS transactions
    cur.execute('SELECT * FROM sms_transactions WHERE user_id = ? ORDER BY created_at DESC', (user_id,))
    sms_tx = cur.fetchall()

    # Get income summary
    cur.execute('SELECT COALESCE(SUM(amount), 0) AS total FROM sms_transactions WHERE user_id = ? AND direction = "in"', (user_id,))
    total_in = cur.fetchone()['total']
    cur.execute('SELECT COALESCE(SUM(amount), 0) AS total FROM sms_transactions WHERE user_id = ? AND direction = "out"', (user_id,))
    total_out = cur.fetchone()['total']

    # Get jobs
    cur.execute('SELECT * FROM job_applications WHERE user_id = ? ORDER BY applied_date DESC', (user_id,))
    jobs = cur.fetchall()

    conn.close()

    # Calculate trust score
    score = 0
    if total_in >= 100000:
        score += 40
    elif total_in >= 50000:
        score += 25
    else:
        score += 10

    if len(jobs) > 0:
        score += 10
    if len(skills) > 0:
        score += 20

    if score >= 70:
        band = "High"
    elif score >= 40:
        band = "Medium"
    else:
        band = "Low"

    return render_template(
        'identity.html',
        user=user,
        skills=skills,
        sms_tx=sms_tx,
        total_in=total_in,
        total_out=total_out,
        jobs=jobs,
        score=score,
        band=band
    )
    return render_template(

        'identity.html',

        user=user,

        skills=skills,

        sms_tx=sms_tx,

        total_in=total_in,

        total_out=total_out,

        jobs=jobs,

        score=score,

        band=band

    )
@app.route('/register', methods=['GET', 'POST'])
def register():

    if request.method == 'POST':

        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        phone = request.form.get('phone', '').strip()
        password = request.form.get('password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()

        if not name or not email or not password:
            flash('Please fill in all required fields.')
            return redirect(url_for('register'))

        if password != confirm_password:
            flash('Passwords do not match.')
            return redirect(url_for('register'))

        if len(password) < 6:
            flash('Password must be at least 6 characters.')
            return redirect(url_for('register'))

        conn = get_db()
        cur = conn.cursor()

        cur.execute(
            'SELECT id FROM users WHERE email = ?',
            (email,)
        )

        if cur.fetchone():
            conn.close()
            flash('An account with this email already exists.')
            return redirect(url_for('login'))

        hashed_password = generate_password_hash(password)

        cur.execute('''
            INSERT INTO users (name, email, phone, password)
            VALUES (?, ?, ?, ?)
        ''', (name, email, phone or None, hashed_password))

        conn.commit()
        conn.close()

        flash('Registration successful! Please log in.')
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':

        login_value = request.form.get('login', '').strip()
        password = request.form.get('password', '').strip()

        if not login_value or not password:
            flash('Please enter your email/phone and password.')
            return redirect(url_for('login'))

        conn = get_db()
        cur = conn.cursor()

        cur.execute('''
            SELECT * FROM users
            WHERE email = ? OR phone = ?
        ''', (login_value.lower(), login_value))

        user = cur.fetchone()
        conn.close()

        if not user:
            flash('Invalid email/phone or password.')
            return redirect(url_for('login'))

        if not user['password']:
            flash('This account does not have a password.')
            return redirect(url_for('login'))

        if not check_password_hash(user['password'], password):
            flash('Invalid email/phone or password.')
            return redirect(url_for('login'))

        session['user_id'] = user['id']
        session['user_name'] = user['name']
        session['user_email'] = user['email']

        flash('Login successful!')

        return redirect(url_for('dashboard'))

    return render_template('login.html')


@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():

    if request.method == 'POST':

        email = request.form.get('email', '').strip().lower()
        new_password = request.form.get('new_password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()

        if not email or not new_password or not confirm_password:
            flash('Please fill in all fields.')
            return redirect(url_for('forgot_password'))

        if new_password != confirm_password:
            flash('Passwords do not match.')
            return redirect(url_for('forgot_password'))

        if len(new_password) < 6:
            flash('Password must be at least 6 characters.')
            return redirect(url_for('forgot_password'))

        conn = get_db()
        cur = conn.cursor()

        cur.execute(
            'SELECT id FROM users WHERE email = ?',
            (email,)
        )

        user = cur.fetchone()

        if not user:
            conn.close()
            flash('No account was found with that email.')
            return redirect(url_for('forgot_password'))

        hashed_password = generate_password_hash(new_password)

        cur.execute('''
            UPDATE users
            SET password = ?
            WHERE email = ?
        ''', (hashed_password, email))

        conn.commit()
        conn.close()

        flash('Password reset successfully! Please log in.')
        return redirect(url_for('login'))

    return render_template('forgot_password.html')


@app.route('/logout')
def logout():

    session.clear()

    flash('You have been logged out.')
    return redirect(url_for('login'))


if __name__ == '__main__':

    debug_mode = os.environ.get(
        'FLASK_DEBUG',
        'True'
    ).lower() == 'true'

    port = int(
        os.environ.get('PORT', 5000)
    )

    app.run(
        debug=debug_mode,
        host='0.0.0.0',
        port=port
    )







