"""
routes/main.py
--------------
Core pages: home, dashboard (role-aware), user profile, admin panel.
"""

from flask import Blueprint, render_template, redirect, url_for, session, flash, request
from config.database import query_db
from models.auth import login_required, admin_required

main_bp = Blueprint('main', __name__)


# ── Home Page ─────────────────────────────────────────────────

@main_bp.route('/')
def index():
    """Public landing page with stats and recent donations."""
    stats = query_db("""
        SELECT
            (SELECT COUNT(*) FROM users WHERE role='donor')    AS total_donors,
            (SELECT COUNT(*) FROM users WHERE role='ngo')      AS total_ngos,
            (SELECT COUNT(*) FROM donations)                   AS total_donations,
            (SELECT COUNT(*) FROM donations WHERE status='claimed') AS claimed_donations
    """, one=True)

    recent = query_db("""
        SELECT d.id, d.title, d.food_type, d.quantity, d.quantity_unit,
               d.city, d.expiry_time, d.status, u.name AS donor_name
        FROM donations d JOIN users u ON u.id=d.donor_id
        WHERE d.status='available'
        ORDER BY d.created_at DESC LIMIT 6
    """)

    return render_template('index.html', stats=stats, recent_donations=recent)


# ── Dashboard (role-based) ────────────────────────────────────

@main_bp.route('/dashboard')
@login_required
def dashboard():
    """
    Show the appropriate dashboard based on user role:
    - donor → their listings and incoming requests
    - ngo   → their submitted requests
    - admin → all users and donations overview
    """
    role = session.get('user_role')
    uid  = session.get('user_id')

    if role == 'donor':
        # Donor's donations
        donations = query_db(
            "SELECT * FROM donations WHERE donor_id=%s ORDER BY created_at DESC",
            (uid,)
        )
        # Incoming requests on their donations
        incoming_requests = query_db(
            """SELECT r.*, d.title AS donation_title, u.name AS ngo_name,
                      u.organization_name, u.phone AS ngo_phone, u.email AS ngo_email
               FROM requests r
               JOIN donations d ON d.id = r.donation_id
               JOIN users u ON u.id = r.ngo_id
               WHERE d.donor_id = %s
               ORDER BY r.created_at DESC""",
            (uid,)
        )
        return render_template('dashboard_donor.html',
                               donations=donations,
                               incoming_requests=incoming_requests)

    elif role == 'ngo':
        # NGO's submitted requests
        my_requests = query_db(
            """SELECT r.*, d.title AS donation_title, d.location, d.city,
                      d.quantity, d.quantity_unit, d.expiry_time, d.food_type,
                      u.name AS donor_name, u.phone AS donor_phone
               FROM requests r
               JOIN donations d ON d.id = r.donation_id
               JOIN users u ON u.id = d.donor_id
               WHERE r.ngo_id = %s
               ORDER BY r.created_at DESC""",
            (uid,)
        )
        return render_template('dashboard_ngo.html', my_requests=my_requests)

    elif role == 'admin':
        # Admin overview
        users = query_db("SELECT * FROM users ORDER BY created_at DESC")
        donations = query_db(
            """SELECT d.*, u.name AS donor_name
               FROM donations d JOIN users u ON u.id=d.donor_id
               ORDER BY d.created_at DESC"""
        )
        all_requests = query_db(
            """SELECT r.*, d.title AS donation_title,
                      ngo.name AS ngo_name, donor.name AS donor_name
               FROM requests r
               JOIN donations d ON d.id = r.donation_id
               JOIN users ngo ON ngo.id = r.ngo_id
               JOIN users donor ON donor.id = d.donor_id
               ORDER BY r.created_at DESC"""
        )
        return render_template('dashboard_admin.html',
                               users=users,
                               donations=donations,
                               all_requests=all_requests)

    return redirect(url_for('main.index'))


# ── User Profile ──────────────────────────────────────────────

@main_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """View and update the current user's profile."""
    uid = session['user_id']

    if request.method == 'POST':
        name    = request.form.get('name', '').strip()
        phone   = request.form.get('phone', '').strip()
        city    = request.form.get('city', '').strip()
        state   = request.form.get('state', '').strip()
        address = request.form.get('address', '').strip()
        org     = request.form.get('organization_name', '').strip()

        query_db(
            """UPDATE users SET name=%s, phone=%s, city=%s, state=%s,
               address=%s, organization_name=%s WHERE id=%s""",
            (name, phone or None, city or None, state or None,
             address or None, org or None, uid),
            commit=True
        )
        session['user_name'] = name
        flash('Profile updated successfully.', 'success')
        return redirect(url_for('main.profile'))

    user = query_db('SELECT * FROM users WHERE id=%s', (uid,), one=True)
    return render_template('profile.html', user=user)


# ── Admin: Toggle User Active Status ──────────────────────────

@main_bp.route('/admin/users/<uuid:user_id>/toggle', methods=['POST'])
@admin_required
def admin_toggle_user(user_id):
    """Admin: activate or deactivate a user account."""
    query_db(
        "UPDATE users SET is_active = NOT is_active WHERE id=%s",
        (str(user_id),), commit=True
    )
    flash('User status updated.', 'info')
    return redirect(url_for('main.dashboard'))


# ── Admin: Delete a Donation ──────────────────────────────────

@main_bp.route('/admin/donations/<uuid:donation_id>/delete', methods=['POST'])
@admin_required
def admin_delete_donation(donation_id):
    """Admin: permanently remove a donation."""
    query_db('DELETE FROM donations WHERE id=%s', (str(donation_id),), commit=True)
    flash('Donation deleted.', 'info')
    return redirect(url_for('main.dashboard'))
