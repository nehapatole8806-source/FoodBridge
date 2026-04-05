"""
routes/auth.py
--------------
Handles user registration, login, and logout.
Validates input, checks credentials, and manages Flask sessions.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from config.database import query_db, insert_db
from models.auth import hash_password, check_password, login_user, logout_user

auth_bp = Blueprint('auth', __name__)


# ── Signup ────────────────────────────────────────────────────

@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    """Display signup form (GET) or create a new user (POST)."""
    if 'user_id' in session:
        return redirect(url_for('main.dashboard'))

    if request.method == 'POST':
        name  = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm  = request.form.get('confirm_password', '')
        role     = request.form.get('role', 'donor')
        org_name = request.form.get('organization_name', '').strip()
        phone    = request.form.get('phone', '').strip()
        city     = request.form.get('city', '').strip()
        state    = request.form.get('state', '').strip()

        # ── Validation ──
        errors = []
        if not name:
            errors.append('Name is required.')
        if not email or '@' not in email:
            errors.append('A valid email is required.')
        if len(password) < 6:
            errors.append('Password must be at least 6 characters.')
        if password != confirm:
            errors.append('Passwords do not match.')
        if role not in ('donor', 'ngo'):
            errors.append('Invalid role selected.')
        if role == 'ngo' and not org_name:
            errors.append('Organization name is required for NGOs.')

        if errors:
            for err in errors:
                flash(err, 'danger')
            return render_template('signup.html', form=request.form)

        # ── Check duplicate email ──
        existing = query_db('SELECT id FROM users WHERE email = %s', (email,), one=True)
        if existing:
            flash('An account with that email already exists.', 'danger')
            return render_template('signup.html', form=request.form)

        # ── Insert user ──
        try:
            user = insert_db(
                """INSERT INTO users
                   (name, email, password_hash, role, organization_name, phone, city, state)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                   RETURNING *""",
                (name, email, hash_password(password), role,
                 org_name or None, phone or None, city or None, state or None)
            )
            login_user(user)
            flash(f'Welcome, {name}! Your account has been created.', 'success')
            return redirect(url_for('main.dashboard'))
        except Exception as e:
            flash('Something went wrong. Please try again.', 'danger')
            return render_template('signup.html', form=request.form)

    return render_template('signup.html', form={})


# ── Login ─────────────────────────────────────────────────────

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Display login form (GET) or authenticate user (POST)."""
    if 'user_id' in session:
        return redirect(url_for('main.dashboard'))

    if request.method == 'POST':
        email    = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        if not email or not password:
            flash('Email and password are required.', 'danger')
            return render_template('login.html')

        user = query_db(
            'SELECT * FROM users WHERE email = %s AND is_active = TRUE',
            (email,), one=True
        )

        if not user or not check_password(password, user['password_hash']):
            flash('Invalid email or password.', 'danger')
            return render_template('login.html')

        login_user(user)
        flash(f'Welcome back, {user["name"]}!', 'success')
        return redirect(url_for('main.dashboard'))

    return render_template('login.html')


# ── Logout ────────────────────────────────────────────────────

@auth_bp.route('/logout')
def logout():
    """Clear the session and redirect to home."""
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.index'))
