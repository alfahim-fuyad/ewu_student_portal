# University Student Portal — Django + AI Assistant

A full-stack Django student portal inspired by East West University (EWU) style academic portals — with role-based access for **Admin / Teacher / Student**, a **floating AI Assistant** on every authenticated page, **Neon PostgreSQL** support, and **Render.com** deployment.

> ✨ The AI Assistant is **permission-aware**: students can only query their own attendance / CGPA / fees / courses. Asking about another student's data is hard-denied at the Django layer before any AI call is made.

---

## 🎯 Features

| Module | Admin | Teacher | Student |
|---|---|---|---|
| Dashboard | ✅ Stats | ✅ Assigned courses | ✅ CGPA / attendance / fees snapshot |
| Students | ✅ CRUD | ✅ Read | ✅ Own profile |
| Teachers | ✅ CRUD | ✅ Read | ✅ Read |
| Departments | ✅ CRUD | ✅ Read | ✅ Read |
| Courses | ✅ CRUD | ✅ Read | ✅ Read |
| Semesters | ✅ CRUD | ✅ Read | ✅ Read |
| Enrollment | ✅ Manage | — | ✅ View own |
| Attendance | ✅ All | ✅ Take & report | ✅ View own |
| Results | ✅ All | ✅ Manage own courses | ✅ View own + transcript |
| Fees | ✅ CRUD + payments | — | ✅ View own + history |
| Notices | ✅ CRUD | ✅ Post (own) | ✅ View visible |
| AI Assistant | ✅ | ✅ | ✅ (permission-filtered) |

---

## 📁 Project Structure

```
student_portal/
├── manage.py
├── requirements.txt
├── .env.example
├── Procfile
├── render.yaml
├── build.sh
├── config/                    # Django project settings
├── accounts/                  # Auth + role-based user model
├── students/                  # Student profiles
├── teachers/                  # Teacher profiles
├── academics/                 # Department + Course + Semester + Enrollment
├── attendance/                # Per-class attendance records
├── results/                   # Marks + GPA + CGPA + transcript
├── fees/                      # Fees + payments
├── notices/                   # Audience-filtered announcements
├── chatbot/                   # AI Assistant (services + views)
├── templates/                 # Base + includes + per-app templates
│   ├── base.html
│   ├── login.html
│   ├── dashboard.html
│   ├── includes/
│   │   ├── navbar.html
│   │   ├── sidebar.html
│   │   ├── messages.html
│   │   ├── footer.html
│   │   └── chatbot.html       # Floating bot UI
│   └── <app>/...
├── static/
│   ├── css/                   # base, login, dashboard, app CSS, chatbot, responsive
│   ├── js/                    # base, app JS, chatbot JS
│   └── images/                # logo, favicon, default profile
├── media/                     # User uploads (avatars, etc.)
└── tests/                     # End-to-end tests per app
```

---

## 🚀 Local Development

### 1. Clone & install

```bash
git clone <your-repo-url> student_portal
cd student_portal
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env — set SECRET_KEY, leave DATABASE_URL empty for SQLite
```

### 3. Apply migrations & seed demo data

```bash
python manage.py migrate
python manage.py seed_demo
python manage.py createsuperuser   # optional, for /admin/
```

### 4. Run the dev server

```bash
python manage.py runserver
# Open http://127.0.0.1:8000/
```

### Demo logins

| Username  | Password  | Role    |
|-----------|-----------|---------|
| admin     | admin     | Admin   |
| teacher1  | teacher1  | Teacher |
| student1  | student1  | Student |
| student2  | student2  | Student |
| student3  | student3  | Student |

---

## 🤖 AI Assistant — how it works

```
User asks question
      ↓
chatbot/services.py: detect_intent()
      ↓
chatbot/services.py: fetch_allowed_context()
    ┌───────────────────────────────────────────┐
    │  PERMISSION RULES (hard-coded, tested):   │
    │                                            │
    │  ✅ Student → own attendance / CGPA /     │
    │       fees / courses / routine / notices  │
    │  ✅ Anyone → public course/teacher info   │
    │  ❌ Student asking about another student  │
    │       → BLOCKED before any AI call        │
    └───────────────────────────────────────────┘
      ↓
OpenAI Chat Completions API (gpt-4o-mini by default)
      ↓
Reply + ChatHistory saved
```

### Try these in the floating bot (bottom-right):

- "What's my CGPA?"   → ✅ Returns student's own CGPA
- "My attendance?"    → ✅ Returns % of own classes attended
- "What courses am I taking?" → ✅ Lists own enrollments
- "What fees do I owe?" → ✅ Lists own unpaid fees
- "Notices today?"    → ✅ Lists notices visible to the user
- "What is Rahim's CGPA?" → 🚫 Permission denied
- "List CSE courses?" → ✅ Public catalog

### Configuring real AI

Without `OPENAI_API_KEY` set, the bot returns a graceful message indicating the API is not configured. To enable real answers:

1. Get a key from https://platform.openai.com/api-keys
2. Add to `.env`:
   ```
   OPENAI_API_KEY=sk-...
   ```
3. Restart the dev server.

The bot also works with any OpenAI-compatible endpoint — set `OPENAI_API_URL` and `OPENAI_MODEL` in `.env`.

---

## 🧪 Running Tests

```bash
python manage.py test tests
```

Tests cover:
- `test_accounts.py` — login/logout, role-based access, profile updates
- `test_students.py` — Student CRUD + permission enforcement
- `test_teachers.py` — Teacher CRUD + permission enforcement
- `test_attendance.py` — Attendance model + take attendance flow
- `test_results.py` — Grade computation + GPA/CGPA math
- `test_chatbot.py` — **Permission rule tests** — verifies the AI cannot leak another student's data

---

## ☁️ Production Deployment

### Target architecture

```
GitHub → Render (Django) → Neon PostgreSQL
                     ↓
                 AI API (OpenAI)
```

### Steps

1. **Push to GitHub** (after `cp .env.example .env`, never commit the real `.env`).

2. **Create a Neon database** at https://neon.tech — copy the connection string (format: `postgres://user:pass@host/db?sslmode=require`).

3. **Create a Render Web Service**:
   - Pick the GitHub repo.
   - Runtime: Python 3.
   - Build command: `./build.sh`
   - Start command: `gunicorn config.wsgi:application --bind 0.0.0.0:$PORT --workers 2`

4. **Environment variables in Render dashboard**:
   | Key | Value |
   |---|---|
   | SECRET_KEY | (auto-generated) |
   | DEBUG | False |
   | ALLOWED_HOSTS | .onrender.com |
   | CSRF_TRUSTED_ORIGINS | https://*.onrender.com |
   | DATABASE_URL | (paste Neon connection string) |
   | OPENAI_API_KEY | (your OpenAI key) |
   | OPENAI_MODEL | gpt-4o-mini |

5. **First deploy** — Render's `build.sh` will run `migrate` + `collectstatic`. To seed demo data on first deploy, set `SEED_DEMO=1` once.

6. Visit `https://your-app.onrender.com`.

> 💡 The `render.yaml` Blueprint file in this repo can also be used with Render's "Apply Blueprint" feature — it pre-configures the web service AND the Neon PostgreSQL database for you.

---

## 🔐 Security Notes

- `.env` is in `.gitignore` — never commit secrets.
- `DEBUG=False` and SSL redirect in production.
- `whitenoise` serves compressed static assets behind Render's CDN.
- AI calls never send the whole database — only the permission-filtered context.
- All views require login (or admin role for admin-only actions).
- CSRF protection on every form & the chatbot endpoint.

---

## 🛠 Tech Stack

- **Backend:** Django 4.2
- **Database:** SQLite (dev), Neon PostgreSQL (prod)
- **Static serving:** whitenoise
- **Production server:** gunicorn
- **AI:** OpenAI Chat Completions (or any OpenAI-compatible API)
- **Frontend:** Vanilla HTML + CSS + JS (no build step)
- **Tests:** Django test runner
- **Deployment:** GitHub → Render

---

## 📜 License

MIT — use freely for your own academic or commercial projects.
