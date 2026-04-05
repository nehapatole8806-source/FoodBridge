"""
routes/donations.py
-------------------
CRUD operations for food donation listings.
Donors can create, update, and cancel their donations.
NGOs and everyone can browse available donations.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from config.database import query_db, insert_db
from models.auth import login_required, donor_required

donations_bp = Blueprint('donations', __name__)


# ── Browse All Available Donations (public) ───────────────────

@donations_bp.route('/donations')
def browse():
    """Show all available donations with optional city filter."""
    # Auto-expire past-due donations first
    query_db(
        "UPDATE donations SET status='expired' WHERE expiry_time < NOW() AND status='available'",
        commit=True
    )

    city   = request.args.get('city', '').strip()
    ftype  = request.args.get('food_type', '').strip()
    search = request.args.get('q', '').strip()

    base_sql = """
        SELECT d.*, u.name AS donor_name, u.phone AS donor_phone
        FROM donations d
        JOIN users u ON u.id = d.donor_id
        WHERE d.status = 'available'
    """
    params = []

    if city:
        base_sql += " AND LOWER(d.city) LIKE %s"
        params.append(f'%{city.lower()}%')
    if ftype:
        base_sql += " AND d.food_type = %s"
        params.append(ftype)
    if search:
        base_sql += " AND (LOWER(d.title) LIKE %s OR LOWER(d.description) LIKE %s)"
        params.extend([f'%{search.lower()}%', f'%{search.lower()}%'])

    base_sql += " ORDER BY d.created_at DESC"

    donations = query_db(base_sql, params)

    # Fetch cities for filter dropdown
    cities = query_db(
        "SELECT DISTINCT city FROM donations WHERE status='available' AND city IS NOT NULL ORDER BY city"
    )

    return render_template('browse.html',
                           donations=donations,
                           cities=[c['city'] for c in cities],
                           filters={'city': city, 'food_type': ftype, 'q': search})


# ── Single Donation Detail ────────────────────────────────────

@donations_bp.route('/donations/<uuid:donation_id>')
def detail(donation_id):
    """Show full detail for a single donation."""
    donation = query_db(
        """SELECT d.*, u.name AS donor_name, u.phone AS donor_phone,
                  u.email AS donor_email, u.city AS donor_city
           FROM donations d
           JOIN users u ON u.id = d.donor_id
           WHERE d.id = %s""",
        (str(donation_id),), one=True
    )
    if not donation:
        flash('Donation not found.', 'danger')
        return redirect(url_for('donations.browse'))

    # Has the current NGO already requested this?
    already_requested = False
    if session.get('user_role') == 'ngo':
        req = query_db(
            'SELECT id FROM requests WHERE donation_id=%s AND ngo_id=%s',
            (str(donation_id), session['user_id']), one=True
        )
        already_requested = req is not None

    return render_template('donation_detail.html',
                           donation=donation,
                           already_requested=already_requested)


# ── Create Donation (Donors only) ─────────────────────────────

@donations_bp.route('/donations/create', methods=['GET', 'POST'])
@donor_required
def create():
    """Allow donors to post a new food donation."""
    if request.method == 'POST':
        title       = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        food_type   = request.form.get('food_type', '')
        quantity    = request.form.get('quantity', '0')
        unit        = request.form.get('quantity_unit', 'servings')
        location    = request.form.get('location', '').strip()
        city        = request.form.get('city', '').strip()
        state       = request.form.get('state', '').strip()
        expiry      = request.form.get('expiry_time', '')
        allergens   = request.form.get('allergens', '').strip()
        pickup_info = request.form.get('pickup_instructions', '').strip()

        # ── Validation ──
        errors = []
        if not title:         errors.append('Title is required.')
        if not food_type:     errors.append('Food type is required.')
        if not location:      errors.append('Location is required.')
        if not expiry:        errors.append('Expiry date/time is required.')
        try:
            qty = int(quantity)
            if qty <= 0:
                errors.append('Quantity must be a positive number.')
        except ValueError:
            errors.append('Quantity must be a number.')
            qty = 0

        if errors:
            for e in errors:
                flash(e, 'danger')
            return render_template('create_donation.html', form=request.form)

        try:
            insert_db(
                """INSERT INTO donations
                   (donor_id, title, description, food_type, quantity, quantity_unit,
                    location, city, state, expiry_time, allergens, pickup_instructions)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                   RETURNING id""",
                (session['user_id'], title, description or None, food_type, qty, unit,
                 location, city or None, state or None, expiry,
                 allergens or None, pickup_info or None)
            )
            flash('Donation posted successfully! 🎉', 'success')
            return redirect(url_for('main.dashboard'))
        except Exception as e:
            flash('Error saving donation. Please try again.', 'danger')
            return render_template('create_donation.html', form=request.form)

    return render_template('create_donation.html', form={})


# ── Edit Donation ─────────────────────────────────────────────

@donations_bp.route('/donations/<uuid:donation_id>/edit', methods=['GET', 'POST'])
@donor_required
def edit(donation_id):
    """Allow the owning donor to edit an available donation."""
    donation = query_db(
        'SELECT * FROM donations WHERE id=%s AND donor_id=%s',
        (str(donation_id), session['user_id']), one=True
    )
    if not donation:
        flash('Donation not found or access denied.', 'danger')
        return redirect(url_for('main.dashboard'))

    if donation['status'] != 'available':
        flash('Only available donations can be edited.', 'warning')
        return redirect(url_for('main.dashboard'))

    if request.method == 'POST':
        title       = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        food_type   = request.form.get('food_type', '')
        quantity    = request.form.get('quantity', '0')
        unit        = request.form.get('quantity_unit', 'servings')
        location    = request.form.get('location', '').strip()
        city        = request.form.get('city', '').strip()
        state       = request.form.get('state', '').strip()
        expiry      = request.form.get('expiry_time', '')
        allergens   = request.form.get('allergens', '').strip()
        pickup_info = request.form.get('pickup_instructions', '').strip()

        try:
            qty = int(quantity)
        except ValueError:
            qty = 0

        query_db(
            """UPDATE donations SET title=%s, description=%s, food_type=%s, quantity=%s,
               quantity_unit=%s, location=%s, city=%s, state=%s, expiry_time=%s,
               allergens=%s, pickup_instructions=%s
               WHERE id=%s AND donor_id=%s""",
            (title, description or None, food_type, qty, unit, location, city or None,
             state or None, expiry, allergens or None, pickup_info or None,
             str(donation_id), session['user_id']),
            commit=True
        )
        flash('Donation updated successfully.', 'success')
        return redirect(url_for('main.dashboard'))

    return render_template('create_donation.html', form=donation, editing=True)


# ── Cancel Donation ───────────────────────────────────────────

@donations_bp.route('/donations/<uuid:donation_id>/cancel', methods=['POST'])
@donor_required
def cancel(donation_id):
    """Allow a donor to cancel their donation."""
    query_db(
        "UPDATE donations SET status='cancelled' WHERE id=%s AND donor_id=%s AND status='available'",
        (str(donation_id), session['user_id']),
        commit=True
    )
    flash('Donation cancelled.', 'info')
    return redirect(url_for('main.dashboard'))


# ── API: Donations JSON (for filtering without page reload) ───

@donations_bp.route('/api/donations')
def api_list():
    """JSON endpoint for dynamic filtering on the browse page."""
    city  = request.args.get('city', '')
    ftype = request.args.get('food_type', '')

    sql = """SELECT d.id, d.title, d.food_type, d.quantity, d.quantity_unit,
                    d.location, d.city, d.expiry_time, d.status,
                    u.name AS donor_name
             FROM donations d JOIN users u ON u.id=d.donor_id
             WHERE d.status='available'"""
    params = []
    if city:
        sql += " AND LOWER(d.city) LIKE %s"
        params.append(f'%{city.lower()}%')
    if ftype:
        sql += " AND d.food_type=%s"
        params.append(ftype)
    sql += " ORDER BY d.created_at DESC LIMIT 50"

    rows = query_db(sql, params)
    # Convert to JSON-serialisable format
    result = []
    for r in rows:
        row = dict(r)
        if row.get('expiry_time'):
            row['expiry_time'] = row['expiry_time'].isoformat()
        result.append(row)
    return jsonify(result)
