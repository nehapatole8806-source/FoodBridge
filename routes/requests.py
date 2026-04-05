"""
routes/requests.py
------------------
NGOs can request (claim) available donations.
Donors can approve or reject claims.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from config.database import query_db, insert_db
from models.auth import login_required, ngo_required, donor_required

requests_bp = Blueprint('requests', __name__)


# ── NGO: Submit a Request ─────────────────────────────────────

@requests_bp.route('/donations/<uuid:donation_id>/request', methods=['POST'])
@ngo_required
def create_request(donation_id):
    """NGO claims an available donation."""
    # Verify donation is still available
    donation = query_db(
        "SELECT * FROM donations WHERE id=%s AND status='available'",
        (str(donation_id),), one=True
    )
    if not donation:
        flash('This donation is no longer available.', 'warning')
        return redirect(url_for('donations.browse'))

    # Prevent self-request (shouldn't happen since NGOs can't donate, but just in case)
    if str(donation['donor_id']) == session['user_id']:
        flash('You cannot request your own donation.', 'danger')
        return redirect(url_for('donations.browse'))

    # Check for duplicate request
    existing = query_db(
        'SELECT id FROM requests WHERE donation_id=%s AND ngo_id=%s',
        (str(donation_id), session['user_id']), one=True
    )
    if existing:
        flash('You have already requested this donation.', 'warning')
        return redirect(url_for('donations.detail', donation_id=donation_id))

    message     = request.form.get('message', '').strip()
    pickup_time = request.form.get('pickup_time', '').strip() or None

    try:
        insert_db(
            """INSERT INTO requests (donation_id, ngo_id, message, pickup_time)
               VALUES (%s, %s, %s, %s) RETURNING id""",
            (str(donation_id), session['user_id'], message or None, pickup_time)
        )
        flash('Request submitted successfully! The donor will be notified.', 'success')
    except Exception:
        flash('Failed to submit request. Please try again.', 'danger')

    return redirect(url_for('donations.detail', donation_id=donation_id))


# ── Donor: Approve a Request ──────────────────────────────────

@requests_bp.route('/requests/<uuid:request_id>/approve', methods=['POST'])
@donor_required
def approve(request_id):
    """Donor approves an NGO's request and marks donation as claimed."""
    req = query_db(
        """SELECT r.*, d.donor_id FROM requests r
           JOIN donations d ON d.id = r.donation_id
           WHERE r.id = %s""",
        (str(request_id),), one=True
    )
    if not req or str(req['donor_id']) != session['user_id']:
        flash('Request not found or access denied.', 'danger')
        return redirect(url_for('main.dashboard'))

    # Approve this request
    query_db(
        "UPDATE requests SET status='approved' WHERE id=%s",
        (str(request_id),), commit=True
    )
    # Mark donation as claimed
    query_db(
        "UPDATE donations SET status='claimed' WHERE id=%s",
        (str(req['donation_id']),), commit=True
    )
    # Reject all other pending requests for the same donation
    query_db(
        "UPDATE requests SET status='rejected' WHERE donation_id=%s AND id != %s AND status='pending'",
        (str(req['donation_id']), str(request_id)), commit=True
    )

    flash('Request approved! The NGO has been notified.', 'success')
    return redirect(url_for('main.dashboard'))


# ── Donor: Reject a Request ───────────────────────────────────

@requests_bp.route('/requests/<uuid:request_id>/reject', methods=['POST'])
@donor_required
def reject(request_id):
    """Donor rejects an NGO's request."""
    req = query_db(
        """SELECT r.*, d.donor_id FROM requests r
           JOIN donations d ON d.id = r.donation_id
           WHERE r.id = %s""",
        (str(request_id),), one=True
    )
    if not req or str(req['donor_id']) != session['user_id']:
        flash('Request not found or access denied.', 'danger')
        return redirect(url_for('main.dashboard'))

    query_db(
        "UPDATE requests SET status='rejected' WHERE id=%s",
        (str(request_id),), commit=True
    )
    flash('Request rejected.', 'info')
    return redirect(url_for('main.dashboard'))


# ── NGO: Mark pickup as completed ────────────────────────────

@requests_bp.route('/requests/<uuid:request_id>/complete', methods=['POST'])
@ngo_required
def complete(request_id):
    """NGO marks a pickup as completed."""
    req = query_db(
        "SELECT * FROM requests WHERE id=%s AND ngo_id=%s AND status='approved'",
        (str(request_id), session['user_id']), one=True
    )
    if not req:
        flash('Request not found or cannot be completed.', 'danger')
        return redirect(url_for('main.dashboard'))

    query_db(
        "UPDATE requests SET status='completed' WHERE id=%s",
        (str(request_id),), commit=True
    )
    flash('Pickup marked as completed. Thank you! 🙏', 'success')
    return redirect(url_for('main.dashboard'))
