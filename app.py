"""
app.py
------
Flask application factory.
Registers all blueprints, configures sessions, and sets up
the database teardown hook.
"""

import os
from datetime import timedelta
from flask import Flask, render_template
from dotenv import load_dotenv

# Load .env variables before anything else
load_dotenv()

from config.database import close_db
from routes import auth_bp, main_bp, donations_bp, requests_bp


def create_app():
    """Create and configure the Flask application."""
    app = Flask(__name__)

    # ── Secret Key & Session Config ──
    app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-change-me')
    app.permanent_session_lifetime = timedelta(
        days=int(os.environ.get('SESSION_LIFETIME_DAYS', 7))
    )

    # ── Register Blueprints ──
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(donations_bp)
    app.register_blueprint(requests_bp)

    # ── Database Teardown ──
    app.teardown_appcontext(close_db)

    # ── Custom Error Pages ──
    @app.errorhandler(404)
    def not_found(e):
        return render_template('error.html', code=404,
                               message='Page not found.'), 404

    @app.errorhandler(500)
    def server_error(e):
        return render_template('error.html', code=500,
                               message='Internal server error.'), 500

    # ── Template Globals ──
    # Makes current_user() available in all Jinja2 templates
    from models.auth import current_user
    @app.context_processor
    def inject_user():
        return dict(current_user=current_user())

    return app


# ── Run directly ──────────────────────────────────────────────
# if __name__ == '__main__':
#     app = create_app()
#     app.run(debug=os.environ.get('FLASK_DEBUG', 'True') == 'True', port=5000)

app = create_app()

# Vercel needs this 'app' variable to be available
if __name__ == '__main__':
    app.run(debug=True)
