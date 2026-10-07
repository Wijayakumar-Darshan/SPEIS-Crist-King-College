"""database.py – SQLite data layer for SPEIS."""
import sqlite3, os, re, secrets, string
from contextlib import contextmanager
from auth import hash_password

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "speis.db")
GRADES  = list(range(6, 14))
CLASSES = list("ABCDEFGH")

AL_STREAMS = ["Physical Science", "Biological Science", "Commerce", "Arts", "Technology"]

DEFAULT_SUBJECTS = {
    "Physical Science": ["Combined Mathematics", "Physics", "Chemistry"],
    "Biological Science": ["Biology", "Chemistry", "Physics"],
    "Commerce": ["Accounting", "Business Studies", "Economics"],
    "Arts": ["History", "Geography", "Political Science"],
    "Technology": ["Engineering Technology", "Science for Technology", "ICT"],
    "General": [
        "Sinhala Language", "Tamil Language", "English",
        "Mathematics", "Science", "History", "Geography",
        "Buddhism", "Shaivism", "Catholic Doctrine", "Christianity",
        "Life Skills", "Music (Western)", "Music (Oriental)", "Art",
        "Dance", "Drama", "ICT", "Health & Physical Education",
        "Practical & Technical Skills",
        "Second Language (Sinhala)", "Second Language (Tamil)",
        "Business & Accounting", "Civic Education",
        "Agriculture & Food Technology", "Media Studies",
        "Literature (English)", "Literature (Sinhala)",
        "Drama & Performing Arts",
    ],
}

DEFAULT_CAREERS = {
    "Physical Science": {
        "Engineer":      {"Combined Mathematics": 80, "Physics": 75, "Chemistry": 65},
        "Data Scientist": {"Combined Mathematics": 85, "Physics": 65, "Chemistry": 55},
    },
    "Biological Science": {
        "Doctor":     {"Biology": 85, "Chemistry": 80, "Physics": 70},
        "Pharmacist": {"Biology": 75, "Chemistry": 80, "Physics": 60},
    },
    "Commerce": {
        "Accountant":       {"Accounting": 80, "Business Studies": 65, "Economics": 65},
        "Business Manager": {"Accounting": 60, "Business Studies": 75, "Economics": 65},
    },
    "Arts": {
        "Lawyer":     {"History": 75, "Geography": 60, "Political Science": 70},
        "Journalist": {"History": 65, "Geography": 55, "Political Science": 55},
    },
    "Technology": {
        "Software Engineer":  {"Engineering Technology": 70, "ICT": 85, "Science for Technology": 65},
        "Network Technician": {"Engineering Technology": 65, "ICT": 75, "Science for Technology": 55},
    },
}


@contextmanager
def get_conn():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def run_query(sql, params=(), fetch=False, fetchone=False):
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(sql, params)
        if fetchone:
            r = cur.fetchone()
            return dict(r) if r else None
        if fetch:
            return [dict(r) for r in cur.fetchall()]
        return cur.lastrowid


def init_db():
    with get_conn() as conn:
        cur = conn.cursor()
        cur.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            username      TEXT    UNIQUE NOT NULL,
            password_hash TEXT    NOT NULL,
            full_name     TEXT,
            role          TEXT    NOT NULL CHECK(role IN ('admin','teacher','student')),
            student_reg   TEXT,
            must_change_password INTEGER NOT NULL DEFAULT 0,
            created_at    TEXT    DEFAULT(datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS streams (
            id   INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL
        );
        CREATE TABLE IF NOT EXISTS subjects (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            name      TEXT    NOT NULL,
            stream_id INTEGER NOT NULL,
            UNIQUE(name, stream_id),
            FOREIGN KEY(stream_id) REFERENCES streams(id)
        );
        CREATE TABLE IF NOT EXISTS careers (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            name      TEXT    NOT NULL,
            stream_id INTEGER NOT NULL,
            UNIQUE(name, stream_id),
            FOREIGN KEY(stream_id) REFERENCES streams(id)
        );
        CREATE TABLE IF NOT EXISTS career_cutoffs (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            career_id  INTEGER NOT NULL,
            subject_id INTEGER NOT NULL,
            min_marks  REAL    NOT NULL,
            UNIQUE(career_id, subject_id),
            FOREIGN KEY(career_id)  REFERENCES careers(id),
            FOREIGN KEY(subject_id) REFERENCES subjects(id)
        );
        CREATE TABLE IF NOT EXISTS students (
            reg_no          TEXT PRIMARY KEY,
            admission_no    TEXT UNIQUE,
            full_name       TEXT NOT NULL,
            initials_name   TEXT,
            gender          TEXT,
            dob             TEXT,
            grade           INTEGER NOT NULL DEFAULT 10,
            class_section   TEXT    NOT NULL DEFAULT 'A',
            medium          TEXT    DEFAULT 'Sinhala',
            parent_name     TEXT,
            contact_no      TEXT,
            stream_id       INTEGER,
            career_id       INTEGER,
            ol_year         INTEGER,
            al_batch        TEXT,
            al_stream       TEXT,
            university_goal TEXT,
            preferred_degree TEXT,
            career_goal     TEXT,
            target_university TEXT,
            FOREIGN KEY(stream_id) REFERENCES streams(id),
            FOREIGN KEY(career_id) REFERENCES careers(id)
        );
        CREATE TABLE IF NOT EXISTS marks (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            reg_no     TEXT    NOT NULL,
            subject_id INTEGER NOT NULL,
            term       INTEGER NOT NULL CHECK(term IN (1,2,3)),
            year       INTEGER NOT NULL,
            grade      INTEGER NOT NULL DEFAULT 10,
            marks      REAL    NOT NULL CHECK(marks >= 0 AND marks <= 100),
            UNIQUE(reg_no, subject_id, term, year),
            FOREIGN KEY(reg_no)     REFERENCES students(reg_no),
            FOREIGN KEY(subject_id) REFERENCES subjects(id)
        );
        CREATE TABLE IF NOT EXISTS exam_results (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            reg_no      TEXT    NOT NULL,
            exam_type   TEXT    NOT NULL CHECK(exam_type IN ('O/L','A/L')),
            exam_year   INTEGER NOT NULL,
            subject_id  INTEGER NOT NULL,
            result_grade TEXT NOT NULL CHECK(result_grade IN ('A','B','C','S','W')),
            entered_at  TEXT DEFAULT(datetime('now')),
            UNIQUE(reg_no, exam_type, exam_year, subject_id),
            FOREIGN KEY(reg_no) REFERENCES students(reg_no),
            FOREIGN KEY(subject_id) REFERENCES subjects(id)
        );
        CREATE TABLE IF NOT EXISTS teacher_classes (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            teacher_id    INTEGER NOT NULL,
            grade         INTEGER NOT NULL,
            class_section TEXT    NOT NULL,
            year          INTEGER NOT NULL,
            UNIQUE(teacher_id, grade, class_section, year),
            FOREIGN KEY(teacher_id) REFERENCES users(id)
        );
        CREATE TABLE IF NOT EXISTS activity_logs (
            id      INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            action  TEXT,
            ts      TEXT DEFAULT(datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS student_credentials (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            reg_no TEXT UNIQUE NOT NULL,
            username TEXT NOT NULL,
            temporary_password TEXT,
            issued_at TEXT DEFAULT(datetime('now')),
            FOREIGN KEY(reg_no) REFERENCES students(reg_no) ON DELETE CASCADE
        );
        """)

        # Lightweight forward-compatible migrations for existing SQLite databases.
        # SQLite has no IF NOT EXISTS for ADD COLUMN, so ignore duplicate-column errors.
        for ddl in (
            "ALTER TABLE users ADD COLUMN must_change_password INTEGER NOT NULL DEFAULT 0",
            "ALTER TABLE students ADD COLUMN email TEXT",
        ):
            try:
                cur.execute(ddl)
            except sqlite3.OperationalError as exc:
                if "duplicate column name" not in str(exc).lower():
                    raise

        # Seed streams
        for s in AL_STREAMS + ["General"]:
            cur.execute("INSERT OR IGNORE INTO streams (name) VALUES (?)", (s,))
        smap = {r["name"]: r["id"] for r in cur.execute("SELECT id,name FROM streams").fetchall()}

        # Seed subjects
        for sname, subs in DEFAULT_SUBJECTS.items():
            sid = smap[sname]
            for sub in subs:
                cur.execute("INSERT OR IGNORE INTO subjects (name,stream_id) VALUES (?,?)", (sub, sid))

        # Seed careers + cutoffs
        for sname, careers in DEFAULT_CAREERS.items():
            sid = smap[sname]
            for cn, cuts in careers.items():
                cur.execute("INSERT OR IGNORE INTO careers (name,stream_id) VALUES (?,?)", (cn, sid))
                cid = cur.execute("SELECT id FROM careers WHERE name=? AND stream_id=?", (cn, sid)).fetchone()["id"]
                for subname, mm in cuts.items():
                    sr = cur.execute("SELECT id FROM subjects WHERE name=? AND stream_id=?", (subname, sid)).fetchone()
                    if sr:
                        cur.execute("INSERT OR IGNORE INTO career_cutoffs (career_id,subject_id,min_marks) VALUES (?,?,?)",
                                    (cid, sr["id"], mm))

        # Default accounts
        for uname, pwd, fname, role, sreg in [
            ("admin",   "admin123",   "System Administrator", "admin",   None),
            ("teacher", "teacher123", "Counselling Teacher",  "teacher", None),
            ("student", "student123", "Demo Student",         "student", None),
        ]:
            cur.execute(
                "INSERT OR IGNORE INTO users (username,password_hash,full_name,role,student_reg) VALUES (?,?,?,?,?)",
                (uname, hash_password(pwd), fname, role, sreg),
            )
        conn.commit()


# ── Helpers ──────────────────────────────────────────────────────────────────
def get_or_create_subject(name, stream_id=None):
    if stream_id:
        r = run_query("SELECT id FROM subjects WHERE name=? AND stream_id=?", (name, stream_id), fetchone=True)
        if r: return r["id"]
    r = run_query("SELECT id FROM subjects WHERE name=?", (name,), fetchone=True)
    if r: return r["id"]
    sid = stream_id or run_query("SELECT id FROM streams WHERE name='General'", fetchone=True)["id"]
    run_query("INSERT OR IGNORE INTO subjects (name,stream_id) VALUES (?,?)", (name, sid))
    return run_query("SELECT id FROM subjects WHERE name=? AND stream_id=?", (name, sid), fetchone=True)["id"]

def get_streams():
    return run_query("SELECT * FROM streams ORDER BY name", fetch=True)

def get_stream_id(name):
    r = run_query("SELECT id FROM streams WHERE name=?", (name,), fetchone=True)
    return r["id"] if r else None

def get_subjects_by_stream(stream_id):
    return run_query("SELECT * FROM subjects WHERE stream_id=? ORDER BY name", (stream_id,), fetch=True)

def get_all_subjects():
    return run_query(
        "SELECT s.*, st.name as stream_name FROM subjects s JOIN streams st ON s.stream_id=st.id ORDER BY st.name,s.name",
        fetch=True)

def get_careers_by_stream(stream_id):
    return run_query("SELECT * FROM careers WHERE stream_id=? ORDER BY name", (stream_id,), fetch=True)

def get_all_careers():
    return run_query(
        """SELECT c.id,c.name,c.stream_id,st.name as stream_name,
           (SELECT COUNT(*) FROM career_cutoffs cc WHERE cc.career_id=c.id) as cutoff_count,
           (SELECT COUNT(*) FROM students s WHERE s.career_id=c.id) as student_count
           FROM careers c JOIN streams st ON c.stream_id=st.id ORDER BY st.name,c.name""",
        fetch=True)

def update_student_career(reg_no, stream_id=None, career_id=None):
    """Assign/update a student's academic stream and career path."""
    run_query(
        "UPDATE students SET stream_id=?, career_id=? WHERE reg_no=?",
        (stream_id, career_id, reg_no),
    )


def get_career_cutoffs(career_id):
    return run_query(
        "SELECT cc.*,s.name as subject_name FROM career_cutoffs cc JOIN subjects s ON cc.subject_id=s.id WHERE cc.career_id=?",
        (career_id,), fetch=True)

# ── Users ─────────────────────────────────────────────────────────────────────
def get_user(username):
    # Login usernames are identifiers, so ignore accidental leading/trailing
    # whitespace and username casing differences. Passwords remain case-sensitive.
    username = str(username or "").strip()
    return run_query(
        "SELECT * FROM users WHERE lower(trim(username))=lower(trim(?)) LIMIT 1",
        (username,), fetchone=True
    )

def get_user_by_id(uid):
    return run_query("SELECT * FROM users WHERE id=?", (uid,), fetchone=True)

def _clean_credential_text(value):
    """Normalize copy/paste artifacts without changing password case/content."""
    if value is None:
        return ""
    text = str(value)
    # Remove common invisible characters introduced by PDF/browser copy-paste.
    text = text.replace("\u200b", "").replace("\ufeff", "").replace("\u00a0", " ")
    return text.strip()

def get_active_student_credential(reg_no=None, username=None):
    """Return the active temporary credential for a student, if one exists."""
    cred = None
    if reg_no:
        cred = run_query(
            "SELECT * FROM student_credentials WHERE lower(trim(reg_no))=lower(trim(?)) LIMIT 1",
            (str(reg_no),), fetchone=True
        )
    if not cred and username:
        cred = run_query(
            "SELECT * FROM student_credentials WHERE lower(trim(username))=lower(trim(?)) LIMIT 1",
            (str(username),), fetchone=True
        )
    return cred

def verify_student_temporary_password(reg_no=None, password="", username=None):
    """Verify the Admin-issued temporary password and synchronize the student hash.

    This is the single source of truth used by both Student login and the first-login
    form. It deliberately does not depend on a stale ``must_change_password`` value
    in the users row; the presence of an active credential row is the authority.
    """
    from auth import hash_password
    supplied = _clean_credential_text(password)
    reg_key = _clean_credential_text(reg_no)
    user_key = _clean_credential_text(username)
    if not supplied or (not reg_key and not user_key):
        return None

    cred = get_active_student_credential(reg_no=reg_key, username=user_key)
    if not cred:
        return None
    temp = _clean_credential_text(cred.get("temporary_password"))
    if not temp or not secrets.compare_digest(temp, supplied):
        return None

    credential_reg = _clean_credential_text(cred.get("reg_no")) or reg_key
    user = get_student_user(credential_reg) if credential_reg else None
    if not user and user_key:
        user = get_user(user_key)
    if not user:
        return None

    # Always repair the account hash and first-login flag when the active Admin
    # credential is valid. This fixes legacy/out-of-sync accounts safely.
    run_query(
        "UPDATE users SET password_hash=?, must_change_password=1, student_reg=COALESCE(student_reg, ?) WHERE id=?",
        (hash_password(temp), credential_reg or user.get("student_reg"), user["id"]),
    )
    return get_user_by_id(user["id"]) or user

def verify_login(username, password):
    """Authenticate Admin/Teacher/Student accounts, including active temporary credentials."""
    from auth import verify_password

    username = _clean_credential_text(username)
    password = _clean_credential_text(password)
    if not username or not password:
        return None

    u = get_user(username)
    if not u:
        return None

    # Normal bcrypt authentication first.
    try:
        if verify_password(password, u.get("password_hash") or ""):
            return u
    except Exception:
        pass

    # Student temporary credential is authoritative while an active credential row exists.
    if str(u.get("role") or "").strip().lower() == "student":
        repaired = verify_student_temporary_password(u.get("student_reg"), password)
        if repaired:
            return repaired

    return None

def get_all_teachers():
    return run_query("SELECT * FROM users WHERE role='teacher' ORDER BY full_name", fetch=True)

def get_all_user_students():
    return run_query("SELECT * FROM users WHERE role='student' ORDER BY full_name", fetch=True)

def get_student_user(reg_no):
    return run_query(
        "SELECT * FROM users WHERE role='student' AND student_reg=?",
        (reg_no,), fetchone=True
    )

def create_user(username, password, full_name, role, student_reg=None, must_change_password=False):
    from auth import hash_password as hp
    try:
        return run_query("""INSERT INTO users
           (username,password_hash,full_name,role,student_reg,must_change_password)
           VALUES (?,?,?,?,?,?)""", (username, hp(password), full_name, role, student_reg, int(bool(must_change_password))))
    except sqlite3.IntegrityError as exc:
        raise ValueError(f"Username '{username}' already exists. Choose a different username.") from exc

def update_user_password(user_id, new_password):
    from auth import hash_password as hp
    run_query("UPDATE users SET password_hash=?, must_change_password=0 WHERE id=?", (hp(new_password), user_id))
    user = get_user_by_id(user_id)
    if user:
        if user.get("student_reg"):
            run_query("DELETE FROM student_credentials WHERE reg_no=?", (user["student_reg"],))
        run_query("DELETE FROM student_credentials WHERE lower(trim(username))=lower(trim(?))", (user.get("username") or "",))

def ensure_student_account(reg_no):
    """Create a student login if the student has none; return credential details when created."""
    student=get_student(reg_no)
    if not student: raise ValueError("Student record was not found.")
    existing=get_student_user(reg_no)
    if existing:
        return {"created_account":False,"reg_no":reg_no,"username":existing["username"],"temporary_password":None,
                "full_name":student["full_name"],"grade":student["grade"],"class_section":student["class_section"]}
    pwd=_generate_temporary_password()
    from auth import hash_password as hp
    with get_conn() as conn:
        conn.execute("""INSERT INTO users(username,password_hash,full_name,role,student_reg,must_change_password)
                       VALUES(?,?,?,?,?,1)""", (reg_no,hp(pwd),student["full_name"],"student",reg_no))
        conn.execute("INSERT INTO student_credentials(reg_no,username,temporary_password) VALUES(?,?,?)",(reg_no,reg_no,pwd))
    return {"created_account":True,"reg_no":reg_no,"username":reg_no,"temporary_password":pwd,
            "full_name":student["full_name"],"grade":student["grade"],"class_section":student["class_section"]}

def reset_student_temporary_password(reg_no):
    student = get_student(reg_no)
    if not student: raise ValueError("Student record was not found.")
    user = get_student_user(reg_no)
    if not user: raise ValueError("Student login account does not exist.")
    pwd = _generate_temporary_password()
    from auth import hash_password as hp
    with get_conn() as conn:
        conn.execute("UPDATE users SET password_hash=?, must_change_password=1, full_name=? WHERE id=?", (hp(pwd), student["full_name"], user["id"]))
        conn.execute("""INSERT INTO student_credentials(reg_no,username,temporary_password,issued_at)
                      VALUES(?,?,?,datetime('now'))
                      ON CONFLICT(reg_no) DO UPDATE SET username=excluded.username, temporary_password=excluded.temporary_password, issued_at=datetime('now')""", (reg_no, user["username"], pwd))
    return {"reg_no":reg_no,"username":user["username"],"temporary_password":pwd,"full_name":student["full_name"],"grade":student["grade"],"class_section":student["class_section"]}

def get_student_credentials(grade=None, class_section=None):
    conds=[]; params=[]
    if grade is not None: conds.append("s.grade=?"); params.append(int(grade))
    if class_section: conds.append("upper(trim(s.class_section))=upper(trim(?))"); params.append(str(class_section))
    where=("WHERE "+" AND ".join(conds)) if conds else ""
    sql="""SELECT s.reg_no, s.full_name, s.grade, s.class_section,
                    u.username, u.must_change_password, sc.temporary_password, sc.issued_at
             FROM students s
             LEFT JOIN users u ON u.student_reg=s.reg_no AND u.role='student'
             LEFT JOIN student_credentials sc ON sc.reg_no=s.reg_no
             """+where+" ORDER BY s.grade,s.class_section,s.full_name"
    return run_query(sql, tuple(params), fetch=True)

def delete_user(user_id):
    with get_conn() as conn:
        conn.execute("DELETE FROM teacher_classes WHERE teacher_id=?", (int(user_id),))
        conn.execute("DELETE FROM student_credentials WHERE reg_no IN (SELECT student_reg FROM users WHERE id=?)", (int(user_id),))
        conn.execute("DELETE FROM users WHERE id=?", (int(user_id),))

# ── Students ──────────────────────────────────────────────────────────────────
def get_student(reg_no):
    return run_query(
        """SELECT s.*,c.name as career_name,st.name as stream_name
           FROM students s
           LEFT JOIN careers c  ON s.career_id=c.id
           LEFT JOIN streams st ON s.stream_id=st.id
           WHERE s.reg_no=?""", (reg_no,), fetchone=True)

def get_all_students(grade=None, class_section=None, stream_id=None):
    filters, params = [], []
    if grade:        filters.append("s.grade=?");         params.append(grade)
    if class_section:filters.append("s.class_section=?"); params.append(class_section)
    if stream_id:    filters.append("s.stream_id=?");     params.append(stream_id)
    where = ("WHERE " + " AND ".join(filters)) if filters else ""
    return run_query(
        f"""SELECT s.*,c.name as career_name,st.name as stream_name
            FROM students s
            LEFT JOIN careers c  ON s.career_id=c.id
            LEFT JOIN streams st ON s.stream_id=st.id
            {where} ORDER BY s.grade,s.class_section,s.full_name""",
        tuple(params), fetch=True)

def upsert_student(reg_no, full_name, grade, class_section, **kwargs):
    fields = {"full_name": full_name, "grade": grade, "class_section": class_section}
    fields.update(kwargs)
    existing = run_query("SELECT reg_no FROM students WHERE reg_no=?", (reg_no,), fetchone=True)
    if existing:
        sets = ", ".join(f"{k}=?" for k in fields)
        run_query(f"UPDATE students SET {sets} WHERE reg_no=?", tuple(fields.values()) + (reg_no,))
    else:
        cols = ["reg_no"] + list(fields.keys())
        vals = [reg_no]  + list(fields.values())
        run_query(
            f"INSERT INTO students ({','.join(cols)}) VALUES ({','.join('?'*len(vals))})",
            tuple(vals))

def _normalise_student_name(name: str) -> str:
    """Normalise names for reliable Excel matching without changing stored spelling."""
    return " ".join(str(name).strip().casefold().split())


class BulkStudentMatchError(ValueError):
    """Raised when an Excel row cannot be matched safely to exactly one student."""


def _next_student_id(conn) -> str:
    """Generate a stable school-wide Student ID such as STD000001."""
    rows = conn.execute(
        "SELECT reg_no FROM students WHERE reg_no LIKE 'STD%'"
    ).fetchall()
    nums = []
    for row in rows:
        m = re.fullmatch(r"STD(\d+)", str(row["reg_no"]).strip().upper())
        if m:
            nums.append(int(m.group(1)))
    return f"STD{(max(nums) if nums else 0) + 1:06d}"


def _generate_temporary_password(length: int = 10) -> str:
    alphabet = string.ascii_letters + string.digits
    # Include symbols so the temporary credential is not trivially guessable.
    symbols = "@#$%&*"
    body = "".join(secrets.choice(alphabet) for _ in range(length - 2))
    return secrets.choice(string.ascii_uppercase) + secrets.choice(string.digits) + secrets.choice(symbols) + body


def bulk_upsert_student_account(name, grade, cls, year):
    """
    Match or create a student and guarantee a linked login account.

    Matching is deliberately conservative:
      * exactly one Name + Grade + Class match -> reuse that student;
      * multiple matches -> raise BulkStudentMatchError (never guess);
      * no match -> create STD000001-style ID and a student user.
    Returns a dict containing the stable student ID and a temporary password
    only when a new login was created.
    """
    name = str(name).strip()
    grade = int(grade)
    cls = str(cls).strip().upper()
    if not name:
        raise BulkStudentMatchError("Student name is empty.")
    if not (6 <= grade <= 13):
        raise BulkStudentMatchError(f"Invalid grade: {grade}.")
    if cls not in CLASSES:
        raise BulkStudentMatchError(f"Invalid class: {cls}.")

    with get_conn() as conn:
        # Serialize ID allocation so two simultaneous imports cannot create
        # the same STDxxxxxx identifier.
        conn.execute("BEGIN IMMEDIATE")
        rows = conn.execute(
            "SELECT reg_no, full_name FROM students WHERE grade=? AND class_section=?",
            (grade, cls),
        ).fetchall()
        wanted = _normalise_student_name(name)
        matches = [r for r in rows if _normalise_student_name(r["full_name"]) == wanted]

        if len(matches) > 1:
            ids = ", ".join(r["reg_no"] for r in matches)
            raise BulkStudentMatchError(
                f"Multiple students match '{name}' in Grade {grade}{cls} ({ids}). "
                "Resolve the duplicate in Manage Students before importing."
            )

        created_account = False
        temp_password = None

        if matches:
            reg_no = matches[0]["reg_no"]
            conn.execute(
                "UPDATE students SET full_name=?, grade=?, class_section=? WHERE reg_no=?",
                (name, grade, cls, reg_no),
            )
        else:
            reg_no = _next_student_id(conn)
            conn.execute(
                "INSERT INTO students (reg_no, full_name, grade, class_section) VALUES (?,?,?,?)",
                (reg_no, name, grade, cls),
            )

        username = reg_no
        user = conn.execute(
            "SELECT id, username, student_reg, must_change_password FROM users WHERE username=?",
            (reg_no,),
        ).fetchone()

        if user:
            # A student ID is the login username. Never silently relink a
            # username already belonging to another student.
            if user["student_reg"] not in (None, reg_no):
                raise BulkStudentMatchError(
                    f"Login username {reg_no} is already linked to another student."
                )
            conn.execute(
                "UPDATE users SET student_reg=?, full_name=?, role='student' WHERE username=?",
                (reg_no, name, reg_no),
            )
        else:
            # Handle legacy databases where the student exists but account doesn't.
            existing_link = conn.execute(
                "SELECT id, username FROM users WHERE student_reg=? AND role='student'",
                (reg_no,),
            ).fetchone()
            if existing_link:
                username = existing_link["username"]
                conn.execute(
                    "UPDATE users SET full_name=? WHERE id=?",
                    (name, existing_link["id"]),
                )
            else:
                temp_password = _generate_temporary_password()
                conn.execute(
                    """INSERT INTO users
                       (username,password_hash,full_name,role,student_reg,must_change_password)
                       VALUES (?,?,?,?,?,1)""",
                    (reg_no, hash_password(temp_password), name, "student", reg_no),
                )
                conn.execute(
                    """INSERT INTO student_credentials(reg_no,username,temporary_password)
                       VALUES (?,?,?)
                       ON CONFLICT(reg_no) DO UPDATE SET username=excluded.username, temporary_password=excluded.temporary_password, issued_at=datetime('now')""",
                    (reg_no, reg_no, temp_password),
                )
                created_account = True

        return {
            "reg_no": reg_no,
            "username": username,
            "temporary_password": temp_password,
            "created_account": created_account,
        }


# Backward-compatible wrapper used by older callers.
def upsert_student_bulk(name, grade, cls, year):
    return bulk_upsert_student_account(name, grade, cls, year)["reg_no"]

def delete_student(reg_no):
    run_query("DELETE FROM marks   WHERE reg_no=?", (reg_no,))
    run_query("DELETE FROM students WHERE reg_no=?", (reg_no,))

# ── Marks ─────────────────────────────────────────────────────────────────────
def save_mark(reg_no, subject_id, term, year, grade, marks):
    run_query(
        """INSERT INTO marks (reg_no,subject_id,term,year,grade,marks) VALUES (?,?,?,?,?,?)
           ON CONFLICT(reg_no,subject_id,term,year) DO UPDATE SET marks=excluded.marks,grade=excluded.grade""",
        (reg_no, subject_id, term, year, grade, marks))

def save_marks_bulk(reg_no, marks_by_subject, term, year, grade):
    """Persist one student's subject marks in a single SQLite transaction."""
    if not marks_by_subject:
        return 0
    saved = 0
    with get_conn() as conn:
        for subject_name, mark_value in marks_by_subject.items():
            row = conn.execute(
                "SELECT id FROM subjects WHERE name=? ORDER BY CASE WHEN stream_id=(SELECT id FROM streams WHERE name='General') THEN 0 ELSE 1 END LIMIT 1",
                (str(subject_name).strip(),),
            ).fetchone()
            if row:
                subject_id = row["id"]
            else:
                general = conn.execute(
                    "SELECT id FROM streams WHERE name='General'"
                ).fetchone()
                subject_id = conn.execute(
                    "INSERT INTO subjects (name,stream_id) VALUES (?,?)",
                    (str(subject_name).strip(), general["id"]),
                ).lastrowid
            conn.execute(
                """INSERT INTO marks
                   (reg_no,subject_id,term,year,grade,marks)
                   VALUES (?,?,?,?,?,?)
                   ON CONFLICT(reg_no,subject_id,term,year)
                   DO UPDATE SET marks=excluded.marks, grade=excluded.grade""",
                (reg_no, subject_id, int(term), int(year), int(grade), float(mark_value)),
            )
            saved += 1
    return saved


def get_marks_for_student(reg_no, year=None, term=None):
    conds, params = ["m.reg_no=?"], [reg_no]
    if year:  conds.append("m.year=?");  params.append(year)
    if term:  conds.append("m.term=?");  params.append(term)
    return run_query(
        f"SELECT m.*,s.name as subject_name FROM marks m JOIN subjects s ON m.subject_id=s.id WHERE {' AND '.join(conds)} ORDER BY m.year,s.name,m.term",
        tuple(params), fetch=True)

def get_marks_for_grades(grades, year=None):
    grades = [int(g) for g in grades]
    if not grades:
        return []
    placeholders=','.join('?'*len(grades)); params=list(grades)
    sql=f"""SELECT m.*, s.name as subject_name, st.full_name, st.grade as student_grade, st.class_section
             FROM marks m JOIN subjects s ON m.subject_id=s.id JOIN students st ON m.reg_no=st.reg_no
             WHERE st.grade IN ({placeholders})"""
    if year:
        sql += " AND m.year=?"; params.append(int(year))
    sql += " ORDER BY m.year, st.grade, st.class_section, st.full_name, s.name, m.term"
    return run_query(sql, tuple(params), fetch=True)


def get_grade_year_averages():
    return run_query(
        "SELECT m.grade,m.year,AVG(m.marks) as avg_marks,COUNT(*) as sample_size FROM marks m GROUP BY m.grade,m.year ORDER BY m.grade,m.year",
        fetch=True)

def get_grade_class_averages(year=None):
    if year:
        return run_query(
            """SELECT m.grade,s.class_section,AVG(m.marks) as avg_marks,COUNT(DISTINCT m.reg_no) as student_count
               FROM marks m JOIN students s ON m.reg_no=s.reg_no
               WHERE m.year=? GROUP BY m.grade,s.class_section ORDER BY m.grade,s.class_section""",
            (year,), fetch=True)
    return run_query(
        """SELECT m.grade,s.class_section,AVG(m.marks) as avg_marks,COUNT(DISTINCT m.reg_no) as student_count
           FROM marks m JOIN students s ON m.reg_no=s.reg_no
           GROUP BY m.grade,s.class_section ORDER BY m.grade,s.class_section""",
        fetch=True)

def get_class_subject_averages(grade, class_section, year=None):
    conds = ["st.grade=?","st.class_section=?"]; params = [grade, class_section]
    if year: conds.append("m.year=?"); params.append(year)
    return run_query(
        f"""SELECT s.name as subject_name,AVG(m.marks) as avg_marks,COUNT(DISTINCT m.reg_no) as n
            FROM marks m JOIN subjects s ON m.subject_id=s.id JOIN students st ON m.reg_no=st.reg_no
            WHERE {' AND '.join(conds)} GROUP BY m.subject_id ORDER BY avg_marks DESC""",
        tuple(params), fetch=True)

def get_student_years(reg_no):
    rows = run_query("SELECT DISTINCT year FROM marks WHERE reg_no=? ORDER BY year DESC", (reg_no,), fetch=True)
    return [r["year"] for r in rows]


# ── Official O/L / A/L results ────────────────────────────────────────────────
def save_exam_result(reg_no, exam_type, exam_year, subject_id, result_grade):
    result_grade = str(result_grade).upper().strip()
    exam_type = str(exam_type).upper().strip()
    if exam_type not in ("O/L", "A/L"):
        raise ValueError("Exam type must be O/L or A/L.")
    if result_grade not in ("A", "B", "C", "S", "W"):
        raise ValueError("Result grade must be A, B, C, S or W.")
    run_query(
        """INSERT INTO exam_results (reg_no,exam_type,exam_year,subject_id,result_grade)
           VALUES (?,?,?,?,?)
           ON CONFLICT(reg_no,exam_type,exam_year,subject_id)
           DO UPDATE SET result_grade=excluded.result_grade, entered_at=datetime('now')""",
        (reg_no, exam_type, int(exam_year), int(subject_id), result_grade))

def get_exam_results(reg_no=None, exam_type=None, exam_year=None):
    conds, params = [], []
    if reg_no: conds.append("er.reg_no=?"); params.append(reg_no)
    if exam_type: conds.append("er.exam_type=?"); params.append(exam_type)
    if exam_year: conds.append("er.exam_year=?"); params.append(int(exam_year))
    where = ("WHERE " + " AND ".join(conds)) if conds else ""
    return run_query(
        f"""SELECT er.*, s.name AS subject_name, st.full_name, st.grade, st.class_section
            FROM exam_results er JOIN subjects s ON er.subject_id=s.id
            JOIN students st ON er.reg_no=st.reg_no {where}
            ORDER BY er.exam_year DESC, st.grade, st.class_section, st.full_name, s.name""",
        tuple(params), fetch=True)

def get_exam_years(exam_type=None):
    if exam_type:
        rows = run_query("SELECT DISTINCT exam_year FROM exam_results WHERE exam_type=? ORDER BY exam_year DESC", (exam_type,), fetch=True)
    else:
        rows = run_query("SELECT DISTINCT exam_year FROM exam_results ORDER BY exam_year DESC", fetch=True)
    return [r["exam_year"] for r in rows]

def get_school_exam_pass_stats(exam_type, exam_year=None):
    rows = get_exam_results(exam_type=exam_type, exam_year=exam_year)
    total = len(rows)
    passed = sum(str(r["result_grade"]).upper() in {"A","B","C","S"} for r in rows)
    rate = round(100.0 * passed / total, 2) if total else None
    return {"exam_type": exam_type, "exam_year": exam_year, "total": total, "passed": passed, "failed": total-passed, "pass_rate": rate}

def get_school_exam_year_rates(exam_type):
    return run_query(
        """SELECT exam_year, COUNT(*) AS total,
                  SUM(CASE WHEN result_grade IN ('A','B','C','S') THEN 1 ELSE 0 END) AS passed,
                  ROUND(100.0*SUM(CASE WHEN result_grade IN ('A','B','C','S') THEN 1 ELSE 0 END)/COUNT(*),2) AS pass_rate
           FROM exam_results WHERE exam_type=? GROUP BY exam_year ORDER BY exam_year""",
        (exam_type,), fetch=True)

def delete_exam_result(result_id):
    run_query("DELETE FROM exam_results WHERE id=?", (int(result_id),))

# ── Subjects / Careers CRUD ───────────────────────────────────────────────────
def add_subject(name, stream_id):
    run_query("INSERT OR IGNORE INTO subjects (name,stream_id) VALUES (?,?)", (name, stream_id))

def update_subject(subject_id, name):
    run_query("UPDATE subjects SET name=? WHERE id=?", (name, subject_id))

def delete_subject(subject_id):
    run_query("DELETE FROM marks WHERE subject_id=?",         (subject_id,))
    run_query("DELETE FROM career_cutoffs WHERE subject_id=?", (subject_id,))
    run_query("DELETE FROM subjects WHERE id=?",               (subject_id,))

def add_career(name, stream_id, cutoffs: dict):
    run_query("INSERT OR IGNORE INTO careers (name,stream_id) VALUES (?,?)", (name, stream_id))
    cid = run_query("SELECT id FROM careers WHERE name=? AND stream_id=?", (name, stream_id), fetchone=True)["id"]
    for sid, mm in cutoffs.items():
        run_query("INSERT INTO career_cutoffs (career_id,subject_id,min_marks) VALUES (?,?,?) ON CONFLICT(career_id,subject_id) DO UPDATE SET min_marks=excluded.min_marks",
                  (cid, sid, mm))
    return cid

def update_career(career_id, name, cutoffs: dict):
    run_query("UPDATE careers SET name=? WHERE id=?", (name, career_id))
    run_query("DELETE FROM career_cutoffs WHERE career_id=?", (career_id,))
    for sid, mm in cutoffs.items():
        run_query("INSERT INTO career_cutoffs (career_id,subject_id,min_marks) VALUES (?,?,?)",
                  (career_id, sid, mm))

def delete_career(career_id):
    run_query("UPDATE students SET career_id=NULL WHERE career_id=?", (career_id,))
    run_query("DELETE FROM career_cutoffs WHERE career_id=?", (career_id,))
    run_query("DELETE FROM careers WHERE id=?",               (career_id,))

# ── Teacher class assignments ─────────────────────────────────────────────────
def assign_teacher_class(teacher_id, grade, class_section, year):
    grade=int(grade); year=int(year); class_section=str(class_section).strip().upper()
    if grade not in GRADES: raise ValueError("Grade must be between 6 and 13.")
    if class_section not in CLASSES: raise ValueError("Invalid class section.")
    teacher=get_user_by_id(int(teacher_id))
    if not teacher or teacher.get("role")!="teacher": raise ValueError("Selected teacher account was not found.")
    with get_conn() as conn:
        conn.execute("DELETE FROM teacher_classes WHERE teacher_id=?", (int(teacher_id),))
        conn.execute("INSERT INTO teacher_classes (teacher_id,grade,class_section,year) VALUES (?,?,?,?)", (int(teacher_id),grade,class_section,year))

def get_teacher_classes(teacher_id, year=None):
    if year:
        return run_query("SELECT * FROM teacher_classes WHERE teacher_id=? AND year=?", (int(teacher_id), int(year)), fetch=True)
    return run_query("SELECT * FROM teacher_classes WHERE teacher_id=? ORDER BY id DESC", (int(teacher_id),), fetch=True)

def teacher_can_access_student(teacher_id, reg_no):
    return bool(run_query("""SELECT 1 FROM students s JOIN teacher_classes tc
        ON tc.grade=s.grade AND upper(trim(tc.class_section))=upper(trim(s.class_section))
        WHERE tc.teacher_id=? AND s.reg_no=? LIMIT 1""", (int(teacher_id), str(reg_no)), fetchone=True))

def get_teacher_students(teacher_id):
    return run_query("""SELECT DISTINCT s.*, c.name AS career_name, st.name AS stream_name
        FROM students s JOIN teacher_classes tc
          ON tc.grade=s.grade AND upper(trim(tc.class_section))=upper(trim(s.class_section))
        LEFT JOIN careers c ON c.id=s.career_id LEFT JOIN streams st ON st.id=s.stream_id
        WHERE tc.teacher_id=? ORDER BY s.grade,s.class_section,s.full_name""", (int(teacher_id),), fetch=True)

def get_teacher_class_subject_averages(teacher_id, grade, class_section, year=None):
    if not teacher_can_access_class(teacher_id, grade, class_section): return []
    conds=["st.grade=?","upper(trim(st.class_section))=upper(trim(?))"]; params=[int(grade),str(class_section)]
    if year: conds.append("m.year=?"); params.append(int(year))
    return run_query(f"""SELECT s.name as subject_name,AVG(m.marks) as avg_marks,COUNT(DISTINCT m.reg_no) as n
        FROM marks m JOIN subjects s ON m.subject_id=s.id JOIN students st ON m.reg_no=st.reg_no
        WHERE {' AND '.join(conds)} GROUP BY m.subject_id ORDER BY avg_marks DESC""", tuple(params), fetch=True)

def teacher_can_access_class(teacher_id, grade, class_section):
    return bool(run_query("SELECT 1 FROM teacher_classes WHERE teacher_id=? AND grade=? AND upper(trim(class_section))=upper(trim(?)) LIMIT 1", (int(teacher_id),int(grade),str(class_section)), fetchone=True))

def save_mark_for_teacher(teacher_id, reg_no, subject_id, term, year, grade, marks):
    if not teacher_can_access_student(teacher_id, reg_no): raise PermissionError("You can only edit marks for students in your currently assigned class.")
    save_mark(reg_no,subject_id,term,year,grade,marks)

def save_marks_bulk_for_teacher(teacher_id, reg_no, marks_by_subject, term, year, grade):
    if not teacher_can_access_student(teacher_id, reg_no): raise PermissionError("You can only edit marks for students in your currently assigned class.")
    return save_marks_bulk(reg_no,marks_by_subject,term,year,grade)
