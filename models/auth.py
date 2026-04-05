"""
models/auth.py
--------------
Authentication helpers: password hashing, session management,
and the login_required decorator used to protect routes.
"""

import bcrypt
from functools import wraps
from flask import session, redirect, url_for, flash


# ── Password Utilities ────────────────────────────────────────

def hash_password(plain_text: str) -> str:
    """Hash a plain-text password using bcrypt."""
    return bcrypt.hashpw(plain_text.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def check_password(plain_text: str, hashed: str) -> bool:
    """Verify a plain-text password against its bcrypt hash."""
    return bcrypt.checkpw(plain_text.encode('utf-8'), hashed.encode('utf-8'))


# ── Session Helpers ───────────────────────────────────────────

def login_user(user: dict):
    """Store essential user info in the Flask session."""
    session.permanent = True
    session['user_id'] = str(user['id'])
    session['user_name'] = user['name']
    session['user_email'] = user['email']
    session['user_role'] = user['role']


def logout_user():
    """Clear the session."""
    session.clear()


def current_user() -> dict | None:
    """Return basic session info for the logged-in user, or None."""
    if 'user_id' not in session:
        return None
    return {
        'id': session['user_id'],
        'name': session['user_name'],
        'email': session['user_email'],
        'role': session['user_role'],
    }


# ── Route Decorators ──────────────────────────────────────────

def login_required(f):
    """Redirect unauthenticated users to /login."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access that page.', 'warning')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated


def donor_required(f):
    """Only allow donor-role users through."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in.', 'warning')
            return redirect(url_for('auth.login'))
        if session.get('user_role') != 'donor':
            flash('This section is for donors only.', 'danger')
            return redirect(url_for('main.dashboard'))
        return f(*args, **kwargs)
    return decorated


def ngo_required(f):
    """Only allow ngo-role users through."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in.', 'warning')
            return redirect(url_for('auth.login'))
        if session.get('user_role') != 'ngo':
            flash('This section is for NGOs only.', 'danger')
            return redirect(url_for('main.dashboard'))
        return f(*args, **kwargs)
    return decorated


def admin_required(f):
    """Only allow admin-role users through."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in.', 'warning')
            return redirect(url_for('auth.login'))
        if session.get('user_role') != 'admin':
            flash('Admin access required.', 'danger')
            return redirect(url_for('main.dashboard'))
        return f(*args, **kwargs)
    return decorated
