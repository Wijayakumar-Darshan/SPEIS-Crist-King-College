import secrets
"""
SPEIS  (Student Performance & Educational Intelligence System)
Roles: Admin | Teacher | Student
"""
import io, datetime, zipfile
import bcrypt
import streamlit as st
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

import database as db
import ui
import ai_advisor, prediction_ai as pai, pdf_report, excel_parser
from auth import verify_password, hash_password, get_session_user, set_session_user, clear_session
from validators import (validate_reg_no, validate_name, validate_grade,
                         validate_marks, validate_password, validate_year, sanitize_text)
from security import log_activity

st.set_page_config(page_title="SPEIS · Student Performance & Educational Intelligence",
                   page_icon="🎓", layout="wide", initial_sidebar_state="expanded")
db.init_db()

# ── Theme ─────────────────────────────────────────────────────────────────────
ui.inject_css()
ui.style_matplotlib()

# ── Helpers ───────────────────────────────────────────────────────────────────
def flash_message(kind, message):
    st.session_state[f"flash_{kind}"] = message

def show_flash_messages():
    for kind, fn in (("success", st.success), ("error", st.error), ("warning", st.warning), ("info", st.info)):
        key=f"flash_{kind}"
        msg=st.session_state.pop(key, None)
        if msg: fn(msg)

def banner(icon, title, sub=""):
    ui.page_header(icon, title, sub)

def card(content_fn):
    st.markdown('<div class="card">', unsafe_allow_html=True)
    content_fn()
    st.markdown('</div>', unsafe_allow_html=True)

def _normalize_text_value(value):
    """Return a stable string value for Streamlit/PyArrow dataframe display."""
    if value is None:
        return ""
    try:
        if pd.isna(value):
            return ""
    except (TypeError, ValueError):
        pass
    return str(value).strip()


def _existing_students_for_import(name, grade, class_section):
    """Find exact normalized Name + Grade + Class matches without guessing."""
    rows = db.run_query(
        """
        SELECT reg_no, full_name, grade, class_section
        FROM students
        WHERE lower(trim(full_name)) = lower(trim(?))
          AND grade = ?
          AND upper(trim(class_section)) = upper(trim(?))
        ORDER BY reg_no
        """,
        (name, int(grade), str(class_section).strip()),
        fetch=True,
    )
    return rows or []


def _next_safe_student_reg_no():
    """Generate a collision-safe stable STD###### Student ID."""
    rows = db.run_query(
        "SELECT reg_no FROM students WHERE reg_no IS NOT NULL",
        fetch=True,
    ) or []

    used = set()
    max_num = 0
    for row in rows:
        reg = str(row.get("reg_no") or "").strip()
        used.add(reg.upper())
        if reg.upper().startswith("STD") and reg[3:].isdigit():
            max_num = max(max_num, int(reg[3:]))

    candidate_num = max_num + 1
    while True:
        candidate = f"STD{candidate_num:06d}"
        if candidate.upper() not in used:
            exists = db.run_query(
                "SELECT 1 FROM students WHERE reg_no = ? LIMIT 1",
                (candidate,),
                fetchone=True,
            )
            if not exists:
                return candidate
        candidate_num += 1


def _prepare_student_for_bulk_import(name, grade, class_section):
    """
    Stabilize student identity before account/marks import.

    One exact Name+Grade+Class match is reused. A new student receives a
    collision-safe STD###### ID. Multiple matches are never guessed.
    """
    matches = _existing_students_for_import(name, grade, class_section)

    if len(matches) > 1:
        raise ValueError(
            f"Multiple existing students match '{name}' in Grade {grade}{class_section}. "
            "Please review the duplicate student records before importing."
        )

    if len(matches) == 1:
        return matches[0]["reg_no"], False

    reg_no = _next_safe_student_reg_no()
    db.upsert_student(
        reg_no,
        str(name).strip(),
        int(grade),
        str(class_section).strip().upper(),
    )
    return reg_no, True


def sidebar_user(icon, role_label):
    u = get_session_user()
    ui.sidebar_brand()
    ui.sidebar_user_chip(u["full_name"], f"{icon} {role_label}")

def logout_btn():
    st.sidebar.markdown('<div class="sb-signout">', unsafe_allow_html=True)
    if st.sidebar.button("🚪  Sign out", width="stretch", key="global_signout"):
        u = get_session_user()
        if u: log_activity(u["id"], "logout")
        clear_session(); st.rerun()
    st.sidebar.markdown('</div>', unsafe_allow_html=True)
    st.sidebar.markdown('<div class="sb-footer">SPEIS • School Intelligence Suite<br/>Secure school administration workspace</div>', unsafe_allow_html=True)

def pivot_marks(marks_rows):
    """Build year-summary pivot from marks rows."""
    df = pd.DataFrame(marks_rows)
    if df.empty: return pd.DataFrame(), []
    piv = df.pivot_table(index="subject_name", columns="term", values="marks", aggfunc="mean")
    piv = piv.reindex(columns=[1,2,3]).round(2)
    piv["average"] = piv.mean(axis=1, skipna=True).round(2)
    sta = [{"subject_name": s, "term1": r.get(1,"-"), "term2": r.get(2,"-"),
            "term3": r.get(3,"-"), "average": r["average"]}
           for s, r in piv.iterrows()]
    return piv, sta

def fig_subj_bar(avg_dict, title):
    fig, ax = plt.subplots(figsize=(7, max(2.5, len(avg_dict)*.4)+.5))
    ax.barh(list(avg_dict.keys()), list(avg_dict.values()), color="#4f46e5")
    ax.set_xlim(0, 100); ax.set_xlabel("Marks"); ax.set_title(title)
    fig.tight_layout(); st.pyplot(fig); plt.close(fig)

def fig_vs_cutoff(ai_plan):
    labels=[p["subject"] for p in ai_plan]; x=range(len(labels)); w=.35
    fig, ax = plt.subplots(figsize=(7, 3.5))
    ax.bar([i-w/2 for i in x],[p["current"] for p in ai_plan],w,label="Student",color="#4f46e5")
    ax.bar([i+w/2 for i in x],[p["cutoff"]  for p in ai_plan],w,label="Cutoff", color="#f59e0b")
    ax.set_xticks(list(x)); ax.set_xticklabels(labels,rotation=20,ha="right")
    ax.set_ylim(0,100); ax.legend(); fig.tight_layout(); st.pyplot(fig); plt.close(fig)

STATUS_ICON = {"On Track":"✅","Almost There":"🟡","Needs Improvement":"🟠","Critical":"🔴"}

def render_ai_section(student, marks_rows):
    """Render career-readiness AI panel. Returns (ai_plan, ai_summary, readiness)."""
    if not marks_rows: return None, None, None
    avg = ai_advisor.average_marks_by_subject(marks_rows)
    if not student.get("career_id"): return None, None, None
    cuts = db.get_career_cutoffs(student["career_id"])
    if not cuts: return None, None, None
    plan    = ai_advisor.build_improvement_plan(avg, cuts)
    summary = ai_advisor.overall_summary(plan)
    ready   = ai_advisor.readiness_score(plan)
    tips    = ai_advisor.study_suggestions(plan)

    st.subheader(f"🤖 AI Career-Readiness — {student.get('career_name','')}")
    c1, c2 = st.columns([3,1])
    with c1: st.info(summary)
    with c2: st.metric("Readiness Score", f"{ready}/100")
    fig_vs_cutoff(plan)
    for p in plan:
        icon = STATUS_ICON.get(p["status"], "🔵")
        st.write(f"{icon} **{p['subject']}** — {p['message']}")
    with st.expander("📚 Study Suggestions"):
        for t in tips: st.write(f"• {t}")
    return plan, summary, ready


def render_career_path_manager(actor_label="Teacher", teacher_id=None):
    """Allow authorised school staff to assign/update a student's career path."""
    ui.section("🎯 Manage Student Career Paths")
    st.caption(f"{actor_label}s can update the student's stream and career path. The change immediately feeds the AI career-readiness analysis.")
    students = db.get_teacher_students(teacher_id) if teacher_id is not None else db.get_all_students()
    if not students:
        st.info("No students available."); return
    opts = {f"G{s['grade']}{s['class_section']} | {s['reg_no']} – {s['full_name']}": s for s in students}
    selected = st.selectbox("Student", list(opts.keys()), key=f"career_mgr_student_{actor_label}")
    stu = db.get_student(opts[selected]["reg_no"])
    streams = db.get_streams()
    stream_map = {x["name"]: x["id"] for x in streams}
    stream_names = list(stream_map.keys())
    current_stream = stu.get("stream_name") or (stream_names[0] if stream_names else "")
    stream_name = st.selectbox("Academic Stream", stream_names,
                               index=stream_names.index(current_stream) if current_stream in stream_names else 0,
                               key=f"career_mgr_stream_{actor_label}") if stream_names else ""
    sid = stream_map.get(stream_name)
    careers = db.get_careers_by_stream(sid) if sid else []
    career_names = ["-- none --"] + [c["name"] for c in careers]
    current_career = next((c["name"] for c in careers if c["id"] == stu.get("career_id")), "-- none --")
    career_name = st.selectbox("Career Path / Career Dream", career_names,
                               index=career_names.index(current_career) if current_career in career_names else 0,
                               key=f"career_mgr_career_{actor_label}")

    c1, c2 = st.columns([1, 3])
    with c1:
        st.metric("Current Career", stu.get("career_name") or "Not set")
    with c2:
        if career_name != "-- none --":
            chosen = next((c for c in careers if c["name"] == career_name), None)
            if chosen:
                st.caption(f"Career path: {chosen['name']} • {stream_name}")
    if st.button("💾 Update Student Career Path", key=f"career_mgr_save_{actor_label}"):
        cid = next((c["id"] for c in careers if c["name"] == career_name), None)
        db.update_student_career(stu["reg_no"], sid, cid)
        log_activity(get_session_user()["id"], f"updated career path for {stu['reg_no']} -> {career_name}")
        st.success(f"Career path updated for {stu['full_name']}.")
        st.rerun()


def render_career_progress_insight(student):
    """Show previous-vs-current career progress, improvement areas and downloadable report."""
    ui.section("🤖 AI Career Progress & Improvements")
    if not student.get("career_id"):
        st.warning("No career path is assigned to this student. Use Manage Student Career Paths first.")
        return
    cuts = db.get_career_cutoffs(student["career_id"])
    if not cuts:
        st.info("No career cutoff subjects are configured for this career path.")
        return
    years = db.get_student_years(student["reg_no"])
    if not years:
        st.info("No academic marks are available yet.")
        return
    current_year = st.selectbox("Current Year", years, key=f"career_insight_year_{student['reg_no']}")
    previous_years = [y for y in years if y < current_year]
    previous_year = previous_years[0] if previous_years else None
    current_rows = db.get_marks_for_student(student["reg_no"], year=current_year)
    previous_rows = db.get_marks_for_student(student["reg_no"], year=previous_year) if previous_year else []
    current_avg = ai_advisor.average_marks_by_subject(current_rows)
    previous_avg = ai_advisor.average_marks_by_subject(previous_rows) if previous_rows else {}
    comparison = ai_advisor.compare_career_progress(current_avg, previous_avg, cuts)

    st.info(ai_advisor.comparison_summary(comparison, student.get("career_name", "")))
    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Improved", comparison["improved"])
    c2.metric("Declined", comparison["declined"])
    c3.metric("At Cutoff", f"{comparison['on_target']}/{comparison['total']}")
    c4.metric("Avg Change", f"{comparison['avg_change']:+.2f}" if comparison["avg_change"] is not None else "-")

    df = pd.DataFrame([{
        "Subject": r["subject"],
        "Previous": r["previous"] if r["previous"] is not None else "-",
        "Current": r["current"],
        "Change": r["change"] if r["change"] is not None else "-",
        "Career Cutoff": r["cutoff"],
        "Trend": r["trend"],
        "Marks Needed": r["improvement_needed"],
    } for r in comparison["rows"]])
    st.dataframe(df, width="stretch", hide_index=True)

    fig,ax=plt.subplots(figsize=(9,max(3,len(comparison["rows"])*.4)))
    labels=[r["subject"] for r in comparison["rows"]]
    x=np.arange(len(labels)); w=.25
    ax.bar(x-w,[r["previous"] or 0 for r in comparison["rows"]],w,label="Previous")
    ax.bar(x,[r["current"] for r in comparison["rows"]],w,label="Current")
    ax.bar(x+w,[r["cutoff"] for r in comparison["rows"]],w,label="Career Cutoff")
    ax.set_xticks(x); ax.set_xticklabels(labels,rotation=25,ha="right",fontsize=8)
    ax.set_ylim(0,100); ax.set_ylabel("Marks"); ax.legend(); fig.tight_layout(); st.pyplot(fig); plt.close(fig)

    st.subheader("📈 Improvement Areas")
    priorities=sorted([r for r in comparison["rows"] if r["improvement_needed"]>0],
                      key=lambda r:r["improvement_needed"], reverse=True)
    if priorities:
        for r in priorities:
            change = "no previous baseline" if r["change"] is None else f"{r['change']:+.1f} marks vs previous year"
            st.warning(f"**{r['subject']}** — {r['improvement_needed']:.1f} marks needed to reach the {r['cutoff']:.1f} cutoff ({change}).")
    else:
        st.success("All configured career-path cutoffs are currently met. Maintain consistency and continue improvement.")

    report = pdf_report.career_progress_report(student, student.get("career_name"), current_year, comparison)
    st.download_button("⬇️ Download Career Progress & Improvement Report (PDF)", report,
                       f"{student['reg_no']}_{current_year}_career_progress.pdf",
                       "application/pdf", key=f"career_progress_pdf_{student['reg_no']}_{current_year}")


# ── FIRST LOGIN SETUP ────────────────────────────────────────────────────────
def student_first_login_setup(user):
    """Mandatory onboarding for accounts created by bulk Excel import."""
    stu = db.get_student(user.get("student_reg"))
    if not stu:
        st.error("Your student account is not linked to a student record. Please contact Admin.")
        return

    banner("🔐", "Complete Your First Login",
           "For your security, change the temporary password and complete your basic profile.")

    st.info(
        "Your account was created automatically from the school's marks file. "
        "Use your Student ID as the username. Please set a private password before continuing."
    )

    careers = db.get_all_careers()
    career_labels = ["I will choose later"] + [
        f"{c['name']} — {c['stream_name']}" for c in careers
    ]
    career_by_label = {f"{c['name']} — {c['stream_name']}": c for c in careers}
    current_label = "I will choose later"
    if stu.get("career_id"):
        for c in careers:
            if c["id"] == stu["career_id"]:
                current_label = f"{c['name']} — {c['stream_name']}"
                break

    with st.form("student_first_login"):
        c1, c2 = st.columns(2)
        with c1:
            st.text_input("Student ID / Username", value=user["username"], disabled=True)
            current_password = st.text_input("Temporary / Current Password *", type="password")
            new_password = st.text_input("New Password *", type="password")
            confirm_password = st.text_input("Confirm New Password *", type="password")
            email = st.text_input("Email", value=stu.get("email") or "")
        with c2:
            mobile = st.text_input("Mobile Number", value=stu.get("contact_no") or "")
            dob = st.text_input("Date of Birth (YYYY-MM-DD)", value=stu.get("dob") or "")
            parent = st.text_input("Parent / Guardian", value=stu.get("parent_name") or "")
            career_label = st.selectbox(
                "Career Dream",
                career_labels,
                index=career_labels.index(current_label),
            )

        st.caption("The password must be at least 6 characters. Never share it with another person.")
        submitted = st.form_submit_button("🔒 Save & Complete First Login", width="stretch")

    if submitted:
        # Use the same temporary-credential verifier as the main Student login.
        # This prevents the first-login form from rejecting a valid Admin-issued
        # password because of a stale hash/flag from an older database version.
        repaired_user = db.verify_student_temporary_password(
            user.get("student_reg"), current_password, username=user.get("username")
        )
        password_ok = bool(repaired_user)
        if not password_ok:
            password_ok = verify_password(current_password, user.get("password_hash") or "")
        if not password_ok:
            st.error("Current/temporary password is incorrect. Please use the latest temporary password issued by Admin.")
            return
        if repaired_user:
            user = repaired_user
        if new_password != confirm_password:
            st.error("New passwords do not match.")
            return
        ok, msg = validate_password(new_password)
        if not ok:
            st.error(msg)
            return
        if email and ("@" not in email or "." not in email.rsplit("@", 1)[-1]):
            st.error("Please enter a valid email address or leave it blank.")
            return

        selected = career_by_label.get(career_label)
        extras = {
            "email": email.strip() or None,
            "contact_no": mobile.strip() or None,
            "dob": dob.strip() or None,
            "parent_name": parent.strip() or None,
        }
        if selected:
            extras["stream_id"] = selected["stream_id"]
            extras["career_id"] = selected["id"]

        try:
            db.upsert_student(
                stu["reg_no"], stu["full_name"], stu["grade"], stu["class_section"],
                **extras
            )
            db.update_user_password(user["id"], new_password)
            updated = db.get_user_by_id(user["id"])
            set_session_user(dict(updated))
            log_activity(user["id"], "completed student first-login profile setup")
            st.success("Profile completed successfully. Welcome to SPEIS!")
            st.rerun()
        except Exception as exc:
            st.error(f"Could not save your profile: {exc}")


# ── LOGIN ─────────────────────────────────────────────────────────────────────
def login_screen():
    left, right = st.columns([1.15, 1], gap="large")
    with left:
        ui.login_hero()
    with right:
        st.markdown('<div style="height:1.2rem"></div>'
                    '<div class="login-title">Welcome back 👋</div>'
                    '<div class="login-sub">Sign in to your SPEIS account to continue.</div>',
                    unsafe_allow_html=True)
        with st.form("lf"):
            role     = st.radio("Login as", ["Admin", "Teacher", "Student"], horizontal=True)
            username = st.text_input("Username / Student ID", placeholder="e.g. STD000001")
            password = st.text_input("Password", type="password", placeholder="••••••••")
            if st.form_submit_button("Sign in →", width="stretch"):
                u = db.verify_login(username.strip(), password)
                if u and str(u.get("role") or "").strip().lower() == role.strip().lower():
                    set_session_user(dict(u))
                    log_activity(u["id"], "login")
                    st.rerun()
                else:
                    st.error("Invalid credentials or role mismatch.")
        st.caption("Forgot your password? Please contact the school administrator.")


# ═══════════════════════════════════════════════════════════════════════════════
# ADMIN DASHBOARD
# ═══════════════════════════════════════════════════════════════════════════════
def admin_dashboard():
    sidebar_user("🛡️","Admin"); u = get_session_user(); show_flash_messages()
    page = ui.sidebar_nav([
        "📊 Dashboard",
        "👤 Manage Users",
        "🎓 Manage Students",
        "📚 Manage Subjects",
        "🎯 Manage Careers",
        "📤 Upload Marks",
        "📈 Class Performance",
        "🏫 School Analytics",
        "🤖 AI Predictions",
        "🤖 AI Insights",
        "🧾 Official O/L & A/L Results",
        "📋 Activity Logs",
    ], key="admin_nav"); logout_btn()

    streams      = db.get_streams()
    stream_names = [s["name"] for s in streams]

    # ── Dashboard ─────────────────────────────────────────────────────────────
    if page == "📊 Dashboard":
        banner("🛡️","Admin Dashboard","School-wide performance overview")
        total_s = len(db.get_all_students())
        total_t = len(db.get_all_teachers())
        total_m = db.run_query("SELECT COUNT(*) as c FROM marks", fetchone=True)["c"]
        ui.stat_cards([
            ("Total Students", total_s, "🎓", "Registered learners", ui.PRIMARY),
            ("Teachers", total_t, "🧑‍🏫", "Active staff accounts", ui.ACCENT),
            ("Mark Records", f"{total_m:,}", "📝", "Across all terms", ui.WARM),
            ("Streams", len(streams), "🧭", "Academic pathways", ui.GOOD),
        ])
        years = sorted({r["year"] for r in db.run_query("SELECT DISTINCT year FROM marks",fetch=True)},reverse=True)
        if years:
            yr  = st.selectbox("Year for overview", years)
            avgs= db.get_grade_class_averages(yr)
            if avgs:
                df = pd.DataFrame(avgs).rename(columns={"grade":"Grade","class_section":"Class",
                    "avg_marks":"Avg Marks","student_count":"Students"})
                df["Avg Marks"]=df["Avg Marks"].round(2)
                ui.section(f"Grade-Class Averages ({yr})","📊")
                ch1,ch2=st.columns([1.2,1],gap="large")
                with ch1:
                    gdf=df.groupby("Grade")["Avg Marks"].mean().round(1)
                    fig,ax=plt.subplots(figsize=(6.5,3.3))
                    bars=ax.bar([f"Gr {g}" for g in gdf.index],gdf.values,color=ui.PRIMARY,width=.55)
                    ax.set_ylim(0,100); ax.set_title("Average marks by grade")
                    ax.grid(axis="x",visible=False)
                    for b,v in zip(bars,gdf.values):
                        ax.text(b.get_x()+b.get_width()/2,v+1.2,f"{v:.1f}",ha="center",fontsize=8,color=ui.INK)
                    fig.tight_layout(); st.pyplot(fig); plt.close(fig)
                with ch2:
                    st.dataframe(df, width="stretch", hide_index=True, height=300)
        else:
            ui.empty_state("📭","No marks uploaded yet. Use Upload Marks to get started.")

    # ── Manage Users ──────────────────────────────────────────────────────────
    elif page == "👤 Manage Users":
        banner("👤","Manage Users","Teachers and Student accounts")
        t1,t2,t3,t4 = st.tabs(["Teachers","Students","Create Account","🔑 Student Credentials"])

        with t1:
            teachers = db.get_all_teachers()
            if teachers:
                df=pd.DataFrame(teachers)[["id","username","full_name","created_at"]]
                st.dataframe(df,width="stretch",hide_index=True)
                with st.expander("Assign Class to Teacher"):
                    t_opts  = {t["full_name"]:t["id"] for t in teachers}
                    sel_t   = st.selectbox("Teacher",list(t_opts.keys()),key="tc_t")
                    tc_g    = st.number_input("Grade",6,13,10,key="tc_g")
                    tc_c    = st.selectbox("Class",list("ABCDEFGH"),key="tc_c")
                    tc_y    = st.number_input("Year",2020,2035,2026,key="tc_y")
                    if st.button("Assign / Update Class", key="assign_teacher_class_btn"):
                        try:
                            db.assign_teacher_class(t_opts[sel_t],int(tc_g),tc_c,int(tc_y))
                            log_activity(u["id"],f"assigned {sel_t} to Grade {int(tc_g)}{tc_c} ({int(tc_y)})")
                            flash_message("success",f"Assignment updated for {sel_t}. Their visible student list now reflects Grade {int(tc_g)}{tc_c}.")
                            st.toast("Teacher class assignment updated successfully.", icon="✅")
                            st.rerun()
                        except Exception as exc:
                            st.error(f"Assignment failed: {exc}")
                with st.expander("Delete Teacher Account"):
                    del_t = st.selectbox("Teacher to delete",[t["username"] for t in teachers],key="dt")
                    if st.checkbox("Confirm delete teacher",key="cdt"):
                        if st.button("Delete Teacher"):
                            try:
                                tid = next(t["id"] for t in teachers if t["username"]==del_t)
                                db.delete_user(tid)
                                flash_message("success",f"Teacher account '{del_t}' deleted successfully.")
                                st.rerun()
                            except Exception as exc:
                                st.error(f"Could not delete teacher: {exc}")
            else: st.info("No teachers yet.")

        with t2:
            stu_users=db.get_all_user_students()
            if stu_users:
                st.dataframe(pd.DataFrame(stu_users)[["id","username","full_name","student_reg","created_at"]],
                             width="stretch",hide_index=True)
            else: st.info("No student accounts yet.")

        with t3:
            st.subheader("Create New Account")
            with st.form("cu"):
                role_c  = st.selectbox("Role",["teacher","student"])
                uname   = st.text_input("Username")
                fname   = st.text_input("Full Name")
                pwd     = st.text_input("Password",type="password")
                sreg    = st.text_input("Student Reg No (students only)")
                if st.form_submit_button("Create Account"):
                    ok,msg=validate_password(pwd)
                    if not ok: st.error(msg)
                    elif not uname.strip(): st.error("Username required.")
                    elif not fname.strip(): st.error("Name required.")
                    else:
                        try:
                            db.create_user(uname.strip(),pwd,fname.strip(),role_c,sreg.strip() or None)
                            log_activity(u["id"],f"created {role_c} account: {uname}")
                            flash_message("success",f"{role_c.title()} account '{uname}' created successfully.")
                            st.rerun()
                        except Exception as exc:
                            st.error(f"Could not create account: {exc}")

        with t4:
            st.subheader("Student Temporary Login Credentials")
            st.caption("Temporary passwords are visible to Admin while they are still temporary. After a student changes the password, the plaintext password is removed.")
            cc1,cc2=st.columns(2)
            cg=cc1.selectbox("Grade",["All"]+[str(g) for g in db.GRADES],key="cred_grade")
            ccls=cc2.selectbox("Class",["All"]+list("ABCDEFGH"),key="cred_class")
            grade_filter=None if cg=="All" else int(cg)
            class_filter=None if ccls=="All" else ccls
            cred_rows=db.get_student_credentials(grade_filter,class_filter)
            if cred_rows:
                display=[]
                for r in cred_rows:
                    display.append({"Student ID":r["reg_no"],"Student Name":r["full_name"],"Class":f"{r['grade']}{r['class_section']}","Username":r.get("username") or "—","Temporary Password":r.get("temporary_password") or "—","Status":"Temporary" if r.get("must_change_password") and r.get("temporary_password") else ("Password changed" if r.get("username") else "No account")})
                st.dataframe(pd.DataFrame(display),width="stretch",hide_index=True)
                pdf=pdf_report.student_credentials_report(cred_rows,grade_filter,class_filter)
                label=(f"Grade {grade_filter}{class_filter}" if grade_filter and class_filter else (f"Grade {grade_filter}" if grade_filter else "All Classes"))
                st.download_button(f"⬇️ Download {label} Credentials PDF",pdf,f"student_credentials_{grade_filter or 'all'}_{class_filter or 'all'}.pdf","application/pdf",key="cred_pdf")
                st.markdown("**Reset a student's temporary password**")
                reset_opts={f"{r['reg_no']} – {r['full_name']} (G{r['grade']}{r['class_section']})":r for r in cred_rows}
                rs=st.selectbox("Student",list(reset_opts.keys()),key="reset_cred_student")
                if st.button("🔄 Generate New Temporary Password",key="reset_cred_btn"):
                    try:
                        result=db.reset_student_temporary_password(reset_opts[rs]["reg_no"])
                        log_activity(u["id"],f"reset temporary password for {result['reg_no']}")
                        flash_message("success",f"New temporary password created for {result['full_name']}: {result['temporary_password']}")
                        st.rerun()
                    except Exception as exc:
                        st.error(f"Could not reset temporary password: {exc}")
            else:
                st.info("No student records match the selected class.")

    # ── Manage Students ───────────────────────────────────────────────────────
    elif page == "🎓 Manage Students":
        banner("🎓","Manage Students","Add, edit, or remove student records")
        t1,t2,t3,t4 = st.tabs(["View","Add/Edit","Update Career","Delete"])

        with t1:
            gf=st.selectbox("Grade",["All"]+[f"Grade {g}" for g in db.GRADES],key="sf_g")
            cf=st.selectbox("Class",["All"]+list("ABCDEFGH"),key="sf_c")
            g=int(gf.split()[1]) if gf!="All" else None
            c=cf if cf!="All" else None
            stus=db.get_all_students(grade=g,class_section=c)
            st.metric("Total",len(stus))
            if stus:
                cols=["reg_no","full_name","grade","class_section","gender","stream_name","career_name"]
                df=pd.DataFrame(stus)[[c for c in cols if c in pd.DataFrame(stus).columns]]
                st.dataframe(df,width="stretch",hide_index=True)

        with t2:
            with st.form("sf"):
                st.markdown("**Student Details**")
                c1,c2,c3=st.columns(3)
                reg_no  = c1.text_input("Reg No *")
                adm_no  = c2.text_input("Admission No")
                fname_s = c3.text_input("Full Name *")
                c4,c5,c6=st.columns(3)
                initials= c4.text_input("Name with Initials")
                gender  = c5.selectbox("Gender",["Male","Female","Other"])
                dob     = c6.text_input("Date of Birth (YYYY-MM-DD)")
                c7,c8,c9=st.columns(3)
                grade_s = c7.number_input("Grade",6,13,10)
                cls_s   = c8.selectbox("Class",list("ABCDEFGH"))
                medium  = c9.selectbox("Medium",["Sinhala","Tamil","English"])
                c10,c11=st.columns(2)
                parent  = c10.text_input("Parent/Guardian")
                contact = c11.text_input("Contact No")
                st.markdown("**A/L Details (Grade 12-13)**")
                c12,c13=st.columns(2)
                al_stream=c12.selectbox("A/L Stream",["None"]+db.AL_STREAMS)
                al_batch =c13.text_input("A/L Batch (e.g. 2027-2028)")
                c14,c15=st.columns(2)
                uni_goal=c14.text_input("University Goal")
                degree  =c15.text_input("Preferred Degree")
                career_g=st.text_input("Career Goal")
                target_u=st.text_input("Target University")
                ol_year =st.number_input("O/L Exam Year",2020,2035,2026)
                if st.form_submit_button("Save Student"):
                    ok1,m1=validate_reg_no(reg_no)
                    ok2,m2=validate_name(fname_s)
                    if not ok1: st.error(m1)
                    elif not ok2: st.error(m2)
                    else:
                        extras={"admission_no":adm_no or None,"initials_name":initials or None,
                                "gender":gender,"dob":dob or None,"medium":medium,
                                "parent_name":parent or None,"contact_no":contact or None,
                                "ol_year":int(ol_year),
                                "al_stream":None if al_stream=="None" else al_stream,
                                "al_batch":al_batch or None,"university_goal":uni_goal or None,
                                "preferred_degree":degree or None,"career_goal":career_g or None,
                                "target_university":target_u or None}
                        if al_stream!="None":
                            sid=db.get_stream_id(al_stream)
                            if sid: extras["stream_id"]=sid
                        try:
                            db.upsert_student(reg_no.strip(),fname_s.strip(),int(grade_s),cls_s,**extras)
                            credential=db.ensure_student_account(reg_no.strip())
                            log_activity(u["id"],f"upserted student {reg_no}")
                            if credential.get("created_account"):
                                flash_message("success",f"Student saved successfully. Temporary login created — Username: {credential['username']} | Password: {credential['temporary_password']}")
                            else:
                                flash_message("success",f"Student {fname_s} updated successfully.")
                            st.rerun()
                        except Exception as exc:
                            st.error(f"Could not save student. Your entered details were kept on the form: {exc}")

        with t3:
            stus_all=db.get_all_students()
            if not stus_all: st.info("No students.")
            else:
                opts={f"{s['reg_no']} - {s['full_name']}":s for s in stus_all}
                sel=st.selectbox("Student",list(opts.keys()),key="uc_stu")
                stu=opts[sel]
                stream_ch=st.selectbox("A/L Stream",db.AL_STREAMS,key="uc_str")
                sid2=db.get_stream_id(stream_ch)
                careers=db.get_careers_by_stream(sid2)
                car_names=["-- none --"]+[c["name"] for c in careers]
                cur_car=next((c["name"] for c in careers if c["id"]==stu.get("career_id")),"-- none --")
                car_sel=st.selectbox("Career Dream",car_names,
                                     index=car_names.index(cur_car) if cur_car in car_names else 0,
                                     key="uc_car")
                if st.button("Update Career"):
                    cid2=next((c["id"] for c in careers if c["name"]==car_sel),None)
                    db.upsert_student(stu["reg_no"],stu["full_name"],stu["grade"],stu["class_section"],
                                      stream_id=sid2,career_id=cid2)
                    log_activity(u["id"],f"updated career for {stu['reg_no']}")
                    st.success("Career updated."); st.rerun()

        with t4:
            stus_d=db.get_all_students()
            if stus_d:
                opts2={f"{s['reg_no']} - {s['full_name']}":s for s in stus_d}
                sel2=st.selectbox("Student to delete",list(opts2.keys()),key="ds")
                if st.checkbox("Confirm delete (removes all marks too)",key="cds"):
                    if st.button("Delete Student"):
                        db.delete_student(opts2[sel2]["reg_no"])
                        log_activity(u["id"],f"deleted student {opts2[sel2]['reg_no']}")
                        st.success("Deleted."); st.rerun()

    # ── Manage Subjects ───────────────────────────────────────────────────────
    elif page == "📚 Manage Subjects":
        banner("📚","Manage Subjects")
        sel_stream=st.selectbox("Stream",stream_names)
        sid=db.get_stream_id(sel_stream)
        with st.form("asf"):
            ns=st.text_input("New subject name")
            if st.form_submit_button("Add"):
                if ns.strip(): db.add_subject(ns.strip(),sid); st.success("Added."); st.rerun()
        subs=db.get_subjects_by_stream(sid)
        for sub in subs:
            with st.expander(f"✏️ {sub['name']}"):
                c1,c2=st.columns([3,1])
                with c1:
                    with st.form(f"es_{sub['id']}"):
                        en=st.text_input("Name",value=sub["name"])
                        if st.form_submit_button("Save"):
                            if en.strip(): db.update_subject(sub["id"],en.strip()); st.success("Updated."); st.rerun()
                with c2:
                    if st.checkbox("Confirm delete",key=f"cds_{sub['id']}"):
                        if st.button("Delete",key=f"ds_{sub['id']}"):
                            db.delete_subject(sub["id"]); st.success("Deleted."); st.rerun()

    # ── Manage Careers ────────────────────────────────────────────────────────
    elif page == "🎯 Manage Careers":
        banner("🎯","Manage Careers & Cutoffs")
        tv,ta,tu,td = st.tabs(["View","Add","Update","Delete"])
        with tv:
            all_c=db.get_all_careers()
            if all_c:
                st.dataframe(pd.DataFrame(all_c).rename(
                    columns={"name":"Career","stream_name":"Stream",
                             "cutoff_count":"Subjects","student_count":"Students"}
                )[["Career","Stream","Subjects","Students"]],
                    width="stretch",hide_index=True)
                sel_v=st.selectbox("View cutoffs for",[f"{c['name']} ({c['stream_name']})" for c in all_c])
                cv=next(c for c in all_c if f"{c['name']} ({c['stream_name']})"==sel_v)
                rows=db.get_career_cutoffs(cv["id"])
                if rows: st.table(pd.DataFrame(rows)[["subject_name","min_marks"]])
            else: st.info("No careers yet.")
        with ta:
            cs=st.selectbox("Stream",stream_names,key="ac_s")
            sid=db.get_stream_id(cs); sbs=db.get_subjects_by_stream(sid)
            if not sbs: st.warning("Add subjects first.")
            else:
                cn=st.text_input("Career name",key="ac_n")
                sopts={s["name"]:s["id"] for s in sbs}
                sel_s=st.multiselect("Required subjects (select all that apply)",list(sopts.keys()))
                with st.form("acf"):
                    cuts={}
                    if sel_s:
                        cols=st.columns(2)
                        for i,nm in enumerate(sel_s):
                            with cols[i%2]:
                                cuts[sopts[nm]]=st.number_input(f"{nm} min",0,100,50,key=f"ac_{sopts[nm]}")
                    else: st.info("Select subjects above.")
                    if st.form_submit_button("Save Career"):
                        if not cn.strip(): st.error("Name required.")
                        elif not cuts: st.error("Select subjects.")
                        else:
                            db.add_career(cn.strip(),sid,cuts)
                            log_activity(u["id"],f"added career {cn}")
                            st.success("Saved."); st.rerun()
        with tu:
            cs2=st.selectbox("Stream",stream_names,key="uc_s")
            sid2=db.get_stream_id(cs2); sbs2=db.get_subjects_by_stream(sid2)
            cars2=db.get_careers_by_stream(sid2)
            if not cars2: st.info("No careers.")
            else:
                sel_c=st.selectbox("Career",[c["name"] for c in cars2],key="uc_c")
                c=next(x for x in cars2 if x["name"]==sel_c)
                cur_cuts={r["subject_id"]:r["min_marks"] for r in db.get_career_cutoffs(c["id"])}
                en=st.text_input("Career name",value=c["name"],key=f"ucn_{c['id']}")
                sopts2={s["name"]:s["id"] for s in sbs2}
                cur_names=[s["name"] for s in sbs2 if s["id"] in cur_cuts]
                sel_s2=st.multiselect("Required subjects",list(sopts2.keys()),default=cur_names,key=f"ucs_{c['id']}")
                with st.form(f"ucf_{c['id']}"):
                    nc={}
                    if sel_s2:
                        cols=st.columns(2)
                        for i,nm in enumerate(sel_s2):
                            with cols[i%2]:
                                nc[sopts2[nm]]=st.number_input(nm,0,100,int(cur_cuts.get(sopts2[nm],50)),key=f"uc_{c['id']}_{sopts2[nm]}")
                    if st.form_submit_button("Save"):
                        if en.strip() and nc:
                            db.update_career(c["id"],en.strip(),nc)
                            log_activity(u["id"],f"updated career {en}")
                            st.success("Updated."); st.rerun()
        with td:
            cs3=st.selectbox("Stream",stream_names,key="dc_s")
            cars3=db.get_careers_by_stream(db.get_stream_id(cs3))
            if cars3:
                sel3=st.selectbox("Career",[c["name"] for c in cars3],key="dc_c")
                c3=next(x for x in cars3 if x["name"]==sel3)
                n=db.run_query("SELECT COUNT(*) as c FROM students WHERE career_id=?",(c3["id"],),fetchone=True)["c"]
                if n: st.warning(f"Assigned to {n} student(s). Deleting clears their career.")
                if st.checkbox("Confirm delete",key=f"cdc_{c3['id']}"):
                    if st.button("Delete Career"):
                        db.delete_career(c3["id"])
                        log_activity(u["id"],f"deleted career {sel3}")
                        st.success("Deleted."); st.rerun()

    # ── Upload Marks ──────────────────────────────────────────────────────────
    elif page == "📤 Upload Marks":
        render_upload_page(u)

    # ── Class Performance ─────────────────────────────────────────────────────
    elif page == "📈 Class Performance":
        render_class_performance()

    # ── School Analytics ──────────────────────────────────────────────────────
    elif page == "🏫 School Analytics":
        banner("🏫","School Analytics","School-wide subject and grade analysis")
        years=[r["year"] for r in db.run_query("SELECT DISTINCT year FROM marks ORDER BY year DESC",fetch=True)]
        if not years: st.info("No marks data yet."); return
        yr=st.selectbox("Year",years)
        avgs=db.get_grade_class_averages(yr)
        if not avgs: st.info("No data for this year."); return
        df=pd.DataFrame(avgs)
        df["avg_marks"]=df["avg_marks"].round(2)
        # Heatmap-style table
        pivot=df.pivot_table(index="grade",columns="class_section",values="avg_marks")
        st.subheader("Average Marks Heatmap (Grade × Class)")
        st.dataframe(pivot.style.background_gradient(cmap="RdYlGn",vmin=40,vmax=90),
                     width="stretch")
        # Grade trend
        grade_rows=db.get_grade_year_averages()
        if grade_rows:
            gdf=pd.DataFrame(grade_rows)
            fig,ax=plt.subplots(figsize=(9,4))
            for g in sorted(gdf["grade"].unique()):
                gd=gdf[gdf["grade"]==g].sort_values("year")
                ax.plot(gd["year"],gd["avg_marks"].round(2),marker="o",label=f"Grade {g}")
            ax.set_ylim(0,100); ax.set_ylabel("Avg Marks"); ax.set_xlabel("Year")
            ax.set_title("School-wide Grade Performance Trend")
            ax.legend(ncol=4,fontsize=8); fig.tight_layout()
            st.pyplot(fig); plt.close(fig)

    # ── AI Predictions ────────────────────────────────────────────────────────
    elif page == "🤖 AI Predictions":
        render_prediction_page()

    elif page == "🤖 AI Insights":
        banner("🤖","AI Career Insights","Compare student progress and identify improvement priorities")
        stus=db.get_all_students()
        if not stus: st.info("No students."); return
        opts={f"G{s['grade']}{s['class_section']} | {s['reg_no']} – {s['full_name']}":s for s in stus}
        ch=st.selectbox("Student",list(opts.keys()),key="admin_ai_insight_student")
        stu=db.get_student(opts[ch]["reg_no"])
        render_ai_section(stu,db.get_marks_for_student(stu["reg_no"]))
        st.markdown("---")
        render_career_progress_insight(stu)

    elif page == "🧾 Official O/L & A/L Results":
        render_exam_results_admin(u)

    # ── Activity Logs ─────────────────────────────────────────────────────────
    elif page == "📋 Activity Logs":
        banner("📋","Activity Logs")
        logs=__import__("security").get_recent_logs(100)
        if logs:
            st.dataframe(pd.DataFrame(logs)[["ts","username","role","action"]].rename(
                columns={"ts":"Timestamp","username":"User","role":"Role","action":"Action"}),
                width="stretch",hide_index=True)
        else: st.info("No logs yet.")


# ═══════════════════════════════════════════════════════════════════════════════
# TEACHER DASHBOARD
# ═══════════════════════════════════════════════════════════════════════════════
def teacher_dashboard():
    sidebar_user("🧑‍🏫","Counselling Teacher"); u=get_session_user(); show_flash_messages()
    page=ui.sidebar_nav([
        "📊 Dashboard",
        "📤 Upload Marks",
        "📝 Enter / Edit Marks",
        "👤 Student Performance",
        "📈 Class Performance",
        "⬇️ Reports",
        "🎯 Manage Career Paths",
        "🤖 AI Insights",
    ], key="teacher_nav"); logout_btn()
    _icon, _name = page.split(" ", 1)
    banner(_icon, "Teacher Dashboard" if _name == "Dashboard" else _name, "Manage only your Admin-assigned classes")
    assigned_students = db.get_teacher_students(u["id"])
    if page != "📊 Dashboard" and not assigned_students:
        st.warning("No class is currently assigned to your account. Student details and marks are hidden until Admin assigns a class.")
        return

    if page == "📊 Dashboard":
        tc=db.get_teacher_classes(u["id"])
        cur = f"Grade {tc[0]['grade']}{tc[0]['class_section']}" if tc else "—"
        ui.stat_cards([
            ("Assigned Class", cur, "🏫", "Set by Admin", ui.PRIMARY),
            ("My Students", len(assigned_students), "🎓", "Visible to you", ui.ACCENT),
            ("Assignments", len(tc), "📌", "Active class assignments", ui.WARM),
        ])
        ui.section("My Assigned Classes","🏫")
        if tc:
            st.dataframe(pd.DataFrame(tc)[["grade","class_section","year"]].rename(
                columns={"grade":"Grade","class_section":"Class","year":"Year"}),
                         width="stretch",hide_index=True)
        else: ui.empty_state("📭","No classes assigned yet. Ask Admin to assign you a class.")

    elif page == "📤 Upload Marks":
        render_upload_page(u)

    elif page == "📝 Enter / Edit Marks":
        ui.section("Enter / Edit Marks")
        gf=st.selectbox("Filter Grade",["All"]+[f"Grade {g}" for g in db.GRADES],key="em_g")
        g=int(gf.split()[1]) if gf!="All" else None
        stus=[s for s in db.get_teacher_students(u["id"]) if g is None or int(s["grade"])==g]
        if not stus: st.info("No students."); return
        opts={f"G{s['grade']}{s['class_section']} | {s['reg_no']} – {s['full_name']}":s for s in stus}
        ch=st.selectbox("Student",list(opts.keys()))
        stu=opts[ch]
        c1,c2,c3=st.columns(3)
        term=c1.selectbox("Term",[1,2,3])
        year=int(c2.number_input("Year",2020,2035,2026,step=1))
        grade_yr=c3.selectbox("Grade this year",[f"Grade {g}" for g in db.GRADES],
                               index=db.GRADES.index(stu["grade"]) if stu["grade"] in db.GRADES else 4)
        gint=int(grade_yr.split()[1])

        all_subs=db.get_all_subjects()
        if stu.get("stream_id"):
            subs=db.get_subjects_by_stream(stu["stream_id"])
        else:
            # Show General subjects
            gen_id=db.get_stream_id("General")
            subs=db.get_subjects_by_stream(gen_id) if gen_id else all_subs

        existing={m["subject_id"]:m["marks"] for m in db.get_marks_for_student(stu["reg_no"],year=year,term=term)}
        with st.form("mf"):
            entries={}; cols=st.columns(2)
            for i,sub in enumerate(subs):
                with cols[i%2]:
                    entries[sub["id"]]=st.number_input(sub["name"],0.0,100.0,
                        float(existing.get(sub["id"],0.0)),step=1.0,key=f"mk_{sub['id']}")
            if st.form_submit_button(f"Save Term {term} Marks"):
                invalid=[sub["name"] for sub in subs if not validate_marks(entries[sub["id"]])[0]]
                if invalid:
                    st.error("Marks were not saved. Please correct these subjects: " + ", ".join(invalid))
                else:
                    try:
                        saved=0
                        for sid2,mv in entries.items():
                            db.save_mark_for_teacher(u["id"],stu["reg_no"],sid2,term,year,gint,mv); saved+=1
                        log_activity(u["id"],f"saved marks for {stu['reg_no']} T{term} {year}")
                        flash_message("success",f"Saved {saved} marks for {stu['full_name']} successfully.")
                        st.rerun()
                    except Exception as exc:
                        st.error(f"Marks were not saved: {exc}")

    elif page == "👤 Student Performance":
        ui.section("Student Performance")
        stus=db.get_teacher_students(u["id"])
        if not stus: st.info("No students."); return
        opts={f"G{s['grade']}{s['class_section']} | {s['reg_no']} – {s['full_name']}":s for s in stus}
        ch=st.selectbox("Student",list(opts.keys()))
        stu=db.get_student(opts[ch]["reg_no"])
        render_student_performance(stu)
        years=db.get_student_years(stu["reg_no"])
        if years:
            pyear=st.selectbox("Chart PDF year",years,key="teacher_perf_pdf_year")
            pm=db.get_marks_for_student(stu["reg_no"],year=pyear)
            if pm:
                chart_pdf=pdf_report.student_performance_report(stu,pyear,pm)
                st.download_button("⬇️ Download This Student's Performance Chart (PDF)",chart_pdf,
                                   f"{stu['reg_no']}_{pyear}_performance_chart.pdf","application/pdf",key="teacher_student_chart_pdf")

    elif page == "📈 Class Performance":
        render_class_performance(teacher_id=u["id"])

    elif page == "⬇️ Reports":
        render_reports_page(teacher_id=u["id"])

    elif page == "🎯 Manage Career Paths":
        render_career_path_manager("Teacher", teacher_id=u["id"])

    elif page == "🤖 AI Insights":
        ui.section("AI Insights")
        st.caption("Compare the student's previous and current academic performance against the selected career-path cutoffs.")
        stus=db.get_teacher_students(u["id"])
        if not stus: st.info("No students."); return
        opts={f"G{s['grade']}{s['class_section']} | {s['reg_no']} – {s['full_name']}":s for s in stus}
        ch=st.selectbox("Student",list(opts.keys()),key="teacher_ai_student")
        stu=db.get_student(opts[ch]["reg_no"])
        render_ai_section(stu,db.get_marks_for_student(stu["reg_no"]))
        st.markdown("---")
        render_career_progress_insight(stu)


# ═══════════════════════════════════════════════════════════════════════════════
# STUDENT DASHBOARD
# ═══════════════════════════════════════════════════════════════════════════════
def student_dashboard():
    sidebar_user("🎒","Student"); u=get_session_user(); show_flash_messages()
    page=ui.sidebar_nav([
        "🏠 Overview",
        "📋 My Profile",
        "📊 My Results",
        "📈 Performance Charts",
        "🎯 Career Readiness",
        "🔮 O/L & A/L Forecast",
        "🤖 AI Recommendations",
        "⬇️ Download Reports",
        "🔑 Change Password",
    ], key="student_nav"); logout_btn()
    banner("🎒","Student Dashboard" if page=="🏠 Overview" else page.split(" ",1)[1],"Your personal academic dashboard")

    # Resolve student record from linked reg_no
    stu_reg = u.get("student_reg")
    stu = db.get_student(stu_reg) if stu_reg else None

    if not stu:
        st.warning("Your student profile is not linked yet. Please contact Admin.")
        return

    if page == "🏠 Overview":
        years=db.get_student_years(stu["reg_no"])
        latest=years[0] if years else None
        rows=db.get_marks_for_student(stu["reg_no"],year=latest) if latest else []
        avg=ai_advisor.average_marks_by_subject(rows) if rows else {}
        overall=round(sum(avg.values())/len(avg),1) if avg else "—"
        ready="—"
        if rows and stu.get("career_id"):
            cuts=db.get_career_cutoffs(stu["career_id"])
            if cuts:
                ready=f"{ai_advisor.readiness_score(ai_advisor.build_improvement_plan(avg,cuts))}/100"
        ui.stat_cards([
            ("Overall Average", overall, "📈", f"Year {latest}" if latest else "No marks yet", ui.PRIMARY),
            ("Subjects", len(avg), "📚", "Assessed this year", ui.ACCENT),
            ("Career Readiness", ready, "🎯", stu.get("career_name") or "Set a career dream", ui.WARM),
            ("Class", f"{stu.get('grade','')}{stu.get('class_section','')}", "🏫", stu.get("full_name",""), ui.GOOD),
        ])
        if avg:
            ui.section("Subject averages","📊")
            fig_subj_bar(avg,f"Subject Averages – {latest}")
            best=max(avg,key=avg.get); weak=min(avg,key=avg.get)
            st.markdown(ui.pill(f"Strongest: {best} ({avg[best]:.0f})","good")+ui.pill(f"Focus area: {weak} ({avg[weak]:.0f})","warn"),
                        unsafe_allow_html=True)
        else:
            ui.empty_state("📭","No results recorded yet. Check back after your teacher uploads marks.")

    elif page == "📋 My Profile":
        ui.section("My Profile")
        c1,c2=st.columns(2,gap="large")
        with c1:
            ui.kv_card("Personal Information",[
                ("Name",stu.get("full_name","")),("Reg No",stu.get("reg_no","")),
                ("Admission No",stu.get("admission_no") or "–"),
                ("Grade",f"{stu.get('grade','')}{stu.get('class_section','')}"),
                ("Gender",stu.get("gender") or "–"),("DOB",stu.get("dob") or "–"),
                ("Medium",stu.get("medium") or "–"),("Parent",stu.get("parent_name") or "–"),
                ("Contact",stu.get("contact_no") or "–")])
        with c2:
            rows=[("Stream",stu.get("stream_name") or "–"),
                  ("Career Dream",stu.get("career_name") or "–"),
                  ("O/L Exam Year",stu.get("ol_year") or "–")]
            if stu.get("grade") in (12,13):
                rows+=[("A/L Stream",stu.get("al_stream") or "–"),("A/L Batch",stu.get("al_batch") or "–"),
                       ("University Goal",stu.get("university_goal") or "–"),
                       ("Preferred Degree",stu.get("preferred_degree") or "–"),
                       ("Target University",stu.get("target_university") or "–")]
            ui.kv_card("Academic Information",rows)

    elif page == "📊 My Results":
        ui.section("My Results")
        years=db.get_student_years(stu["reg_no"])
        if not years: st.info("No results recorded yet."); return
        yr=st.selectbox("Year",years)
        t_term,t_annual=st.tabs(["Term Results","Annual Summary"])

        with t_term:
            term=st.selectbox("Term",[1,2,3])
            mrows=db.get_marks_for_student(stu["reg_no"],year=yr,term=term)
            if not mrows: st.info("No marks for this term.")
            else:
                df=pd.DataFrame(mrows)[["subject_name","marks"]]
                df["Grade"]=df["marks"].apply(lambda m: "A" if m>=75 else ("B" if m>=65 else ("C" if m>=55 else ("S" if m>=35 else "W"))))
                st.dataframe(df.rename(columns={"subject_name":"Subject","marks":"Marks"}),
                             width="stretch",hide_index=True)
                avg=round(df["marks"].mean(),2)
                c1,c2=st.columns(2)
                c1.metric("Average",avg)
                c2.metric("Subjects",len(mrows))

        with t_annual:
            all_m=db.get_marks_for_student(stu["reg_no"],year=yr)
            if not all_m: st.info("No marks for this year.")
            else:
                piv,sta=pivot_marks(all_m)
                ov=round(piv["average"].mean(),2)
                st.dataframe(piv,width="stretch")
                st.metric("Overall Yearly Average",ov)

    elif page == "📈 Performance Charts":
        ui.section("Performance Charts")
        years=db.get_student_years(stu["reg_no"])
        if not years: st.info("No data."); return
        yr=st.selectbox("Year",years,key="pc_yr")
        all_m=db.get_marks_for_student(stu["reg_no"],year=yr)
        if not all_m: st.info("No data."); return
        avg=ai_advisor.average_marks_by_subject(all_m)
        fig_subj_bar(avg,f"Subject Averages – {yr}")

        # Term comparison
        st.subheader("Term Comparison")
        df=pd.DataFrame(all_m)
        pivot=df.pivot_table(index="subject_name",columns="term",values="marks",aggfunc="mean").round(2)
        fig,ax=plt.subplots(figsize=(8,4))
        x=np.arange(len(pivot))
        w=0.25
        for i,t in enumerate([1,2,3]):
            if t in pivot.columns:
                ax.bar(x+i*w,pivot[t].fillna(0),w,label=f"Term {t}")
        ax.set_xticks(x+w); ax.set_xticklabels(pivot.index,rotation=20,ha="right",fontsize=8)
        ax.set_ylim(0,100); ax.legend(); fig.tight_layout()
        st.pyplot(fig); plt.close(fig)

        # Class average comparison
        cls_subs=db.get_class_subject_averages(stu["grade"],stu["class_section"],yr)
        if cls_subs:
            st.subheader("My Marks vs Class Average")
            cls_avg={r["subject_name"]:round(r["avg_marks"],2) for r in cls_subs}
            my_avg =avg
            common =sorted(set(cls_avg) & set(my_avg))
            if common:
                fig2,ax2=plt.subplots(figsize=(7,3.5))
                x2=range(len(common)); w2=0.35
                ax2.bar([i-w2/2 for i in x2],[my_avg[s] for s in common],w2,label="Me",color="#4f46e5")
                ax2.bar([i+w2/2 for i in x2],[cls_avg[s] for s in common],w2,label="Class Avg",color="#f59e0b")
                ax2.set_xticks(list(x2)); ax2.set_xticklabels(common,rotation=20,ha="right",fontsize=8)
                ax2.set_ylim(0,100); ax2.legend(); fig2.tight_layout()
                st.pyplot(fig2); plt.close(fig2)

    elif page == "🎯 Career Readiness":
        ui.section("Career Readiness")
        if not stu.get("career_id"):
            st.info("No career dream set yet. Update it below.")
            stream_ch=st.selectbox("Your A/L Stream",db.AL_STREAMS)
            sid=db.get_stream_id(stream_ch)
            cars=db.get_careers_by_stream(sid)
            car_sel=st.selectbox("Career Dream",[c["name"] for c in cars])
            if st.button("Set Career Dream"):
                cid=next(c["id"] for c in cars if c["name"]==car_sel)
                db.upsert_student(stu["reg_no"],stu["full_name"],stu["grade"],stu["class_section"],
                                  stream_id=sid,career_id=cid)
                st.success("Career dream updated!"); st.rerun()
            return
        marks=db.get_marks_for_student(stu["reg_no"])
        if not marks: st.info("No marks recorded yet."); return
        render_ai_section(stu,marks)

    elif page == "🔮 O/L & A/L Forecast":
        render_student_forecast(stu)

    elif page == "🤖 AI Recommendations":
        ui.section("AI Study Recommendations")
        marks=db.get_marks_for_student(stu["reg_no"])
        if not marks: st.info("No marks recorded yet."); return
        avg=ai_advisor.average_marks_by_subject(marks)
        if not stu.get("career_id"):
            st.info("Set your career dream first (Career Readiness tab)."); return
        cuts=db.get_career_cutoffs(stu["career_id"])
        if not cuts: st.info("No cutoffs configured yet."); return
        plan=ai_advisor.build_improvement_plan(avg,cuts)
        tips=ai_advisor.study_suggestions(plan)
        st.subheader("Study Priority List")
        for i,t in enumerate(tips,1):
            st.info(f"{i}. {t}")
        # Subject ranking
        st.subheader("Your Subject Rankings")
        sorted_avg=sorted(avg.items(),key=lambda x:x[1],reverse=True)
        df=pd.DataFrame(sorted_avg,columns=["Subject","Average"])
        df["Rank"]=range(1,len(df)+1)
        df["Grade"]=df["Average"].apply(lambda m:"A" if m>=75 else("B" if m>=65 else("C" if m>=55 else("S" if m>=35 else"W"))))
        st.dataframe(df[["Rank","Subject","Average","Grade"]],width="stretch",hide_index=True)

    elif page == "⬇️ Download Reports":
        ui.section("Download My Reports")
        years=db.get_student_years(stu["reg_no"])
        if not years: st.info("No results yet."); return
        yr=st.selectbox("Year",years)
        t1,t2=st.tabs(["Term Report","Annual Report"])

        with t1:
            term=st.selectbox("Term",[1,2,3],key="dr_t")
            mrows=db.get_marks_for_student(stu["reg_no"],year=yr,term=term)
            if not mrows: st.info("No marks for this term.")
            else:
                avg2=ai_advisor.average_marks_by_subject(mrows)
                plan2=ready2=summary2=None
                if stu.get("career_id"):
                    cuts2=db.get_career_cutoffs(stu["career_id"])
                    if cuts2:
                        plan2=ai_advisor.build_improvement_plan(avg2,cuts2)
                        summary2=ai_advisor.overall_summary(plan2)
                        ready2=ai_advisor.readiness_score(plan2)
                pdf=pdf_report.student_term_report(stu,term,yr,mrows,plan2,summary2,ready2)
                st.download_button(f"Download Term {term} Report (PDF)",pdf,
                                   f"{stu['reg_no']}_T{term}_{yr}.pdf","application/pdf")

        with t2:
            all_m2=db.get_marks_for_student(stu["reg_no"],year=yr)
            if not all_m2: st.info("No marks for this year.")
            else:
                piv2,sta2=pivot_marks(all_m2)
                ov2=round(piv2["average"].mean(),2)
                avg3=ai_advisor.average_marks_by_subject(all_m2)
                plan3=summary3=None
                if stu.get("career_id"):
                    cuts3=db.get_career_cutoffs(stu["career_id"])
                    if cuts3:
                        plan3=ai_advisor.build_improvement_plan(avg3,cuts3)
                        summary3=ai_advisor.overall_summary(plan3)
                pdf2=pdf_report.student_year_report(stu,yr,sta2,ov2,plan3,summary3)
                st.download_button("Download Annual Report (PDF)",pdf2,
                                   f"{stu['reg_no']}_{yr}_annual.pdf","application/pdf")

    elif page == "🔑 Change Password":
        ui.section("Change Password")
        with st.form("cpf"):
            cur_p=st.text_input("Current Password",type="password")
            new_p=st.text_input("New Password",type="password")
            cnf_p=st.text_input("Confirm Password",type="password")
            if st.form_submit_button("Change Password"):
                if not verify_password(cur_p,u["password_hash"]):
                    st.error("Current password incorrect.")
                elif new_p!=cnf_p:
                    st.error("Passwords do not match.")
                else:
                    ok,msg=validate_password(new_p)
                    if not ok: st.error(msg)
                    else:
                        db.update_user_password(u["id"],new_p)
                        log_activity(u["id"],"changed password")
                        st.success("Password updated successfully.")



def render_student_forecast(stu):
    ui.section("O/L & A/L Outcome Forecast")
    st.caption("A lightweight planning estimate using your official result history and recent internal assessment data.")
    for exam_type in ("O/L","A/L"):
        st.subheader(f"{exam_type} Forecast")
        hist=db.get_exam_results(stu["reg_no"],exam_type=exam_type)
        marks=db.get_marks_for_student(stu["reg_no"])
        target_grades=(10,11) if exam_type=="O/L" else (12,13)
        marks=[m for m in marks if m.get("grade") in target_grades or m.get("student_grade") in target_grades]
        latest_year=max([m["year"] for m in marks], default=None)
        if latest_year is not None:
            marks=[m for m in marks if m["year"]==latest_year]
        if not hist and not marks:
            st.info(f"No {exam_type} result or assessment data is available yet."); continue
        target=(max([r["exam_year"] for r in hist]) + 1) if hist else datetime.date.today().year + 1
        forecast=pai.student_exam_forecast(hist,marks,target)
        c1,c2,c3=st.columns(3)
        c1.metric("Estimated Pass Rate",f"{forecast['pass_rate']}%" if forecast['pass_rate'] is not None else "—")
        c2.metric("Confidence",forecast.get("confidence","—"))
        c3.metric("Target Year",forecast.get("target_year","—"))
        if hist:
            rows=[{"Year":r["exam_year"],"Subject":r["subject_name"],"Grade":r["result_grade"]} for r in hist]
            st.dataframe(pd.DataFrame(rows),width="stretch",hide_index=True)
        st.caption(f"Method: {forecast.get('method','—')}. This is an internal planning estimate, not an official examination prediction.")


# ═══════════════════════════════════════════════════════════════════════════════
# SHARED PAGES
# ═══════════════════════════════════════════════════════════════════════════════
def render_student_performance(stu):
    if not stu: st.warning("Student not found."); return
    years=db.get_student_years(stu["reg_no"])
    if not years: st.info("No marks recorded."); return
    yr=st.selectbox("Year",years,key="sp_yr")
    all_m=db.get_marks_for_student(stu["reg_no"],year=yr)
    if not all_m: st.info("No marks for this year."); return
    avg=ai_advisor.average_marks_by_subject(all_m)
    c1,c2,c3=st.columns(3)
    c1.metric("Overall Avg",round(sum(avg.values())/len(avg),2) if avg else "-")
    c2.metric("Subjects",len(avg))
    c3.metric("Grade",f"{stu.get('grade','')}{stu.get('class_section','')}")
    fig_subj_bar(avg,f"{stu['full_name']} – {yr} Average")
    render_ai_section(stu,all_m)


def render_class_performance(teacher_id=None):
    ui.section("Class-wise Performance")
    years=[r["year"] for r in db.run_query("SELECT DISTINCT year FROM marks ORDER BY year DESC",fetch=True)]
    if not years: st.info("No data."); return
    yr=st.selectbox("Year",years,key="cp_yr")
    avgs=db.get_grade_class_averages(yr)
    if teacher_id is not None:
        allowed={(int(x["grade"]),str(x["class_section"]).upper()) for x in db.get_teacher_classes(teacher_id)}
        avgs=[r for r in avgs if (int(r["grade"]),str(r["class_section"]).upper()) in allowed]
    if not avgs: st.info("No data."); return
    df=pd.DataFrame(avgs); df["avg_marks"]=df["avg_marks"].round(2)
    df.rename(columns={"grade":"Grade","class_section":"Class","avg_marks":"Avg","student_count":"Students"},inplace=True)
    st.dataframe(df,width="stretch",hide_index=True)

    for grade in sorted(df["Grade"].unique()):
        gdf=df[df["Grade"]==grade].sort_values("Class")
        if gdf.empty: continue
        fig,ax=plt.subplots(figsize=(max(3,len(gdf)*0.7),3))
        bars=ax.bar(gdf["Class"],gdf["Avg"],color="#4f46e5",width=.5)
        ax.set_ylim(0,100); ax.set_title(f"Grade {grade} ({yr})")
        for bar,val in zip(bars,gdf["Avg"]):
            ax.text(bar.get_x()+bar.get_width()/2,bar.get_height()+.5,
                    f"{val:.1f}",ha="center",va="bottom",fontsize=8)
        fig.tight_layout(); st.pyplot(fig); plt.close(fig)

    st.markdown("---"); st.subheader("Drill Into a Class")
    g_opts=[f"Grade {g}" for g in sorted(df["Grade"].unique())]
    sel_g=st.selectbox("Grade",g_opts,key="cp_g")
    gint=int(sel_g.split()[1])
    classes=df[df["Grade"]==gint]["Class"].tolist()
    sel_c=st.selectbox("Class",classes,key="cp_c")
    subs=db.get_teacher_class_subject_averages(teacher_id,gint,sel_c,yr) if teacher_id is not None else db.get_class_subject_averages(gint,sel_c,yr)
    if subs:
        sdf=pd.DataFrame(subs); sdf["avg_marks"]=sdf["avg_marks"].round(2)
        fig2,ax2=plt.subplots(figsize=(7,max(3,len(sdf)*.4)))
        ax2.barh(sdf["subject_name"],sdf["avg_marks"],color="#4f46e5")
        ax2.set_xlim(0,100); ax2.set_title(f"Grade {gint}{sel_c} Subjects ({yr})")
        fig2.tight_layout(); st.pyplot(fig2); plt.close(fig2)
        st.dataframe(sdf[["subject_name","avg_marks","n"]].rename(
            columns={"subject_name":"Subject","avg_marks":"Avg","n":"Students"}),
            width="stretch",hide_index=True)

        row2=df[(df["Grade"]==gint)&(df["Class"]==sel_c)]
        ca=float(row2["Avg"].values[0]) if not row2.empty else 0
        sc=int(row2["Students"].values[0]) if not row2.empty else 0
        pdf=pdf_report.class_report(gint,sel_c,yr,subs,ca,sc)
        st.download_button(f"Download Grade {gint}{sel_c} Report (PDF)",pdf,
                           f"G{gint}{sel_c}_{yr}_class.pdf","application/pdf")


def render_prediction_page():
    ui.section("AI Grade Performance Prediction")
    st.caption("Linear regression trained on all marks. More years = higher confidence. Grades 10-11 = O/L critical.")
    rows=db.get_grade_year_averages()
    if not rows: st.warning("No marks data yet."); return
    results=pai.predict_grade_performance(rows,2)
    ol_sum=pai.ol_risk_summary(results)
    st.info(ol_sum)

    # School-level next-exam pass-rate forecasting.
    st.subheader("🏫 Next-Year School Exam Pass-Rate Forecast")
    latest_marks_years=[r["year"] for r in db.run_query("SELECT DISTINCT year FROM marks ORDER BY year DESC",fetch=True)]
    forecast_year=(latest_marks_years[0] + 1) if latest_marks_years else datetime.date.today().year + 1
    ol_hist=db.get_exam_results(exam_type="O/L")
    al_hist=db.get_exam_results(exam_type="A/L")
    ol_internal=db.get_marks_for_grades((10,11), year=latest_marks_years[0]) if latest_marks_years else []
    al_internal=db.get_marks_for_grades((12,13), year=latest_marks_years[0]) if latest_marks_years else []
    ol_forecast=pai.forecast_exam_pass_rate(ol_hist,ol_internal,forecast_year)
    al_forecast=pai.forecast_exam_pass_rate(al_hist,al_internal,forecast_year)
    fc1,fc2=st.columns(2)
    with fc1:
        st.metric(f"O/L {forecast_year} Estimated Pass Rate", f"{ol_forecast['pass_rate']}%" if ol_forecast['pass_rate'] is not None else "—")
        st.caption(f"Confidence: {ol_forecast['confidence']} · {ol_forecast['method']}")
    with fc2:
        st.metric(f"A/L {forecast_year} Estimated Pass Rate", f"{al_forecast['pass_rate']}%" if al_forecast['pass_rate'] is not None else "—")
        st.caption(f"Confidence: {al_forecast['confidence']} · {al_forecast['method']}")
    st.caption("Forecasts are internal planning estimates, not official examination predictions.")
    ol_stats=db.get_school_exam_pass_stats("O/L"); al_stats=db.get_school_exam_pass_stats("A/L")
    forecast_pdf=pdf_report.outcome_forecast_report({},ol_forecast,al_forecast,ol_stats,al_stats)
    st.download_button("⬇️ Download School O/L & A/L Forecast PDF",forecast_pdf,f"school_exam_forecast_{forecast_year}.pdf","application/pdf",key="school_exam_forecast_pdf")
    with_data=[r for r in results if r["data_points"]>0]
    cols=st.columns(min(len(with_data),4))
    for i,r in enumerate(with_data[:4]):
        col=pai.RISK_COLORS[r["status"]]
        with cols[i]:
            st.markdown(
                f"<div style='border-left:5px solid {col};background:{col}18;border-radius:12px;"
                f"padding:.8rem 1rem;margin-bottom:.5rem;'>"
                f"<b>Grade {r['grade']}</b><br/>"
                f"<span style='font-size:1.5rem;color:{col};font-weight:700;'>{r['predicted_avg']}</span><br/>"
                f"<small>{pai.RISK_LABELS.get(r['status'],r['status'])} · {r['confidence']}</small></div>",
                unsafe_allow_html=True)
    if len(with_data)>4:
        cols2=st.columns(min(len(with_data)-4,4))
        for i,r in enumerate(with_data[4:8]):
            col=pai.RISK_COLORS[r["status"]]
            with cols2[i]:
                st.markdown(
                    f"<div style='border-left:5px solid {col};background:{col}18;border-radius:12px;"
                    f"padding:.8rem 1rem;margin-bottom:.5rem;'>"
                    f"<b>Grade {r['grade']}</b><br/>"
                    f"<span style='font-size:1.5rem;color:{col};font-weight:700;'>{r['predicted_avg']}</span><br/>"
                    f"<small>{pai.RISK_LABELS.get(r['status'],r['status'])} · {r['confidence']}</small></div>",
                    unsafe_allow_html=True)
    st.subheader("Current vs Predicted")
    x=np.arange(8); w=.38
    fig,ax=plt.subplots(figsize=(10,4))
    cur=[r["current_avg"] or 0 for r in results]
    pred=[r["predicted_avg"] or 0 for r in results]
    bcol=[pai.RISK_COLORS.get(r["status"],"#aaa") for r in results]
    ax.bar(x-w/2,cur,w,label="Current",color="#4f46e5",alpha=.85)
    ax.bar(x+w/2,pred,w,label="Predicted",color=bcol,alpha=.85)
    for yv,col,ls,lb in [(75,"#10b981","--","Strong"),(60,"#4f46e5",":","On Track"),(45,"#f0a500","-.","Warning")]:
        ax.axhline(yv,color=col,linestyle=ls,linewidth=1.2,label=lb)
    ax.set_xticks(x); ax.set_xticklabels([f"Gr {r['grade']}" for r in results])
    ax.set_ylim(0,100); ax.legend(fontsize=8,loc="lower right"); fig.tight_layout()
    st.pyplot(fig); plt.close(fig)

    st.subheader("Trend Lines")
    fig2,ax2=plt.subplots(figsize=(10,4))
    cl=plt.cm.tab10.colors
    for i,r in enumerate(with_data):
        c=cl[i%len(cl)]
        hy=[h[0] for h in r["historical"]]; hm=[h[1] for h in r["historical"]]
        py=[p[0] for p in r["projection_series"]]; pm=[p[1] for p in r["projection_series"]]
        ax2.scatter(hy,hm,color=c,s=30,zorder=3)
        if len(py)>1:
            ax2.plot(py,pm,color=c,linewidth=2,linestyle="--" if r["data_points"]==1 else "-",label=f"Grade {r['grade']}")
    ax2.set_ylim(0,100); ax2.set_xlabel("Year"); ax2.set_ylabel("Avg")
    ax2.legend(fontsize=8,ncol=4,loc="lower right"); fig2.tight_layout()
    st.pyplot(fig2); plt.close(fig2)

    prediction_table = pd.DataFrame([
        {
            "Grade": _normalize_text_value(r["grade"]),
            "Years": _normalize_text_value(r["data_points"]),
            "Current": _normalize_text_value(r["current_avg"]),
            "Predicted": _normalize_text_value(r["predicted_avg"]),
            "Trend/yr": _normalize_text_value(r["trend_slope"]),
            "Status": _normalize_text_value(r["status"]),
            "Confidence": _normalize_text_value(r["confidence"]),
        }
        for r in results
    ])
    st.dataframe(prediction_table, width="stretch", hide_index=True)
    for r in with_data:
        col=pai.RISK_COLORS[r["status"]]
        st.markdown(f"<div style='border-left:4px solid {col};padding:.4rem .8rem;margin:.2rem 0;border-radius:6px;background:{col}10;'>{r['message']}</div>",
                    unsafe_allow_html=True)
    pdf=pdf_report.prediction_report(results,ol_sum)
    st.download_button("Download AI Prediction Report (PDF)",pdf,
                       f"prediction_{datetime.date.today()}.pdf","application/pdf")


def render_upload_page(u):
    ui.section("Bulk Upload Marks from Excel")
    st.markdown("""
> **Supported formats:**  
> - Grades 6–9: Junior class sheets (e.g. `First__team__Test_8D_2026.xlsm`)  
> - Grades 10–11: O/L format (e.g. `2026__grade_11_First_Term___S1.xlsm`)  
> 
> Each class sheet (A–H) is imported. Students auto-registered as `YEAR-GradeClass-SeqNo`.
""")
    c1,c2,c3=st.columns(3)
    grade_hint_label=c1.selectbox(
        "Grade hint",
        ["Auto"] + [str(g) for g in range(6,14)],
        key="ul_g",
        help="Use Auto to detect the grade from the workbook/file name.",
    )
    hint_g=None if grade_hint_label=="Auto" else int(grade_hint_label)
    ov_term=c2.selectbox("Term","Auto-detect 1 2 3".split(),key="ul_t")
    ov_year=int(c3.number_input("Year",2020,2035,2026,step=1,key="ul_y"))

    uploaded=st.file_uploader("Upload .xlsx or .xlsm",type=["xlsx","xlsm"],key="ul_f")
    if not uploaded: return

    # Windows-safe: pass BytesIO directly — no temp file created
    try:
        file_bytes=io.BytesIO(uploaded.getbuffer())
        fmt,classes=excel_parser.detect_and_parse(file_bytes,hint_g or None,filename=uploaded.name)
    except Exception as e:
        st.error(f"Parse error: {e}"); return

    if not classes:
        st.warning("No class data found in file."); return
    if u.get("role") == "teacher":
        allowed={(int(x["grade"]),str(x["class_section"]).upper()) for x in db.get_teacher_classes(u["id"])}
        unauthorized=[f"Grade {int(c.get('grade') or hint_g)}{str(c.get('class_section','A')).upper()}" for c in classes
                      if (int(c.get("grade") or hint_g or 0),str(c.get("class_section","A")).upper()) not in allowed]
        if unauthorized:
            st.error("Upload blocked. These classes are not assigned to you: " + ", ".join(unauthorized))
            return

    st.success(f"Format: **{fmt.upper()}** | {len(classes)} class(es) detected")

    for cls_data in classes:
        grade=cls_data.get("grade") or hint_g
        cls  =cls_data.get("class_section","A")
        term =int(ov_term) if ov_term!="Auto-detect" else (cls_data.get("term") or 1)
        year =cls_data.get("year") or ov_year
        stus =cls_data.get("students",[])

        with st.expander(f"Grade {grade}{cls}  |  Term {term}  {year}  |  {len(stus)} students",expanded=False):
            if not stus: st.info("No students found."); continue
            preview=pd.DataFrame([{"Name":s["name"],"Subjects":len(s["marks"]),
                "Sample":str(list(s["marks"].items())[:3])} for s in stus[:8]])
            st.dataframe(preview,width="stretch",hide_index=True)
            if len(stus)>8: st.caption(f"... and {len(stus)-8} more")

            if st.button(f"Import Grade {grade}{cls}",key=f"imp_{grade}{cls}_{term}_{year}"):
                ok_n=err_n=created_n=updated_n=0
                credentials=[]
                errors=[]
                with st.spinner("Importing students, accounts and marks..."):
                    for stu_row in stus:
                        try:
                            # Stabilize the student identity before account creation.
                            prepared_reg_no, _ = _prepare_student_for_bulk_import(
                                stu_row["name"], grade, cls
                            )

                            result=db.bulk_upsert_student_account(
                                stu_row["name"], grade, cls, year
                            )
                            rn=result.get("reg_no") or prepared_reg_no
                            if result["created_account"]:
                                created_n += 1
                                credentials.append({
                                    "Student ID": result["username"],
                                    "Name": stu_row["name"],
                                    "Temporary Password": result["temporary_password"],
                                })
                            else:
                                updated_n += 1

                            db.save_marks_bulk(
                                rn, stu_row["marks"], term, year, grade
                            )
                            ok_n += 1
                        except Exception as ex:
                            err_n += 1
                            errors.append(f"{stu_row['name']}: {ex}")

                if credentials:
                    st.session_state.setdefault("bulk_credentials", []).extend(credentials)
                log_activity(
                    u["id"],
                    f"bulk import G{grade}{cls} T{term} {year}: "
                    f"{ok_n} ok, {created_n} accounts created, {updated_n} matched, {err_n} err"
                )
                st.success(
                    f"Imported {ok_n} students. {created_n} new login accounts created, "
                    f"{updated_n} existing students matched, {err_n} skipped."
                )
                if credentials:
                    st.warning(
                        "These credentials are now also available in Admin → Manage Users → Student Credentials until the student changes the password."
                    )
                    credentials_df = pd.DataFrame(credentials).fillna("").astype(str)
                    st.dataframe(
                        credentials_df,
                        width="stretch",
                        hide_index=True,
                    )
                if errors:
                    with st.expander(f"⚠️ {len(errors)} row(s) need review"):
                        for msg in errors:
                            st.error(msg)


    # Keep newly generated credentials visible after Streamlit reruns.
    saved_credentials = st.session_state.get("bulk_credentials", [])
    if saved_credentials:
        st.markdown("---")
        st.subheader("🔐 Newly Created Student Login Credentials")
        st.caption(
            "These are temporary passwords generated by SPEIS. "
            "Students should change them during first login."
        )
        saved_credentials_df = pd.DataFrame(saved_credentials).fillna("").astype(str)
        st.dataframe(
            saved_credentials_df,
            width="stretch",
            hide_index=True,
        )


def _zip_files(files):
    """Create an in-memory ZIP without writing temporary report files to disk."""
    out=io.BytesIO()
    with zipfile.ZipFile(out,"w",zipfile.ZIP_DEFLATED) as z:
        for filename,data in files:
            z.writestr(filename,data)
    return out.getvalue()


def _career_ai_for_report(stu, marks):
    plan=summ=ready=None
    if stu.get("career_id"):
        avg=ai_advisor.average_marks_by_subject(marks)
        cuts=db.get_career_cutoffs(stu["career_id"])
        if cuts:
            plan=ai_advisor.build_improvement_plan(avg,cuts); summ=ai_advisor.overall_summary(plan); ready=ai_advisor.readiness_score(plan)
    return plan,summ,ready


def render_reports_page(teacher_id=None):
    ui.section("Download Reports")
    st.caption("Every report is generated in memory. Use the ZIP buttons to download multiple PDFs together.")
    stus=db.get_teacher_students(teacher_id) if teacher_id is not None else db.get_all_students()
    if not stus: st.info("No students."); return
    opts={f"G{s['grade']}{s['class_section']} | {s['reg_no']} – {s['full_name']}":s for s in stus}
    ch=st.selectbox("Student",list(opts.keys()),key="reports_student")
    stu=db.get_student(opts[ch]["reg_no"]); years=db.get_student_years(stu["reg_no"])
    if not years: st.info("No marks."); return
    yr=st.selectbox("Year",years,key="reports_year")
    all_m=db.get_marks_for_student(stu["reg_no"],year=yr)
    t1,t2,t3=st.tabs(["Term Report","Annual Report","Performance Chart"])
    generated=[]
    with t1:
        term=st.selectbox("Term",[1,2,3],key="rr_t")
        mrows=db.get_marks_for_student(stu["reg_no"],year=yr,term=term)
        if not mrows: st.info("No marks.")
        else:
            plan,summ,ready=_career_ai_for_report(stu,mrows)
            pdf=pdf_report.student_term_report(stu,term,yr,mrows,plan,summ,ready)
            generated.append((f"{stu['reg_no']}_T{term}_{yr}.pdf",pdf))
            st.download_button("⬇️ Download Term Report (PDF)",pdf,generated[-1][0],"application/pdf",key="rr_term_pdf")
    with t2:
        if not all_m: st.info("No marks.")
        else:
            piv,sta=pivot_marks(all_m); ov=round(piv["average"].mean(),2)
            plan2,summ2,_=_career_ai_for_report(stu,all_m)
            pdf2=pdf_report.student_year_report(stu,yr,sta,ov,plan2,summ2)
            generated.append((f"{stu['reg_no']}_{yr}_annual.pdf",pdf2))
            st.download_button("⬇️ Download Annual Report (PDF)",pdf2,generated[-1][0],"application/pdf",key="rr_annual_pdf")
    with t3:
        if not all_m: st.info("No marks.")
        else:
            chart=pdf_report.student_performance_report(stu,yr,all_m)
            generated.append((f"{stu['reg_no']}_{yr}_performance_chart.pdf",chart))
            st.download_button("⬇️ Download Performance Chart (PDF)",chart,generated[-1][0],"application/pdf",key="rr_chart_pdf")
    if all_m:
        # Build a complete report pack for this student/year.
        if not generated:
            generated=[]
        term_rows=[]
        for term in (1,2,3):
            mr=db.get_marks_for_student(stu["reg_no"],year=yr,term=term)
            if mr:
                pl,sm,re=_career_ai_for_report(stu,mr)
                term_rows.append((f"{stu['reg_no']}_T{term}_{yr}.pdf",pdf_report.student_term_report(stu,term,yr,mr,pl,sm,re)))
        piv,sta=pivot_marks(all_m); ov=round(piv["average"].mean(),2); pl,sm,_=_career_ai_for_report(stu,all_m)
        pack=term_rows+[(f"{stu['reg_no']}_{yr}_annual.pdf",pdf_report.student_year_report(stu,yr,sta,ov,pl,sm)),
                        (f"{stu['reg_no']}_{yr}_performance_chart.pdf",pdf_report.student_performance_report(stu,yr,all_m))]
        st.download_button("📦 Download Complete Student Report Pack (ZIP)",_zip_files(pack),f"{stu['reg_no']}_{yr}_reports.zip","application/zip",key="student_report_pack")


def render_exam_results_admin(user):
    banner("🧾","Official O/L & A/L Results","Record actual examination grades and forecast school outcomes")
    st.info("Enter official subject grades for each examination year. A/B/C/S are treated as passes; W is treated as a fail.")
    students=db.get_all_students()
    if not students: st.warning("Add students first."); return
    opts={f"{s['reg_no']} – {s['full_name']} (G{s['grade']}{s['class_section']})":s for s in students}
    c1,c2,c3=st.columns(3)
    sel=c1.selectbox("Student",list(opts.keys()),key="exam_student")
    stu=opts[sel]; exam_type=c2.selectbox("Exam",["O/L","A/L"],key="exam_type")
    exam_year=int(c3.number_input("Exam Year",2020,2035,datetime.date.today().year,key="exam_year"))
    stream_id=stu.get("stream_id") or db.get_stream_id("General")
    subs=db.get_subjects_by_stream(stream_id) if stream_id else db.get_all_subjects()
    if not subs: st.warning("No subjects available."); return
    existing={r["subject_id"]:r["result_grade"] for r in db.get_exam_results(stu["reg_no"],exam_type,exam_year)}
    with st.form("exam_result_form"):
        cols=st.columns(2); vals={}
        for i,sub in enumerate(subs):
            with cols[i%2]: vals[sub["id"]]=st.selectbox(sub["name"],["—","A","B","C","S","W"],index=(["—","A","B","C","S","W"].index(existing.get(sub["id"],"—"))),key=f"ex_{exam_type}_{exam_year}_{sub['id']}")
        if st.form_submit_button("Save Official Results"):
            saved=0
            for sid,grade in vals.items():
                if grade!="—": db.save_exam_result(stu["reg_no"],exam_type,exam_year,sid,grade); saved+=1
            log_activity(user["id"],f"saved {exam_type} results for {stu['reg_no']} {exam_year}")
            st.success(f"Saved {saved} result(s)."); st.rerun()
    current=db.get_exam_results(stu["reg_no"],exam_type,exam_year)
    if current: st.dataframe(pd.DataFrame(current)[["subject_name","result_grade"]].rename(columns={"subject_name":"Subject","result_grade":"Grade"}),width="stretch",hide_index=True)

    st.markdown("---"); st.subheader("School Forecast")
    hist=db.get_exam_results(exam_type=exam_type)
    target=exam_year+1
    internal=db.get_marks_for_grades((10,11) if exam_type=="O/L" else (12,13), year=exam_year)
    forecast=pai.forecast_exam_pass_rate(hist,internal,target)
    school_years=db.get_school_exam_year_rates(exam_type)
    stats=db.get_school_exam_pass_stats(exam_type)
    c1,c2,c3=st.columns(3); c1.metric(f"Current Historical {exam_type} Pass Rate",f"{stats['pass_rate']}%" if stats['pass_rate'] is not None else "—"); c2.metric(f"Next-Year {exam_type} Estimate",f"{forecast['pass_rate']}%" if forecast['pass_rate'] is not None else "—"); c3.metric("Confidence",forecast["confidence"])
    if school_years: st.dataframe(pd.DataFrame(school_years).rename(columns={"exam_year":"Year","total":"Results","passed":"Passed","pass_rate":"Pass Rate %"}),width="stretch",hide_index=True)
    if forecast.get("pass_rate") is not None: st.caption(f"Method: {forecast['method']}. Planning estimate only; not an official prediction.")


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    user=get_session_user()
    if not user:
        login_screen()
    elif user["role"]=="admin":
        admin_dashboard()
    elif user["role"]=="teacher":
        teacher_dashboard()
    elif user["role"]=="student":
        # Accounts generated by Excel bulk import must complete secure onboarding
        # before accessing academic records.
        if user.get("must_change_password"):
            student_first_login_setup(user)
        else:
            student_dashboard()
    else:
        st.error("Unknown role."); clear_session()

if __name__=="__main__":
    main()

