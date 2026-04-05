# 🌾 FoodBridge — Food Donation Platform

A full-stack web application connecting food donors with NGOs to reduce waste and fight hunger.

**Stack:** Python · Flask · PostgreSQL (Supabase) · HTML · CSS · JavaScript

---

## 📁 Project Structure

```
food_donation/
├── app.py                    # Flask app factory & entry point
├── requirements.txt          # Python dependencies
├── schema.sql                # PostgreSQL database schema
├── .env.example              # Environment variables template
│
├── config/
│   ├── __init__.py
│   └── database.py           # DB connection helpers (psycopg2)
│
├── models/
│   ├── __init__.py
│   └── auth.py               # Password hashing, session helpers, decorators
│
├── routes/
│   ├── __init__.py
│   ├── auth.py               # Signup / Login / Logout
│   ├── main.py               # Home, Dashboard, Profile, Admin
│   ├── donations.py          # Donation CRUD + browse + API
│   └── requests.py           # NGO claim/request flow
│
├── templates/                # Jinja2 HTML templates
│   ├── base.html             # Master layout (nav, flash, footer)
│   ├── index.html            # Home / landing page
│   ├── login.html
│   ├── signup.html
│   ├── browse.html           # Browse donations with filters
│   ├── donation_detail.html  # Single donation + claim form
│   ├── create_donation.html  # Create / edit donation form
│   ├── dashboard_donor.html
│   ├── dashboard_ngo.html
│   ├── dashboard_admin.html
│   ├── profile.html
│   └── error.html
│
└── static/
    ├── css/style.css         # Full design system
    └── js/main.js            # Client-side interactivity
```

---

## 🗄️ Database Schema

Three core tables in PostgreSQL:

| Table       | Purpose                                          |
|-------------|--------------------------------------------------|
| `users`     | All accounts (donor / ngo / admin roles)         |
| `donations` | Food listings posted by donors                   |
| `requests`  | NGO claims on available donations                |

See `schema.sql` for full definitions with indexes and triggers.

---

## ⚡ Quick Setup

### 1. Clone / extract the project

```bash
cd food_donation
```

### 2. Create a virtual environment

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Set up Supabase PostgreSQL

1. Go to [supabase.com](https://supabase.com) and create a free account
2. Click **"New Project"** → give it a name (e.g. `foodbridge`)
3. Set a strong database password — **save it!**
4. Once created, go to **Settings → Database**
5. Copy the **Connection string** (URI format):
   ```
   postgresql://postgres:[YOUR-PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres
   ```

6. In Supabase, go to **SQL Editor** and paste the entire contents of `schema.sql`, then click **Run**

### 4. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env`:

```env
SECRET_KEY=your-random-secret-key-here
DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@db.YOUR_PROJECT_REF.supabase.co:5432/postgres
FLASK_ENV=development
FLASK_DEBUG=True
```

Generate a secure secret key:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

### 5. Run the application

```bash
python app.py
```

Open [http://localhost:5000](http://localhost:5000)

---

## 👤 User Roles

| Role    | Can do                                                              |
|---------|---------------------------------------------------------------------|
| Donor   | Post donations, manage listings, approve/reject NGO requests        |
| NGO     | Browse donations, submit pickup requests, mark pickups complete     |
| Admin   | View all users/donations/requests, activate/deactivate users, delete donations |

**Default admin account** (created by schema.sql seed):
- Email: `admin@foodbridge.com`
- Password: `admin123`
- ⚠️ Change this immediately in production!

---

## 🔗 Key Routes

| Method | URL                              | Description                    |
|--------|----------------------------------|--------------------------------|
| GET    | `/`                              | Home page                      |
| GET    | `/signup`                        | Registration form              |
| POST   | `/signup`                        | Create account                 |
| GET    | `/login`                         | Login form                     |
| POST   | `/login`                         | Authenticate                   |
| GET    | `/logout`                        | End session                    |
| GET    | `/dashboard`                     | Role-based dashboard           |
| GET    | `/donations`                     | Browse donations (filterable)  |
| GET    | `/donations/<id>`                | Donation detail + claim form   |
| GET    | `/donations/create`              | Post new donation (donors)     |
| POST   | `/donations/create`              | Save new donation              |
| GET    | `/donations/<id>/edit`           | Edit donation (owner only)     |
| POST   | `/donations/<id>/cancel`         | Cancel donation                |
| POST   | `/donations/<id>/request`        | NGO submits claim              |
| POST   | `/requests/<id>/approve`         | Donor approves claim           |
| POST   | `/requests/<id>/reject`          | Donor rejects claim            |
| POST   | `/requests/<id>/complete`        | NGO marks pickup done          |
| GET    | `/profile`                       | View/edit profile              |
| GET    | `/api/donations`                 | JSON API for filtering         |

---

## 🎨 Design Highlights

- **Warm organic aesthetic** — earthy greens, amber, cream tones
- **Playfair Display** headings + **DM Sans** body text
- Fully responsive — mobile, tablet, desktop
- Animated hero with floating cards
- Role-aware dashboards with stats
- Sticky sidebar navigation

---

## 🔐 Security Notes

- Passwords hashed with **bcrypt** (cost factor 12)
- Session-based authentication with `flask.session`
- Route-level decorators enforce role access
- SQL queries use **parameterised statements** (no SQL injection)
- Input validation on all forms (server-side)

---

## 🚀 Production Checklist

- [ ] Set `FLASK_ENV=production`, `FLASK_DEBUG=False`
- [ ] Use a strong, random `SECRET_KEY`
- [ ] Enable SSL on your hosting (Supabase uses SSL by default)
- [ ] Add `gunicorn` or `uWSGI` as WSGI server
- [ ] Add `sslmode=require` to `DATABASE_URL`
- [ ] Change default admin password
- [ ] Set up a scheduled job to auto-expire donations

---

## 📦 Dependencies

| Package             | Purpose                        |
|---------------------|--------------------------------|
| `Flask`             | Web framework                  |
| `psycopg2-binary`   | PostgreSQL adapter             |
| `python-dotenv`     | Load `.env` variables          |
| `bcrypt`            | Password hashing               |
| `PyJWT`             | (Available for JWT auth if needed) |
| `Werkzeug`          | Flask dependency / utilities   |
