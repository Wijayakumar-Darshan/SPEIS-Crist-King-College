# SPEIS – Student Performance & Educational Intelligence System

## Quick Start
```bash
pip install -r requirements.txt
streamlit run app.py
```
Open **http://localhost:8501**

## Default Logins
| Role    | Username  | Password    |
|---------|-----------|-------------|
| Admin   | admin     | admin123    |
| Teacher | teacher   | teacher123  |
| Student | student   | student123  |

> Change default credentials before production use.

### Automatic Student Login from S1 Excel
When a teacher/admin imports an S1 marks workbook:
1. SPEIS matches an existing student by **Name + Grade + Class**.
2. If exactly one match exists, the student's existing Student ID is reused and only marks are updated.
3. If no match exists, SPEIS creates a stable Student ID such as `STD000001`, creates the linked student login, and generates a random temporary password.
4. The upload screen shows newly generated credentials once so the school can securely give them to the student.
5. The student's first login is forced through onboarding: change password, email, mobile, DOB, parent/guardian and career dream.
6. Future S1 uploads continue using the same Student ID, so marks remain attached to one student history.
7. If multiple students have the same Name + Grade + Class, SPEIS stops that row with **Needs Review** instead of guessing.

Temporary passwords are stored only as bcrypt hashes and cannot be recovered from the database.

## Key Features

### Three Roles
- **Admin** — full access: manage users, students, subjects, careers, upload marks, school analytics, AI predictions, activity logs
- **Teacher** — upload marks, enter/edit marks, view class/student performance, generate reports, AI insights
- **Student** — personal dashboard: results, charts, career readiness, AI recommendations, download reports, change password

### Excel Bulk Upload (Windows-safe)
- No temp files — uses BytesIO directly, avoiding Windows file-locking errors
- **Grades 6–9**: Junior format (`First__team__Test_8D_2026.xlsm`)
- **Grades 10–11**: O/L format (`2026__grade_11_First_Term___S1.xlsm`)
- Auto-detects grade, class section (A–H) and term from sheet headers
- Auto-registers students with stable IDs such as `STD000001` and automatically creates their login account

### AI Features
- Career readiness score (0–100) vs minimum cutoffs
- Subject-level improvement plans with status (On Track / Almost There / Needs Improvement / Critical)
- Personalised study suggestions and priority list
- Grade performance prediction (linear regression, improves with more years of data)
- O/L risk assessment (Grade 10 & 11 highlighted)

### Student Profiles
- Full personal info (name, DOB, gender, medium, parent/guardian)
- O/L details (exam year, target batch)
- A/L details (stream, batch, university goal, preferred degree, career goal, target university)

### Reports (downloadable PDF)
- Student term report + AI career insight chart
- Student annual report (3-term summary)
- Class performance report with subject breakdown
- AI grade prediction report with trend charts

### Security
- bcrypt password hashing
- Role-based access control (Admin/Teacher/Student)
- Students can only see their own records
- Activity logging (login, uploads, report downloads)
- Input validation on all forms

## File Structure
```
speis/
├── app.py              # Streamlit UI (Admin + Teacher + Student)
├── database.py         # SQLite data layer
├── excel_parser.py     # Excel bulk import (BytesIO, Windows-safe)
├── ai_advisor.py       # Career readiness & study suggestions
├── prediction_ai.py    # Grade prediction (linear regression)
├── pdf_report.py       # PDF generation (Unicode font)
├── auth.py             # bcrypt authentication
├── validators.py       # Input validation
├── security.py         # Activity logging
├── schema.prisma       # Prisma schema for DB migrations
├── NotoSansSinhala.ttf # Unicode font (Latin + Sinhala)
├── requirements.txt
└── data/               # SQLite DB auto-created here
```

## Prisma Migrations
```bash
npx prisma db push --schema schema.prisma
# or
npx prisma migrate dev --name init --schema schema.prisma
```

## Professional School UI — October 2026

The current build includes a redesigned school-focused interface:
- Professional navy/blue/teal visual system
- Reliable native Streamlit sidebar navigation with clear active states
- Responsive Admin, Teacher and Student layouts
- Refined cards, metrics, forms, tabs, tables and reports
- School-office friendly spacing, typography and contrast
- Updated login experience

The redesign is implemented in `ui.py` and does not change the existing database, authentication, AI, marks, report or Excel-import logic.


## SPEIS Commercial-Ready Update — October 2026

This build keeps the original lightweight Streamlit + SQLite architecture and adds:

### 1. Official O/L and A/L result history
- New `exam_results` table stores one result per student, exam type, exam year and subject.
- Supported grades: **A, B, C, S, W**.
- Admin can enter results for every examination year and update existing entries.
- A/B/C/S are treated as passes and W as a fail for school analytics.

### 2. Lightweight outcome forecasting
The forecasting engine in `prediction_ai.py` intentionally avoids heavy ML dependencies.
It combines:
- historical official examination pass rates, and
- the latest internal assessment pass signal.

Where both are available, the default weighting is **70% historical official results + 30% current internal assessment signal**. With insufficient official history, the system lowers confidence and clearly labels the result as an internal planning estimate.

Forecasts are available for:
- Admin: school-wide O/L and A/L next-year pass-rate estimates.
- Student: individual O/L and A/L planning estimate using the student's official history and latest relevant internal assessment data.

These estimates are not official examination predictions and should not be represented to parents/students as guarantees.

### 3. PDF and report improvements
- Teacher → Student Performance now has a dedicated **Download This Student's Performance Chart (PDF)** action.
- Teacher Reports now includes Term, Annual and Performance Chart PDFs.
- A complete student/year **ZIP report pack** can be downloaded.
- Admin AI Prediction includes a school O/L & A/L forecast PDF.
- Existing term, annual, class and AI prediction PDFs remain supported.

### 4. Deployment
1. Create a Python 3.10+ environment.
2. Install `requirements.txt`.
3. Start with:
   `streamlit run app.py`
4. The SQLite database is created under `data/speis.db` automatically.
5. For cloud deployment, attach persistent storage if the platform does not preserve the local filesystem. Otherwise, the SQLite database will reset when the deployment is rebuilt/restarted.

### 5. Production checklist before selling to a school
- Change the demo Admin/Teacher/Student passwords.
- Create school-specific accounts and remove demo accounts.
- Configure regular encrypted database backups.
- Keep the school's database outside public/static hosting paths.
- Test the school's Excel mark templates before the first live import.
- Use HTTPS in production.
- Obtain the school's approval for the data retention, privacy and reporting workflow.


### Career Path Management & AI Progress Comparison — October 2026
- Teachers can assign/update each student's academic stream and career path from **Manage Career Paths**.
- Admins retain school-wide student career management through **Manage Students → Update Career**.
- Teacher and Admin **AI Insights** compare the student's current year with the previous available year.
- The comparison includes subject-by-subject improvement/decline, career cutoffs, marks still needed, and an overall trend.
- Both Teacher and Admin can download a **Career Progress & Improvement PDF** for the selected student/year.
- The comparison is descriptive and planning-oriented; it does not replace teacher/professional judgement.

## 2026-10-04 Access & Credentials Update

The current version includes Admin-controlled teacher class assignment, teacher-only access to the assigned class, immediate reassignment, protected teacher mark editing, Admin student temporary-credential management, and class-wise credential PDF export. Temporary passwords are retained only while the account is marked as requiring a password change and are removed after the student sets a new password.


### Temporary Student Login
If Admin sees a student under **Student Temporary Login Credentials**, use the displayed Student ID/Username and the latest Temporary Password with **Login as → Student**. Temporary credentials are case-sensitive for the password. The login system tolerates accidental spaces around the username/password from copy-paste, repairs legacy temporary-credential hash mismatches, and requires the student to set a new password on first login. After the new password is saved, the old temporary password is permanently invalidated.
