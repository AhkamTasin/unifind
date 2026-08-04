# 🎓 UniFind — Campus Lost & Found Management System (in development)

**UniFind** is the short name of this web application, being built for
**CSE 338 (Web Technologies Sessional)** at Sylhet Engineering College.

> ⚠️ **Status: under active development.**
> This is the current build stage. Features are being added every day and pushed to
> this repository as they are completed.

## ✅ Currently implemented

| Module | Features |
| --- | --- |
| **Public pages** | Home page, How It Works, About |
| **User module** | Registration (Student / Teacher / University Staff / Admin) · secure login/logout · profile management · password change · in-app notifications (FR-01, 02, 03, 12) |
| **Reporting** | Users can report lost items (FR-04) and found items (FR-05) with details and photos · My Reports page |
| **Desk view** | Admin can **view** all lost and found reports (read-only) |

## 🔜 Coming next (in progress)

- Accept / reject / verification of reports & unique tracking IDs (FR-06, FR-07, FR-08)
- Ownership claims workflow (FR-10, 11, 13)
- Search & browsing with filters (FR-09)
- Admin panel: dashboard, claims review, user management, case resolution (FR-14–17)

---

## 🛠 Technology Stack (per proposal)

- **Frontend:** HTML5, CSS3, Bootstrap 5, JavaScript
- **Backend:** Django (Python)
- **Database:** MySQL *(SQLite is used by default so the project runs out of the box)*
- **Architecture:** Three-tier (Presentation / Application / Database)

---

## 🚀 Setup & Run

> Requires **Python 3.10+**.

### Fastest way — launcher scripts

- **Windows:** double-click `run.bat`
- **macOS / Linux:** run `./run.sh` in a terminal

### Manual way

```bash
# 1. Create a virtual environment (recommended)
python -m venv venv
# Windows:      venv\Scripts\activate
# macOS/Linux:  source venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Create the database tables
python manage.py migrate

# 4. Run the server
python manage.py runserver
```

Open **http://127.0.0.1:8000** in Chrome, Edge or Firefox.
Create an account from the **Register** page, then use the **Report** menu to
report a lost or found item (demo categories and accounts are loaded via
`python manage.py seed_data`). Log in as `admin` to open **Desk Reports**
(a read-only view of all reports).

---

## 📁 Project Structure

```
unifind/
├── manage.py
├── lostfound/           # Project configuration
├── core/                # Main application
│   ├── models.py        # Database schema (per proposal §3.4)
│   ├── forms.py         # Registration, login, profile forms
│   ├── views.py         # Public pages + user module views
│   └── urls.py
├── templates/           # Bootstrap 5 templates
│   ├── home.html, how_it_works.html, about.html
│   └── accounts/        # register, login, profile, notifications
└── static/              # CSS, JS, logo
```

---

## 🗄 Using MySQL (as specified in the proposal)

1. Create the database in MySQL:

   ```sql
   CREATE DATABASE campus_lost_found CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
   ```

2. Set environment variables (see `.env.example`):

   ```bash
   export DB_ENGINE=mysql DB_NAME=campus_lost_found DB_USER=root DB_PASSWORD=your_password
   ```

3. Install the MySQL driver and run:

   ```bash
   pip install -r requirements.txt
   python manage.py migrate
   python manage.py runserver
   ```
