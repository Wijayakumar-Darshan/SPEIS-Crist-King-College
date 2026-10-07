"""
ui.py – SPEIS design system.

All look-and-feel lives here: theme CSS, matplotlib chart style and small
reusable HTML components. Business logic stays in app.py / database.py.
"""
import html
import streamlit as st
import matplotlib

# ── Palette ───────────────────────────────────────────────────────────────────
PRIMARY = "#4f46e5"     # indigo
PRIMARY_DK = "#3730a3"
ACCENT = "#06b6d4"      # cyan
WARM = "#f59e0b"        # amber
GOOD = "#10b981"
BAD = "#ef4444"
INK = "#0f172a"
MUTED = "#64748b"
LINE = "#e2e8f0"
CHART_COLORS = [PRIMARY, WARM, ACCENT, GOOD, "#ec4899", "#8b5cf6", "#14b8a6", "#f97316"]

_CSS = """
<style>
/* ============================================================
   SPEIS SCHOOL DESIGN SYSTEM — v2
   Clean, calm, modern and school-administration friendly.
   ============================================================ */

:root{
  --navy:#10233f;
  --navy-2:#17365f;
  --blue:#2563eb;
  --blue-2:#1d4ed8;
  --teal:#0f9f9a;
  --green:#159570;
  --amber:#d98b18;
  --red:#dc4b4b;
  --ink:#172033;
  --muted:#68758a;
  --line:#e5eaf1;
  --bg:#f4f7fb;
  --card:#ffffff;
  --radius:16px;
  --shadow:0 6px 24px rgba(16,35,63,.07);
  --shadow-sm:0 2px 10px rgba(16,35,63,.055);
}

html,body,[class*="css"],.stApp{
  font-family:Inter,ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;
  color:var(--ink);
}
.stApp{
  background:
    radial-gradient(800px 300px at 95% -5%,rgba(37,99,235,.075),transparent 65%),
    linear-gradient(180deg,#f8fafc 0%,var(--bg) 55%,#f3f6fa 100%);
}
h1,h2,h3,h4{
  font-family:Inter,ui-sans-serif,system-ui,sans-serif;
  color:var(--ink);
  letter-spacing:-.018em;
}
h1{font-weight:800}
h2{font-size:1.42rem;font-weight:750}
h3{font-weight:700}
.block-container{
  padding-top:1.65rem;
  padding-bottom:3rem;
  max-width:none;
  width:100%;
  padding-left:2rem;
  padding-right:2rem;
}

/* Premium workspace shell */
[data-testid="stAppViewContainer"]{background:transparent!important}
[data-testid="stMainBlockContainer"]{max-width:none!important}
[data-testid="stSidebarCollapsedControl"]{display:flex!important;position:fixed!important;left:12px!important;top:72px!important;z-index:999999!important}
[data-testid="stSidebarCollapsedControl"] button{width:42px!important;height:42px!important;border-radius:12px!important;background:#0b2341!important;color:#fff!important;border:1px solid rgba(255,255,255,.14)!important;box-shadow:0 8px 24px rgba(2,12,27,.22)!important}
[data-testid="stSidebarCollapsedControl"] button:hover{background:#163f6c!important}
[data-testid="stSidebarNav"]{display:none!important}
.stColumn{min-width:0!important}
div[data-testid="stVerticalBlock"]{min-width:0}

/* Hide Streamlit chrome but retain the sidebar toggle. */
#MainMenu,footer,[data-testid="stToolbar"],[data-testid="stDeployButton"]{
  display:none!important;
}
header[data-testid="stHeader"]{
  background:rgba(248,250,252,.84);
  backdrop-filter:blur(12px);
}

/* ============================================================
   SIDEBAR — DARK PROFESSIONAL SCHOOL NAVIGATION
   Uses Streamlit's real radio controls; CSS only changes presentation.
   ============================================================ */
section[data-testid="stSidebar"]{
  background:linear-gradient(180deg,#071a33 0%,#0a2342 55%,#081a31 100%);
  border-right:1px solid rgba(255,255,255,.08);
  box-shadow:8px 0 30px rgba(2,12,27,.22);
  min-width:310px;
  max-width:310px;
}
section[data-testid="stSidebar"] > div:first-child{
  padding:22px 16px 24px;
}
section[data-testid="stSidebar"] *{box-sizing:border-box}
section[data-testid="stSidebar"] hr{
  border:0;
  border-top:1px solid rgba(255,255,255,.09);
  margin:14px 6px;
}

/* Brand */
.sb-brand{
  display:flex;
  align-items:center;
  gap:12px;
  padding:4px 7px 17px;
}
.sb-logo{
  width:45px;height:45px;flex:0 0 45px;
  display:grid;place-items:center;
  border-radius:13px;
  font-size:21px;color:#fff;
  background:linear-gradient(145deg,#1d4ed8,#0891b2);
  border:1px solid rgba(255,255,255,.14);
  box-shadow:0 9px 22px rgba(0,0,0,.25);
}
.sb-brand b{
  display:block;color:#fff;
  font-size:18px;line-height:1.05;
  letter-spacing:.02em;font-weight:800;
}
.sb-brand small{
  display:block;margin-top:4px;
  color:#8ea7c4;font-size:9.5px;line-height:1.2;
  letter-spacing:.065em;text-transform:uppercase;font-weight:650;
}

/* User profile */
.sb-user{
  display:flex;align-items:center;gap:10px;
  padding:11px;
  border:1px solid rgba(255,255,255,.09);
  border-radius:14px;
  background:rgba(255,255,255,.055);
  box-shadow:inset 0 1px 0 rgba(255,255,255,.035);
}
.sb-avatar{
  width:40px;height:40px;flex:0 0 40px;
  display:grid;place-items:center;
  border-radius:12px;color:#fff;
  font-weight:800;font-size:13px;
  background:linear-gradient(145deg,#2563eb,#0891b2);
  box-shadow:0 6px 14px rgba(0,0,0,.22);
}
.sb-user .n{
  color:#fff;font-weight:750;font-size:13px;line-height:1.2;
  overflow:hidden;text-overflow:ellipsis;white-space:nowrap;
}
.sb-user .r{color:#8fa8c4;font-size:11px;margin-top:3px}
.sb-label{
  color:#6f8aa8;font-size:9.5px;font-weight:800;
  letter-spacing:.14em;text-transform:uppercase;
  margin:19px 8px 8px;
}

/* Button-based navigation: stable across Streamlit releases */
section[data-testid="stSidebar"] .sb-nav-title{
  margin-top:18px!important;
  margin-bottom:8px!important;
}
section[data-testid="stSidebar"] .stButton{
  width:100%!important;
  margin:0 0 6px 0!important;
}
section[data-testid="stSidebar"] .stButton > button{
  width:100%!important;
  min-height:46px!important;
  justify-content:flex-start!important;
  text-align:left!important;
  padding:0 13px!important;
  border-radius:11px!important;
  border:1px solid rgba(255,255,255,.055)!important;
  background:rgba(255,255,255,.025)!important;
  color:#b9c9dc!important;
  font-size:12.5px!important;
  font-weight:600!important;
  box-shadow:none!important;
  transition:all .16s ease!important;
}
section[data-testid="stSidebar"] .stButton > button:hover{
  background:rgba(255,255,255,.075)!important;
  border-color:rgba(96,165,250,.18)!important;
  color:#fff!important;
  transform:translateX(2px)!important;
}
section[data-testid="stSidebar"] .stButton > button[kind="primary"]{
  color:#fff!important;
  font-weight:750!important;
  background:linear-gradient(90deg,rgba(37,99,235,.34),rgba(8,145,178,.13))!important;
  border-color:rgba(96,165,250,.28)!important;
  box-shadow:inset 3px 0 0 #60a5fa,0 5px 14px rgba(0,0,0,.10)!important;
}

/* Sidebar footer / scrollbar */
section[data-testid="stSidebar"] .sb-footer{margin-top:18px;padding:11px 12px;border-top:1px solid rgba(255,255,255,.08);color:#6f8aa8;font-size:10px;line-height:1.5}

/* Sign-out */
.sb-signout .stButton{margin-top:10px!important}
.sb-signout .stButton > button{min-height:43px!important;border:1px solid rgba(248,113,113,.16)!important;background:rgba(220,72,72,.07)!important;color:#c8d5e5!important;border-radius:11px!important;box-shadow:none!important;font-size:12px!important;font-weight:700!important}
.sb-signout .stButton > button:hover{color:#fff!important;background:rgba(220,72,72,.17)!important;border-color:rgba(248,113,113,.3)!important;box-shadow:none!important;transform:none!important}

section[data-testid="stSidebar"] > div:first-child::-webkit-scrollbar{width:5px}
section[data-testid="stSidebar"] > div:first-child::-webkit-scrollbar-thumb{
  background:#284665;border-radius:99px;
}

/* ============================================================
   PAGE HEADER
   ============================================================ */
.page-head{
  position:relative;
  overflow:hidden;
  display:flex;
  align-items:center;
  min-height:126px;
  padding:20px 24px;
  margin-bottom:20px;
  border:1px solid rgba(255,255,255,.12);
  border-radius:22px;
  color:#fff;
  background:linear-gradient(120deg,#102d50 0%,#174b7e 58%,#167f83 100%);
  box-shadow:0 16px 38px rgba(16,35,63,.14);
}
.page-head::before{
  content:"";
  position:absolute;
  width:300px;height:300px;
  right:-90px;top:-135px;
  border-radius:50%;
  border:45px solid rgba(255,255,255,.055);
}
.page-head::after{
  content:"";
  position:absolute;
  width:150px;height:150px;
  right:125px;bottom:-105px;
  border-radius:50%;
  background:rgba(255,255,255,.045);
}
.page-head .ph-row{
  display:flex;
  align-items:center;
  gap:14px;
  position:relative;
  z-index:2;
}
.page-head .ph-ico{
  width:54px;height:54px;
  flex:0 0 54px;
  display:grid;
  place-items:center;
  border:1px solid rgba(255,255,255,.18);
  border-radius:15px;
  font-size:23px;
  background:rgba(255,255,255,.105);
  backdrop-filter:blur(8px);
}
.page-head h1{
  color:#fff!important;
  margin:0;
  font-size:1.55rem;
  line-height:1.18;
}
.page-head p{
  color:rgba(255,255,255,.78);
  margin:5px 0 0;
  font-size:.87rem;
}

/* ============================================================
   CARDS / STATS
   ============================================================ */
.card{
  background:var(--card);
  border:1px solid var(--line);
  border-radius:var(--radius);
  padding:18px 19px;
  margin-bottom:14px;
  box-shadow:var(--shadow-sm);
}
.card h4{
  margin:0 0 10px;
  color:var(--navy);
  font-size:14px;
  font-weight:750;
}
.kv{
  display:flex;
  justify-content:space-between;
  gap:16px;
  padding:9px 0;
  border-bottom:1px dashed #e8edf3;
  font-size:13px;
}
.kv:last-child{border-bottom:none}
.kv span:first-child{color:var(--muted)}
.kv span:last-child{color:var(--ink);font-weight:650;text-align:right}

.stat-grid{
  display:grid;
  grid-template-columns:repeat(4,minmax(0,1fr));
  gap:16px;
  margin:2px 0 22px;
}
.stat{
  position:relative;
  overflow:hidden;
  background:#fff;
  border:1px solid var(--line);
  border-radius:15px;
  padding:18px;
  box-shadow:var(--shadow-sm);
  transition:transform .18s ease,box-shadow .18s ease;
}
.stat:hover{transform:translateY(-2px);box-shadow:var(--shadow)}
.stat::before{
  content:"";
  position:absolute;
  left:0;top:0;bottom:0;
  width:3px;
  background:var(--c,#2563eb);
}
.stat .ico{
  width:36px;height:36px;
  display:grid;place-items:center;
  border-radius:10px;
  margin-bottom:10px;
  background:#f0f5ff;
  font-size:17px;
}
.stat .lbl{color:#718096;font-size:11px;font-weight:650}
.stat .val{
  color:var(--navy);
  font-size:23px;
  font-weight:800;
  line-height:1.15;
  margin-top:2px;
}
.stat .hint{color:#8a95a6;font-size:10.5px;margin-top:4px}

div[data-testid="stMetric"]{
  background:#fff;
  border:1px solid var(--line);
  border-radius:14px;
  padding:12px 15px;
  box-shadow:var(--shadow-sm);
}
div[data-testid="stMetric"] label{color:var(--muted)!important;font-size:11px!important}
div[data-testid="stMetricValue"]{color:var(--navy)!important;font-weight:800}

.section-title{
  display:flex;
  align-items:center;
  gap:8px;
  margin:22px 0 10px;
  color:var(--navy);
  font-size:15px;
  font-weight:750;
}
.section-title::after{
  content:"";
  flex:1;
  height:1px;
  background:#e4e9f0;
}

.pill{
  display:inline-block;
  padding:4px 9px;
  border-radius:999px;
  font-size:10.5px;
  font-weight:700;
  margin:1px 2px;
}
.pill.good{background:#e7f7f1;color:#087653}
.pill.warn{background:#fff4df;color:#9a6500}
.pill.bad{background:#ffebeb;color:#b42c2c}
.pill.info{background:#eaf1ff;color:#2456a6}

.empty{
  text-align:center;
  padding:36px 18px;
  color:var(--muted);
  background:#fff;
  border:1.5px dashed #dce3ec;
  border-radius:15px;
}
.empty .e-ico{font-size:30px;margin-bottom:5px}

/* ============================================================
   FORMS / CONTROLS
   ============================================================ */
div[data-testid="stForm"]{
  background:#fff;
  padding:20px;
  border:1px solid var(--line);
  border-radius:16px;
  box-shadow:var(--shadow-sm);
}
div[data-testid="stExpander"]{
  background:#fff;
  border:1px solid var(--line);
  border-radius:14px;
  box-shadow:var(--shadow-sm);
  overflow:hidden;
}
div[data-testid="stExpander"] summary{
  font-weight:700;
  color:var(--navy);
}
div[data-baseweb="input"],
div[data-baseweb="select"]>div,
div[data-baseweb="textarea"]{
  border-radius:10px!important;
  border-color:#dce3ec!important;
  background:#fff!important;
}
div[data-baseweb="input"]:focus-within,
div[data-baseweb="select"]>div:focus-within{
  box-shadow:0 0 0 3px rgba(37,99,235,.11)!important;
  border-color:#7ca6e8!important;
}
.stTextInput label,.stSelectbox label,.stNumberInput label,
.stMultiSelect label,.stTextArea label,.stDateInput label{
  color:#526176!important;
  font-weight:650!important;
  font-size:11.5px!important;
}
.stButton>button,.stFormSubmitButton>button{
  min-height:40px;
  color:#fff!important;
  border:0!important;
  border-radius:10px!important;
  background:linear-gradient(135deg,#2563eb,#1d4ed8)!important;
  font-weight:700!important;
  box-shadow:0 5px 13px rgba(37,99,235,.18)!important;
  transition:transform .15s ease,box-shadow .15s ease!important;
}
.stButton>button:hover,.stFormSubmitButton>button:hover{
  transform:translateY(-1px)!important;
  box-shadow:0 8px 18px rgba(37,99,235,.25)!important;
}
.stDownloadButton>button{
  min-height:40px;
  color:#fff!important;
  border:0!important;
  border-radius:10px!important;
  background:linear-gradient(135deg,#159570,#08795d)!important;
  font-weight:700!important;
}
div[data-baseweb="tab-list"]{
  gap:4px;
  padding:4px;
  border:1px solid #e4e9f0;
  border-radius:11px;
  background:#eef2f7;
  max-width:100%;
  overflow-x:auto;
}
button[data-baseweb="tab"]{
  border-radius:8px!important;
  padding:7px 13px!important;
  font-size:12px!important;
  font-weight:650!important;
}
button[data-baseweb="tab"][aria-selected="true"]{
  background:#fff!important;
  color:#1d4ed8!important;
  box-shadow:0 2px 7px rgba(16,35,63,.08)!important;
}
div[data-baseweb="tab-highlight"],div[data-baseweb="tab-border"]{display:none}

div[data-testid="stAlert"]{
  border-radius:12px;
  border:1px solid rgba(16,35,63,.06);
  box-shadow:var(--shadow-sm);
}
div[data-testid="stDataFrame"]{
  border:1px solid var(--line);
  border-radius:14px;
  overflow:hidden;
  box-shadow:var(--shadow-sm);
}
div[data-testid="stFileUploader"] section{
  border:1.5px dashed #a9c5ed;
  border-radius:14px;
  background:#f5f9ff;
}
div[data-testid="stImage"] img,.stPyplot img{border-radius:12px}
div[data-testid="stPyplot"]{
  background:#fff;
  border:1px solid var(--line);
  border-radius:15px;
  padding:7px;
  box-shadow:var(--shadow-sm);
}

/* ============================================================
   DATA TABLES / CHARTS / CONTENT SURFACES
   ============================================================ */
div[data-testid="stDataFrame"]{margin:8px 0 18px!important;background:#fff!important;border:1px solid #dfe6ef!important;border-radius:16px!important;box-shadow:0 8px 24px rgba(16,35,63,.06)!important}
div[data-testid="stDataFrame"] > div{border-radius:16px!important}
div[data-testid="stDataFrame"] iframe{border-radius:16px!important}
.stPyplot{margin:6px 0 18px!important}
.stPyplot img{display:block!important;width:100%!important;height:auto!important}
div[data-testid="stHorizontalBlock"]{gap:18px!important}
.stCaption{color:#7a8799!important}
.stMarkdown p{line-height:1.55}
button[kind="secondary"]{border:1px solid #d9e1ec!important;background:#fff!important;color:#334155!important;box-shadow:0 3px 10px rgba(16,35,63,.05)!important}
button[kind="secondary"]:hover{border-color:#9db7d7!important;background:#f7faff!important}

/* ============================================================
   LOGIN
   ============================================================ */
.login-hero{
  position:relative;
  overflow:hidden;
  min-height:470px;
  padding:38px;
  border-radius:22px;
  color:#fff;
  background:linear-gradient(145deg,#102d50,#174b7e 62%,#167f83);
  box-shadow:0 14px 34px rgba(16,35,63,.13);
}
.login-hero::after{
  content:"";
  position:absolute;
  right:-90px;bottom:-100px;
  width:330px;height:330px;
  border-radius:50%;
  border:55px solid rgba(255,255,255,.055);
}
.login-hero .logo{
  width:58px;height:58px;
  display:grid;place-items:center;
  border-radius:17px;
  background:rgba(255,255,255,.12);
  border:1px solid rgba(255,255,255,.14);
  font-size:25px;
  margin-bottom:22px;
}
.login-hero h1{
  color:#fff!important;
  font-size:2rem;
  line-height:1.13;
  margin:0 0 9px;
}
.login-hero p{
  color:rgba(255,255,255,.78);
  font-size:.94rem;
  margin:0 0 22px;
}
.feat{
  display:flex;
  align-items:flex-start;
  gap:10px;
  margin:11px 0;
  position:relative;
  z-index:1;
}
.feat i{
  width:33px;height:33px;
  flex:0 0 33px;
  display:grid;place-items:center;
  border-radius:10px;
  background:rgba(255,255,255,.105);
  font-style:normal;
}
.feat b{display:block;font-size:12.5px}
.feat span{display:block;font-size:10.5px;color:rgba(255,255,255,.65);margin-top:2px}
.login-title{
  color:var(--navy);
  font-weight:800;
  font-size:1.45rem;
  margin:.25rem 0 .1rem;
}
.login-sub{color:var(--muted);font-size:.86rem;margin-bottom:8px}

@media (max-width:1100px){
  section[data-testid="stSidebar"]{
    min-width:285px;
    max-width:285px;
  }
  .stat-grid{grid-template-columns:repeat(2,minmax(0,1fr));}
}
@media (max-width:900px){
  .page-head{min-height:96px;padding:17px 18px}
  .page-head h1{font-size:1.3rem}
}
/* ============================================================
   MOBILE RESPONSIVE — SPEIS
   UI ONLY — NO APPLICATION LOGIC CHANGES
   ============================================================ */

/* Tablets / small laptops */
@media (max-width:1100px){
  .block-container{
    padding-left:1.25rem;
    padding-right:1.25rem;
  }

  .stat-grid{
    grid-template-columns:repeat(2,minmax(0,1fr));
  }
}

/* ============================================================
   TABLET / MOBILE
   ============================================================ */
@media (max-width:768px){

  /* Main page spacing */
  .block-container{
    padding-top:1rem!important;
    padding-left:12px!important;
    padding-right:12px!important;
    padding-bottom:2rem!important;
  }

  /* Sidebar */
  section[data-testid="stSidebar"]{
    min-width:85vw!important;
    max-width:85vw!important;
    width:85vw!important;
  }

  section[data-testid="stSidebar"] > div:first-child{
    padding:18px 13px 20px!important;
  }

  /* Sidebar buttons */
  section[data-testid="stSidebar"] .stButton > button{
    min-height:44px!important;
    font-size:12px!important;
    padding:0 11px!important;
  }

  /* Main page header */
  .page-head{
    min-height:auto!important;
    padding:17px 16px!important;
    margin-bottom:15px!important;
    border-radius:16px!important;
  }

  .page-head .ph-row{
    gap:10px!important;
    align-items:flex-start!important;
  }

  .page-head .ph-ico{
    width:44px!important;
    height:44px!important;
    flex:0 0 44px!important;
    border-radius:12px!important;
    font-size:19px!important;
  }

  .page-head h1{
    font-size:1.15rem!important;
    line-height:1.25!important;
  }

  .page-head p{
    font-size:.75rem!important;
    line-height:1.4!important;
    margin-top:4px!important;
  }

  /* ==========================================================
     STREAMLIT COLUMNS
     Stack columns vertically on mobile.
     ========================================================== */

  [data-testid="stHorizontalBlock"]{
    flex-wrap:wrap!important;
    gap:0.75rem!important;
  }

  [data-testid="stHorizontalBlock"] > [data-testid="column"]{
    width:100%!important;
    min-width:100%!important;
    max-width:100%!important;
    flex:1 1 100%!important;
  }

  /* ==========================================================
     STAT CARDS
     ========================================================== */

  .stat-grid{
    grid-template-columns:repeat(2,minmax(0,1fr))!important;
    gap:9px!important;
    margin-bottom:16px!important;
  }

  .stat{
    padding:13px!important;
    border-radius:13px!important;
  }

  .stat .ico{
    width:31px!important;
    height:31px!important;
    font-size:15px!important;
    margin-bottom:7px!important;
  }

  .stat .lbl{
    font-size:9.5px!important;
  }

  .stat .val{
    font-size:19px!important;
  }

  .stat .hint{
    font-size:9px!important;
  }

  /* Streamlit metrics */
  div[data-testid="stMetric"]{
    padding:10px 12px!important;
    border-radius:12px!important;
  }

  div[data-testid="stMetric"] label{
    font-size:10px!important;
  }

  div[data-testid="stMetricValue"]{
    font-size:1.25rem!important;
  }

  /* ==========================================================
     CARDS
     ========================================================== */

  .card{
    padding:14px!important;
    border-radius:13px!important;
    margin-bottom:11px!important;
  }

  .card h4{
    font-size:13px!important;
  }

  .kv{
    gap:10px!important;
    font-size:11.5px!important;
    padding:8px 0!important;
  }

  .kv span:first-child{
    flex:0 0 auto;
  }

  .kv span:last-child{
    max-width:60%;
    overflow-wrap:anywhere;
  }

  /* ==========================================================
     SECTION TITLES
     ========================================================== */

  .section-title{
    margin:18px 0 9px!important;
    font-size:13px!important;
    gap:6px!important;
  }

  /* ==========================================================
     FORMS
     ========================================================== */

  div[data-testid="stForm"]{
    padding:14px!important;
    border-radius:13px!important;
  }

  /* All normal controls should use full mobile width */
  div[data-testid="stTextInput"],
  div[data-testid="stTextArea"],
  div[data-testid="stNumberInput"],
  div[data-testid="stSelectbox"],
  div[data-testid="stMultiSelect"],
  div[data-testid="stDateInput"],
  div[data-testid="stFileUploader"]{
    width:100%!important;
  }

  /* Buttons */
  div.stButton > button,
  div[data-testid="stFormSubmitButton"] > button,
  div[data-testid="stDownloadButton"] > button{
    width:100%!important;
    min-height:44px!important;
    font-size:12px!important;
  }

  /* ==========================================================
     TABS
     ========================================================== */

  [data-baseweb="tab-list"]{
    overflow-x:auto!important;
    overflow-y:hidden!important;
    flex-wrap:nowrap!important;
    -webkit-overflow-scrolling:touch!important;
    scrollbar-width:none!important;
  }

  [data-baseweb="tab-list"]::-webkit-scrollbar{
    display:none!important;
  }

  [data-baseweb="tab"]{
    white-space:nowrap!important;
    flex:0 0 auto!important;
    font-size:12px!important;
    padding-left:12px!important;
    padding-right:12px!important;
  }

  /* ==========================================================
     DATA TABLES
     ========================================================== */

  div[data-testid="stDataFrame"],
  div[data-testid="stTable"]{
    width:100%!important;
    max-width:100%!important;
    overflow-x:auto!important;
    -webkit-overflow-scrolling:touch!important;
  }

  /* Prevent long text from destroying the layout */
  table{
    font-size:11px!important;
  }

  /* ==========================================================
     EXPANDERS
     ========================================================== */

  div[data-testid="stExpander"]{
    border-radius:12px!important;
  }

  div[data-testid="stExpander"] summary{
    font-size:12px!important;
  }

  /* ==========================================================
     ALERTS
     ========================================================== */

  div[data-testid="stAlert"]{
    font-size:12px!important;
    border-radius:11px!important;
  }

  /* ==========================================================
     IMAGES / CHARTS
     ========================================================== */

  img{
    max-width:100%!important;
    height:auto!important;
  }

  div[data-testid="stImage"],
  div[data-testid="stPyplot"]{
    width:100%!important;
    max-width:100%!important;
    overflow:hidden!important;
  }

  /* ==========================================================
     LOGIN SCREEN
     ========================================================== */

  .login-hero{
    min-height:auto!important;
    padding:24px 18px!important;
    border-radius:16px!important;
  }

  .login-hero h1{
    font-size:1.35rem!important;
    line-height:1.25!important;
  }

  .login-sub{
    font-size:.78rem!important;
  }

  .login-title{
    font-size:1.3rem!important;
  }

  .feat{
    gap:8px!important;
    margin:9px 0!important;
  }

  .feat i{
    width:30px!important;
    height:30px!important;
    flex:0 0 30px!important;
  }

  .feat b{
    font-size:11.5px!important;
  }

  .feat span{
    font-size:9.5px!important;
  }

  /* Radio buttons */
  div[data-testid="stRadio"] label{
    font-size:11px!important;
  }

  /* Captions */
  .stCaption,
  [data-testid="stCaptionContainer"]{
    font-size:10px!important;
  }
}

/* ============================================================
   VERY SMALL PHONES
   ============================================================ */
@media (max-width:480px){

  .block-container{
    padding-left:9px!important;
    padding-right:9px!important;
  }

  /* One stat card per row on very small screens */
  .stat-grid{
    grid-template-columns:1fr!important;
    gap:8px!important;
  }

  .stat{
    padding:12px!important;
  }

  .page-head{
    padding:14px!important;
  }

  .page-head .ph-ico{
    width:40px!important;
    height:40px!important;
    flex-basis:40px!important;
    font-size:17px!important;
  }

  .page-head h1{
    font-size:1rem!important;
  }

  .page-head p{
    font-size:.7rem!important;
  }

  .card{
    padding:12px!important;
  }

  .section-title{
    font-size:12px!important;
  }

  /* Smaller mobile inputs */
  input,
  textarea,
  select{
    font-size:12px!important;
  }

  /* Keep long values inside cards */
  .kv{
    flex-direction:column!important;
    gap:3px!important;
  }

  .kv span:last-child{
    max-width:100%!important;
    text-align:left!important;
  }
}
</style>
"""


def inject_css():
    st.markdown(_CSS, unsafe_allow_html=True)


def style_matplotlib():
    """Clean, modern default look for every matplotlib chart in the app."""
    matplotlib.rcParams.update({
        "figure.facecolor": "white", "axes.facecolor": "white",
        "axes.edgecolor": LINE, "axes.labelcolor": MUTED, "axes.titlecolor": INK,
        "axes.titleweight": "bold", "axes.titlesize": 11, "axes.titlelocation": "left",
        "axes.spines.top": False, "axes.spines.right": False,
        "axes.grid": True, "grid.color": "#eef2f7", "grid.linewidth": .9, "axes.axisbelow": True,
        "xtick.color": MUTED, "ytick.color": MUTED, "font.size": 9,
        "legend.frameon": False, "axes.prop_cycle": matplotlib.cycler(color=CHART_COLORS),
        "figure.dpi": 110,
    })


# ── Components ────────────────────────────────────────────────────────────────
def _e(x):
    return html.escape(str(x))


def page_header(icon, title, sub=""):
    st.markdown(
        f'<div class="page-head"><div class="ph-row"><div class="ph-ico">{icon}</div>'
        f'<div><h1>{_e(title)}</h1><p>{_e(sub)}</p></div></div></div>',
        unsafe_allow_html=True)


def section(title, icon=""):
    st.markdown(f'<div class="section-title">{icon} {_e(title)}</div>', unsafe_allow_html=True)


def stat_cards(items):
    """items: list of (label, value, icon, hint, color_hex). hint/color optional."""
    out = ['<div class="stat-grid">']
    for it in items:
        label, value, icon = it[0], it[1], it[2]
        hint = it[3] if len(it) > 3 else ""
        color = it[4] if len(it) > 4 else PRIMARY
        out.append(
            f'<div class="stat" style="--c:{color}"><div class="ico">{icon}</div>'
            f'<div class="lbl">{_e(label)}</div><div class="val">{_e(value)}</div>'
            f'<div class="hint">{_e(hint)}</div></div>')
    out.append('</div>')
    st.markdown("".join(out), unsafe_allow_html=True)


def kv_card(title, rows):
    """rows: list of (label, value)."""
    body = "".join(f'<div class="kv"><span>{_e(k)}</span><span>{_e(v)}</span></div>' for k, v in rows)
    st.markdown(f'<div class="card"><h4>{_e(title)}</h4>{body}</div>', unsafe_allow_html=True)


def empty_state(icon, text):
    st.markdown(f'<div class="empty"><div class="e-ico">{icon}</div>{_e(text)}</div>', unsafe_allow_html=True)


def pill(text, kind="info"):
    return f'<span class="pill {kind}">{_e(text)}</span>'


def sidebar_collapsed():
    """Return the current SPEIS sidebar collapsed state."""
    return bool(st.session_state.get("speis_sidebar_collapsed", False))


def sidebar_brand():
    """Render the SPEIS sidebar header and full-sidebar collapse control."""
    if "speis_sidebar_collapsed" not in st.session_state:
        st.session_state.speis_sidebar_collapsed = False

    collapsed = bool(st.session_state.speis_sidebar_collapsed)
    toggle_icon = "▶" if collapsed else "◀"
    toggle_help = "Expand sidebar" if collapsed else "Minimize sidebar"

    # The state marker is deliberately placed INSIDE the real Streamlit
    # sidebar. CSS uses :has(...) to resize the complete sidebar section.
    sidebar_class = (
        "speis-sidebar-collapsed"
        if collapsed
        else "speis-sidebar-expanded"
    )

    st.sidebar.markdown(
        f'<div class="speis-sidebar-state {sidebar_class}"></div>',
        unsafe_allow_html=True,
    )

    # Small floating-style control inside the sidebar.
    st.sidebar.markdown(
        '<div class="sb-toggle-wrap">',
        unsafe_allow_html=True,
    )

    if st.sidebar.button(
        toggle_icon,
        key="speis_sidebar_toggle",
        help=toggle_help,
    ):
        st.session_state.speis_sidebar_collapsed = not collapsed
        st.rerun()

    st.sidebar.markdown(
        '</div>',
        unsafe_allow_html=True,
    )

    # Existing SPEIS brand.
    st.sidebar.markdown(
        '<div class="sb-brand">'
        '<div class="sb-logo">🎓</div>'
        '<div class="sb-brand-text">'
        '<b>SPEIS</b>'
        '<small>School Intelligence Suite</small>'
        '</div>'
        '</div>',
        unsafe_allow_html=True,
    )


def sidebar_user_chip(name, role_label):
    initials = "".join(
        w[0] for w in str(name).split()[:2]
    ).upper() or "?"

    st.sidebar.markdown(
        f'<div class="sb-user">'
        f'<div class="sb-avatar">{_e(initials)}</div>'
        f'<div class="sb-user-text">'
        f'<div class="n">{_e(name)}</div>'
        f'<div class="r">{_e(role_label)}</div>'
        f'</div>'
        f'</div>',
        unsafe_allow_html=True
    )


def sidebar_nav(options, key="speis_nav"):
    """Responsive SPEIS sidebar navigation.

    The actual page values remain unchanged.
    Only the displayed label changes when the sidebar is minimized.
    """

    if not options:
        return ""

    if key not in st.session_state or st.session_state[key] not in options:
        st.session_state[key] = options[0]

    collapsed = sidebar_collapsed()

    st.sidebar.markdown(
        '<div class="sb-label sb-nav-title">Navigation</div>',
        unsafe_allow_html=True
    )

    for i, option in enumerate(options):

        active = st.session_state[key] == option

        # Keep the original page value.
        # Only display the icon when collapsed.
        icon = option.split(" ", 1)[0] if " " in option else option
        display_label = icon if collapsed else option

        clicked = st.sidebar.button(
            display_label,
            key=f"{key}_{i}",
            width="stretch",
            type="primary" if active else "secondary",
            help=option if collapsed else None,
        )

        if clicked and st.session_state[key] != option:
            st.session_state[key] = option
            st.rerun()

    return st.session_state[key]

def login_hero():
    st.markdown("""
<div class="login-hero">
  <div class="logo">🎓</div>
  <h1>Student Performance &amp; Educational Intelligence</h1>
  <p>A digital assessment platform built for Sri Lankan schools.</p>
  <div class="feat"><i>📊</i><div><b>Marks &amp; analytics</b><span>Term, annual and class-wise insight</span></div></div>
  <div class="feat"><i>🎯</i><div><b>Career readiness</b><span>Track progress against career cut-offs</span></div></div>
  <div class="feat"><i>🔮</i><div><b>O/L &amp; A/L forecasts</b><span>Lightweight planning estimates</span></div></div>
  <div class="feat"><i>📄</i><div><b>Instant PDF reports</b><span>Generated securely in memory</span></div></div>
</div>""", unsafe_allow_html=True)
"""
ui.py – SPEIS design system.

All look-and-feel lives here: theme CSS, matplotlib chart style and small
reusable HTML components. Business logic stays in app.py / database.py.
"""
import html
import streamlit as st
import matplotlib

# ── Palette ───────────────────────────────────────────────────────────────────
PRIMARY = "#4f46e5"     # indigo
PRIMARY_DK = "#3730a3"
ACCENT = "#06b6d4"      # cyan
WARM = "#f59e0b"        # amber
GOOD = "#10b981"
BAD = "#ef4444"
INK = "#0f172a"
MUTED = "#64748b"
LINE = "#e2e8f0"
CHART_COLORS = [PRIMARY, WARM, ACCENT, GOOD, "#ec4899", "#8b5cf6", "#14b8a6", "#f97316"]

_CSS = """
<style>
/* ============================================================
   SPEIS SCHOOL DESIGN SYSTEM — v2
   Clean, calm, modern and school-administration friendly.
   ============================================================ */

:root{
  --navy:#10233f;
  --navy-2:#17365f;
  --blue:#2563eb;
  --blue-2:#1d4ed8;
  --teal:#0f9f9a;
  --green:#159570;
  --amber:#d98b18;
  --red:#dc4b4b;
  --ink:#172033;
  --muted:#68758a;
  --line:#e5eaf1;
  --bg:#f4f7fb;
  --card:#ffffff;
  --radius:16px;
  --shadow:0 6px 24px rgba(16,35,63,.07);
  --shadow-sm:0 2px 10px rgba(16,35,63,.055);
}

html,body,[class*="css"],.stApp{
  font-family:Inter,ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;
  color:var(--ink);
}
.stApp{
  background:
    radial-gradient(800px 300px at 95% -5%,rgba(37,99,235,.075),transparent 65%),
    linear-gradient(180deg,#f8fafc 0%,var(--bg) 55%,#f3f6fa 100%);
}
h1,h2,h3,h4{
  font-family:Inter,ui-sans-serif,system-ui,sans-serif;
  color:var(--ink);
  letter-spacing:-.018em;
}
h1{font-weight:800}
h2{font-size:1.42rem;font-weight:750}
h3{font-weight:700}
.block-container{
  padding-top:1.65rem;
  padding-bottom:3rem;
  max-width:none;
  width:100%;
  padding-left:2rem;
  padding-right:2rem;
}

/* Premium workspace shell */
[data-testid="stAppViewContainer"]{background:transparent!important}
[data-testid="stMainBlockContainer"]{max-width:none!important}
[data-testid="stSidebarCollapsedControl"]{display:flex!important;position:fixed!important;left:12px!important;top:72px!important;z-index:999999!important}
[data-testid="stSidebarCollapsedControl"] button{width:42px!important;height:42px!important;border-radius:12px!important;background:#0b2341!important;color:#fff!important;border:1px solid rgba(255,255,255,.14)!important;box-shadow:0 8px 24px rgba(2,12,27,.22)!important}
[data-testid="stSidebarCollapsedControl"] button:hover{background:#163f6c!important}
[data-testid="stSidebarNav"]{display:none!important}
.stColumn{min-width:0!important}
div[data-testid="stVerticalBlock"]{min-width:0}

/* Hide Streamlit chrome but retain the sidebar toggle. */
#MainMenu,footer,[data-testid="stToolbar"],[data-testid="stDeployButton"]{
  display:none!important;
}
header[data-testid="stHeader"]{
  background:rgba(248,250,252,.84);
  backdrop-filter:blur(12px);
}

/* ============================================================
   SIDEBAR — DARK PROFESSIONAL SCHOOL NAVIGATION
   Fully collapsible: wide expanded / thin icon-only collapsed.
   ============================================================ */
section[data-testid="stSidebar"]{
  background:linear-gradient(180deg,#071a33 0%,#0a2342 55%,#081a31 100%);
  border-right:1px solid rgba(255,255,255,.08);
  box-shadow:8px 0 30px rgba(2,12,27,.22);
  min-width:310px;
  max-width:310px;
  width:310px;
  transition:width .25s ease,min-width .25s ease,max-width .25s ease!important;
}
section[data-testid="stSidebar"] > div:first-child{
  padding:22px 16px 24px;
  transition:padding .25s ease!important;
}
section[data-testid="stSidebar"] *{box-sizing:border-box}
section[data-testid="stSidebar"] hr{
  border:0;border-top:1px solid rgba(255,255,255,.09);margin:14px 6px;
}

/* Toggle button is always visible inside the sidebar */
section[data-testid="stSidebar"] .sb-toggle-wrap{
  display:flex;
  justify-content:flex-end;
  margin:0 0 8px;
}
section[data-testid="stSidebar"] .sb-toggle-wrap .stButton{
  width:auto!important;
  margin:0!important;
}
section[data-testid="stSidebar"] .sb-toggle-wrap .stButton > button{
  width:40px!important;
  min-width:40px!important;
  height:38px!important;
  min-height:38px!important;
  padding:0!important;
  display:flex!important;
  align-items:center!important;
  justify-content:center!important;
  border-radius:10px!important;
  background:rgba(255,255,255,.07)!important;
  border:1px solid rgba(255,255,255,.11)!important;
  color:#dbeafe!important;
  font-size:15px!important;
  box-shadow:none!important;
  transform:none!important;
}
section[data-testid="stSidebar"] .sb-toggle-wrap .stButton > button:hover{
  background:rgba(255,255,255,.15)!important;
  border-color:rgba(255,255,255,.22)!important;
  transform:none!important;
}

/* Brand */
.sb-brand{display:flex;align-items:center;gap:12px;padding:4px 7px 17px}
.sb-logo{
  width:45px;height:45px;flex:0 0 45px;display:grid;place-items:center;
  border-radius:13px;font-size:21px;color:#fff;
  background:linear-gradient(145deg,#1d4ed8,#0891b2);
  border:1px solid rgba(255,255,255,.14);
  box-shadow:0 9px 22px rgba(0,0,0,.25);
}
.sb-brand b{display:block;color:#fff;font-size:18px;line-height:1.05;letter-spacing:.02em;font-weight:800}
.sb-brand small{display:block;margin-top:4px;color:#8ea7c4;font-size:9.5px;line-height:1.2;letter-spacing:.065em;text-transform:uppercase;font-weight:650}

/* User profile */
.sb-user{display:flex;align-items:center;gap:10px;padding:11px;border:1px solid rgba(255,255,255,.09);border-radius:14px;background:rgba(255,255,255,.055);box-shadow:inset 0 1px 0 rgba(255,255,255,.035)}
.sb-avatar{width:40px;height:40px;flex:0 0 40px;display:grid;place-items:center;border-radius:12px;color:#fff;font-weight:800;font-size:13px;background:linear-gradient(145deg,#2563eb,#0891b2);box-shadow:0 6px 14px rgba(0,0,0,.22)}
.sb-user .n{color:#fff;font-weight:750;font-size:13px;line-height:1.2;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.sb-user .r{color:#8fa8c4;font-size:11px;margin-top:3px}
.sb-label{color:#6f8aa8;font-size:9.5px;font-weight:800;letter-spacing:.14em;text-transform:uppercase;margin:19px 8px 8px}

/* Navigation */
section[data-testid="stSidebar"] .sb-nav-title{margin-top:18px!important;margin-bottom:8px!important}
section[data-testid="stSidebar"] .stButton{width:100%!important;margin:0 0 6px 0!important}
section[data-testid="stSidebar"] .stButton > button{
  width:100%!important;min-height:46px!important;justify-content:flex-start!important;
  text-align:left!important;padding:0 13px!important;border-radius:11px!important;
  border:1px solid rgba(255,255,255,.055)!important;background:rgba(255,255,255,.025)!important;
  color:#b9c9dc!important;font-size:12.5px!important;font-weight:600!important;
  box-shadow:none!important;transition:all .16s ease!important;
}
section[data-testid="stSidebar"] .stButton > button:hover{
  background:rgba(255,255,255,.075)!important;border-color:rgba(96,165,250,.18)!important;
  color:#fff!important;transform:translateX(2px)!important;
}
section[data-testid="stSidebar"] .stButton > button[kind="primary"]{
  color:#fff!important;font-weight:750!important;
  background:linear-gradient(90deg,rgba(37,99,235,.34),rgba(8,145,178,.13))!important;
  border-color:rgba(96,165,250,.28)!important;
  box-shadow:inset 3px 0 0 #60a5fa,0 5px 14px rgba(0,0,0,.10)!important;
}

/* Footer / sign out */
section[data-testid="stSidebar"] .sb-footer{margin-top:18px;padding:11px 12px;border-top:1px solid rgba(255,255,255,.08);color:#6f8aa8;font-size:10px;line-height:1.5}
.sb-signout .stButton{margin-top:10px!important}
.sb-signout .stButton > button{min-height:43px!important;border:1px solid rgba(248,113,113,.16)!important;background:rgba(220,72,72,.07)!important;color:#c8d5e5!important;border-radius:11px!important;box-shadow:none!important;font-size:12px!important;font-weight:700!important}
.sb-signout .stButton > button:hover{color:#fff!important;background:rgba(220,72,72,.17)!important;border-color:rgba(248,113,113,.3)!important;box-shadow:none!important;transform:none!important}
section[data-testid="stSidebar"] > div:first-child::-webkit-scrollbar{width:5px}
section[data-testid="stSidebar"] > div:first-child::-webkit-scrollbar-thumb{background:#284665;border-radius:99px}

/* ============================================================
   SPEIS SIDEBAR — PREMIUM FULL COLLAPSE
   ------------------------------------------------------------
   Expanded:
     Desktop  = 310px
     Mobile   = 86vw

   Collapsed:
     Desktop  = 72px
     Mobile   = 64px
     Small     = 58px

   IMPORTANT:
   The state marker is INSIDE section[data-testid="stSidebar"].
   :has(...) therefore resizes the REAL sidebar itself.
   ============================================================ */

/* ---------- BASE / EXPANDED SIDEBAR ---------- */
section[data-testid="stSidebar"]{
  width:310px!important;
  min-width:310px!important;
  max-width:310px!important;
  flex:0 0 310px!important;
  box-sizing:border-box!important;
}

section[data-testid="stSidebar"] > div:first-child{
  width:100%!important;
  min-width:0!important;
  max-width:none!important;
  padding:22px 16px 24px!important;
  box-sizing:border-box!important;
}

/* The state marker is invisible. It only drives CSS state. */
section[data-testid="stSidebar"] .speis-sidebar-state{
  display:none!important;
}

/* ---------- TOGGLE BUTTON ---------- */
section[data-testid="stSidebar"] .sb-toggle-wrap{
  display:flex!important;
  justify-content:flex-end!important;
  align-items:center!important;
  width:100%!important;
  height:38px!important;
  margin:0 0 2px!important;
}

section[data-testid="stSidebar"] .sb-toggle-wrap .stButton{
  width:38px!important;
  min-width:38px!important;
  margin:0!important;
}

section[data-testid="stSidebar"] .sb-toggle-wrap .stButton > button{
  width:38px!important;
  min-width:38px!important;
  height:38px!important;
  min-height:38px!important;
  padding:0!important;
  display:flex!important;
  align-items:center!important;
  justify-content:center!important;
  border-radius:11px!important;
  border:1px solid rgba(255,255,255,.11)!important;
  background:rgba(255,255,255,.07)!important;
  color:#dcecff!important;
  font-size:14px!important;
  font-weight:800!important;
  box-shadow:0 5px 15px rgba(0,0,0,.12)!important;
  transform:none!important;
}

section[data-testid="stSidebar"] .sb-toggle-wrap .stButton > button:hover{
  background:rgba(96,165,250,.20)!important;
  border-color:rgba(96,165,250,.35)!important;
  color:#fff!important;
  transform:none!important;
}

/* ---------- COLLAPSED: THE COMPLETE REAL SIDEBAR ---------- */
section[data-testid="stSidebar"]:has(
  .speis-sidebar-state.speis-sidebar-collapsed
){
  width:72px!important;
  min-width:72px!important;
  max-width:72px!important;
  flex:0 0 72px!important;
  box-sizing:border-box!important;
}

section[data-testid="stSidebar"]:has(
  .speis-sidebar-state.speis-sidebar-collapsed
) > div:first-child{
  width:72px!important;
  min-width:72px!important;
  max-width:72px!important;
  padding:10px 8px 16px!important;
  box-sizing:border-box!important;
}

/* Toggle becomes centered in the rail. */
section[data-testid="stSidebar"]:has(
  .speis-sidebar-state.speis-sidebar-collapsed
) .sb-toggle-wrap{
  justify-content:center!important;
  height:40px!important;
  margin:0 0 8px!important;
}

section[data-testid="stSidebar"]:has(
  .speis-sidebar-state.speis-sidebar-collapsed
) .sb-toggle-wrap .stButton{
  width:42px!important;
  min-width:42px!important;
}

section[data-testid="stSidebar"]:has(
  .speis-sidebar-state.speis-sidebar-collapsed
) .sb-toggle-wrap .stButton > button{
  width:42px!important;
  min-width:42px!important;
  height:40px!important;
  min-height:40px!important;
  padding:0!important;
  border-radius:12px!important;
  font-size:14px!important;
}

/* ---------- BRAND ---------- */
section[data-testid="stSidebar"]:has(
  .speis-sidebar-state.speis-sidebar-collapsed
) .sb-brand{
  width:100%!important;
  display:flex!important;
  justify-content:center!important;
  align-items:center!important;
  padding:4px 0 12px!important;
}

section[data-testid="stSidebar"]:has(
  .speis-sidebar-state.speis-sidebar-collapsed
) .sb-brand-text{
  display:none!important;
}

section[data-testid="stSidebar"]:has(
  .speis-sidebar-state.speis-sidebar-collapsed
) .sb-logo{
  width:46px!important;
  height:46px!important;
  min-width:46px!important;
  flex:0 0 46px!important;
  border-radius:14px!important;
  font-size:20px!important;
}

/* ---------- USER CARD ---------- */
section[data-testid="stSidebar"]:has(
  .speis-sidebar-state.speis-sidebar-collapsed
) .sb-user{
  width:100%!important;
  display:flex!important;
  justify-content:center!important;
  align-items:center!important;
  padding:7px 0!important;
  border-color:transparent!important;
  background:transparent!important;
  box-shadow:none!important;
}

section[data-testid="stSidebar"]:has(
  .speis-sidebar-state.speis-sidebar-collapsed
) .sb-user-text{
  display:none!important;
}

section[data-testid="stSidebar"]:has(
  .speis-sidebar-state.speis-sidebar-collapsed
) .sb-avatar{
  width:42px!important;
  height:42px!important;
  min-width:42px!important;
  flex:0 0 42px!important;
  border-radius:13px!important;
}

/* ---------- NAVIGATION LABEL ---------- */
section[data-testid="stSidebar"]:has(
  .speis-sidebar-state.speis-sidebar-collapsed
) .sb-nav-title{
  display:none!important;
}

/* ---------- NAV BUTTONS ---------- */
section[data-testid="stSidebar"]:has(
  .speis-sidebar-state.speis-sidebar-collapsed
) .stButton{
  width:100%!important;
  min-width:0!important;
  margin:0 0 7px!important;
}

section[data-testid="stSidebar"]:has(
  .speis-sidebar-state.speis-sidebar-collapsed
) .stButton > button{
  width:100%!important;
  min-width:0!important;
  max-width:100%!important;
  height:47px!important;
  min-height:47px!important;
  padding:0!important;
  display:flex!important;
  align-items:center!important;
  justify-content:center!important;
  text-align:center!important;
  border-radius:12px!important;
  font-size:20px!important;
  line-height:1!important;
  overflow:hidden!important;
  white-space:nowrap!important;
  transform:none!important;
}

section[data-testid="stSidebar"]:has(
  .speis-sidebar-state.speis-sidebar-collapsed
) .stButton > button:hover{
  transform:none!important;
}

/* Keep the active icon button visually strong. */
section[data-testid="stSidebar"]:has(
  .speis-sidebar-state.speis-sidebar-collapsed
) .stButton > button[kind="primary"]{
  box-shadow:
    inset 3px 0 0 #60a5fa,
    0 7px 16px rgba(0,0,0,.14)!important;
}

/* ---------- SIGN OUT ---------- */
section[data-testid="stSidebar"]:has(
  .speis-sidebar-state.speis-sidebar-collapsed
) .sb-signout .stButton > button{
  font-size:0!important;
  justify-content:center!important;
  padding:0!important;
}

section[data-testid="stSidebar"]:has(
  .speis-sidebar-state.speis-sidebar-collapsed
) .sb-signout .stButton > button::before{
  content:"🚪";
  font-size:18px!important;
  line-height:1!important;
}

/* ---------- FOOTER ---------- */
section[data-testid="stSidebar"]:has(
  .speis-sidebar-state.speis-sidebar-collapsed
) .sb-footer{
  display:none!important;
}

/* ---------- SCROLLBAR ---------- */
section[data-testid="stSidebar"] > div:first-child::-webkit-scrollbar{
  width:4px;
}
section[data-testid="stSidebar"] > div:first-child::-webkit-scrollbar-thumb{
  background:#284665;
  border-radius:99px;
}

/* Do not show Streamlit's second sidebar-open control.
   Our custom rail toggle is the only sidebar control. */
[data-testid="stSidebarCollapsedControl"]{
  display:none!important;
}

/* ============================================================
   RESPONSIVE MOBILE
   ============================================================ */
@media (max-width:768px){

  /* Expanded drawer */
  section[data-testid="stSidebar"]{
    width:86vw!important;
    min-width:86vw!important;
    max-width:86vw!important;
    flex:0 0 86vw!important;
  }

  section[data-testid="stSidebar"] > div:first-child{
    width:100%!important;
    min-width:0!important;
    max-width:none!important;
    padding:14px 12px 20px!important;
  }

  /* Collapsed mobile rail */
  section[data-testid="stSidebar"]:has(
    .speis-sidebar-state.speis-sidebar-collapsed
  ){
    width:64px!important;
    min-width:64px!important;
    max-width:64px!important;
    flex:0 0 64px!important;
  }

  section[data-testid="stSidebar"]:has(
    .speis-sidebar-state.speis-sidebar-collapsed
  ) > div:first-child{
    width:64px!important;
    min-width:64px!important;
    max-width:64px!important;
    padding:8px 6px 14px!important;
  }

  section[data-testid="stSidebar"]:has(
    .speis-sidebar-state.speis-sidebar-collapsed
  ) .sb-logo{
    width:40px!important;
    height:40px!important;
    min-width:40px!important;
    flex-basis:40px!important;
    border-radius:12px!important;
    font-size:18px!important;
  }

  section[data-testid="stSidebar"]:has(
    .speis-sidebar-state.speis-sidebar-collapsed
  ) .sb-avatar{
    width:38px!important;
    height:38px!important;
    min-width:38px!important;
    flex-basis:38px!important;
    border-radius:11px!important;
    font-size:11px!important;
  }

  section[data-testid="stSidebar"]:has(
    .speis-sidebar-state.speis-sidebar-collapsed
  ) .stButton > button{
    height:44px!important;
    min-height:44px!important;
    font-size:18px!important;
    border-radius:11px!important;
  }

  section[data-testid="stSidebar"]:has(
    .speis-sidebar-state.speis-sidebar-collapsed
  ) .sb-toggle-wrap .stButton > button{
    width:40px!important;
    min-width:40px!important;
    height:38px!important;
    min-height:38px!important;
    font-size:13px!important;
  }
}

@media (max-width:480px){

  section[data-testid="stSidebar"]:has(
    .speis-sidebar-state.speis-sidebar-collapsed
  ){
    width:58px!important;
    min-width:58px!important;
    max-width:58px!important;
    flex:0 0 58px!important;
  }

  section[data-testid="stSidebar"]:has(
    .speis-sidebar-state.speis-sidebar-collapsed
  ) > div:first-child{
    width:58px!important;
    min-width:58px!important;
    max-width:58px!important;
    padding:7px 5px 12px!important;
  }

  section[data-testid="stSidebar"]:has(
    .speis-sidebar-state.speis-sidebar-collapsed
  ) .sb-logo{
    width:36px!important;
    height:36px!important;
    min-width:36px!important;
    flex-basis:36px!important;
    font-size:16px!important;
  }

  section[data-testid="stSidebar"]:has(
    .speis-sidebar-state.speis-sidebar-collapsed
  ) .sb-avatar{
    width:34px!important;
    height:34px!important;
    min-width:34px!important;
    flex-basis:34px!important;
  }

  section[data-testid="stSidebar"]:has(
    .speis-sidebar-state.speis-sidebar-collapsed
  ) .stButton > button{
    height:42px!important;
    min-height:42px!important;
    font-size:17px!important;
  }
}

/* ============================================================
   PAGE HEADER
   ============================================================ */
.page-head{
  position:relative;
  overflow:hidden;
  display:flex;
  align-items:center;
  min-height:126px;
  padding:20px 24px;
  margin-bottom:20px;
  border:1px solid rgba(255,255,255,.12);
  border-radius:22px;
  color:#fff;
  background:linear-gradient(120deg,#102d50 0%,#174b7e 58%,#167f83 100%);
  box-shadow:0 16px 38px rgba(16,35,63,.14);
}
.page-head::before{
  content:"";
  position:absolute;
  width:300px;height:300px;
  right:-90px;top:-135px;
  border-radius:50%;
  border:45px solid rgba(255,255,255,.055);
}
.page-head::after{
  content:"";
  position:absolute;
  width:150px;height:150px;
  right:125px;bottom:-105px;
  border-radius:50%;
  background:rgba(255,255,255,.045);
}
.page-head .ph-row{
  display:flex;
  align-items:center;
  gap:14px;
  position:relative;
  z-index:2;
}
.page-head .ph-ico{
  width:54px;height:54px;
  flex:0 0 54px;
  display:grid;
  place-items:center;
  border:1px solid rgba(255,255,255,.18);
  border-radius:15px;
  font-size:23px;
  background:rgba(255,255,255,.105);
  backdrop-filter:blur(8px);
}
.page-head h1{
  color:#fff!important;
  margin:0;
  font-size:1.55rem;
  line-height:1.18;
}
.page-head p{
  color:rgba(255,255,255,.78);
  margin:5px 0 0;
  font-size:.87rem;
}

/* ============================================================
   CARDS / STATS
   ============================================================ */
.card{
  background:var(--card);
  border:1px solid var(--line);
  border-radius:var(--radius);
  padding:18px 19px;
  margin-bottom:14px;
  box-shadow:var(--shadow-sm);
}
.card h4{
  margin:0 0 10px;
  color:var(--navy);
  font-size:14px;
  font-weight:750;
}
.kv{
  display:flex;
  justify-content:space-between;
  gap:16px;
  padding:9px 0;
  border-bottom:1px dashed #e8edf3;
  font-size:13px;
}
.kv:last-child{border-bottom:none}
.kv span:first-child{color:var(--muted)}
.kv span:last-child{color:var(--ink);font-weight:650;text-align:right}

.stat-grid{
  display:grid;
  grid-template-columns:repeat(4,minmax(0,1fr));
  gap:16px;
  margin:2px 0 22px;
}
.stat{
  position:relative;
  overflow:hidden;
  background:#fff;
  border:1px solid var(--line);
  border-radius:15px;
  padding:18px;
  box-shadow:var(--shadow-sm);
  transition:transform .18s ease,box-shadow .18s ease;
}
.stat:hover{transform:translateY(-2px);box-shadow:var(--shadow)}
.stat::before{
  content:"";
  position:absolute;
  left:0;top:0;bottom:0;
  width:3px;
  background:var(--c,#2563eb);
}
.stat .ico{
  width:36px;height:36px;
  display:grid;place-items:center;
  border-radius:10px;
  margin-bottom:10px;
  background:#f0f5ff;
  font-size:17px;
}
.stat .lbl{color:#718096;font-size:11px;font-weight:650}
.stat .val{
  color:var(--navy);
  font-size:23px;
  font-weight:800;
  line-height:1.15;
  margin-top:2px;
}
.stat .hint{color:#8a95a6;font-size:10.5px;margin-top:4px}

div[data-testid="stMetric"]{
  background:#fff;
  border:1px solid var(--line);
  border-radius:14px;
  padding:12px 15px;
  box-shadow:var(--shadow-sm);
}
div[data-testid="stMetric"] label{color:var(--muted)!important;font-size:11px!important}
div[data-testid="stMetricValue"]{color:var(--navy)!important;font-weight:800}

.section-title{
  display:flex;
  align-items:center;
  gap:8px;
  margin:22px 0 10px;
  color:var(--navy);
  font-size:15px;
  font-weight:750;
}
.section-title::after{
  content:"";
  flex:1;
  height:1px;
  background:#e4e9f0;
}

.pill{
  display:inline-block;
  padding:4px 9px;
  border-radius:999px;
  font-size:10.5px;
  font-weight:700;
  margin:1px 2px;
}
.pill.good{background:#e7f7f1;color:#087653}
.pill.warn{background:#fff4df;color:#9a6500}
.pill.bad{background:#ffebeb;color:#b42c2c}
.pill.info{background:#eaf1ff;color:#2456a6}

.empty{
  text-align:center;
  padding:36px 18px;
  color:var(--muted);
  background:#fff;
  border:1.5px dashed #dce3ec;
  border-radius:15px;
}
.empty .e-ico{font-size:30px;margin-bottom:5px}

/* ============================================================
   FORMS / CONTROLS
   ============================================================ */
div[data-testid="stForm"]{
  background:#fff;
  padding:20px;
  border:1px solid var(--line);
  border-radius:16px;
  box-shadow:var(--shadow-sm);
}
div[data-testid="stExpander"]{
  background:#fff;
  border:1px solid var(--line);
  border-radius:14px;
  box-shadow:var(--shadow-sm);
  overflow:hidden;
}
div[data-testid="stExpander"] summary{
  font-weight:700;
  color:var(--navy);
}
div[data-baseweb="input"],
div[data-baseweb="select"]>div,
div[data-baseweb="textarea"]{
  border-radius:10px!important;
  border-color:#dce3ec!important;
  background:#fff!important;
}
div[data-baseweb="input"]:focus-within,
div[data-baseweb="select"]>div:focus-within{
  box-shadow:0 0 0 3px rgba(37,99,235,.11)!important;
  border-color:#7ca6e8!important;
}
.stTextInput label,.stSelectbox label,.stNumberInput label,
.stMultiSelect label,.stTextArea label,.stDateInput label{
  color:#526176!important;
  font-weight:650!important;
  font-size:11.5px!important;
}
.stButton>button,.stFormSubmitButton>button{
  min-height:40px;
  color:#fff!important;
  border:0!important;
  border-radius:10px!important;
  background:linear-gradient(135deg,#2563eb,#1d4ed8)!important;
  font-weight:700!important;
  box-shadow:0 5px 13px rgba(37,99,235,.18)!important;
  transition:transform .15s ease,box-shadow .15s ease!important;
}
.stButton>button:hover,.stFormSubmitButton>button:hover{
  transform:translateY(-1px)!important;
  box-shadow:0 8px 18px rgba(37,99,235,.25)!important;
}
.stDownloadButton>button{
  min-height:40px;
  color:#fff!important;
  border:0!important;
  border-radius:10px!important;
  background:linear-gradient(135deg,#159570,#08795d)!important;
  font-weight:700!important;
}
div[data-baseweb="tab-list"]{
  gap:4px;
  padding:4px;
  border:1px solid #e4e9f0;
  border-radius:11px;
  background:#eef2f7;
  max-width:100%;
  overflow-x:auto;
}
button[data-baseweb="tab"]{
  border-radius:8px!important;
  padding:7px 13px!important;
  font-size:12px!important;
  font-weight:650!important;
}
button[data-baseweb="tab"][aria-selected="true"]{
  background:#fff!important;
  color:#1d4ed8!important;
  box-shadow:0 2px 7px rgba(16,35,63,.08)!important;
}
div[data-baseweb="tab-highlight"],div[data-baseweb="tab-border"]{display:none}

div[data-testid="stAlert"]{
  border-radius:12px;
  border:1px solid rgba(16,35,63,.06);
  box-shadow:var(--shadow-sm);
}
div[data-testid="stDataFrame"]{
  border:1px solid var(--line);
  border-radius:14px;
  overflow:hidden;
  box-shadow:var(--shadow-sm);
}
div[data-testid="stFileUploader"] section{
  border:1.5px dashed #a9c5ed;
  border-radius:14px;
  background:#f5f9ff;
}
div[data-testid="stImage"] img,.stPyplot img{border-radius:12px}
div[data-testid="stPyplot"]{
  background:#fff;
  border:1px solid var(--line);
  border-radius:15px;
  padding:7px;
  box-shadow:var(--shadow-sm);
}

/* ============================================================
   DATA TABLES / CHARTS / CONTENT SURFACES
   ============================================================ */
div[data-testid="stDataFrame"]{margin:8px 0 18px!important;background:#fff!important;border:1px solid #dfe6ef!important;border-radius:16px!important;box-shadow:0 8px 24px rgba(16,35,63,.06)!important}
div[data-testid="stDataFrame"] > div{border-radius:16px!important}
div[data-testid="stDataFrame"] iframe{border-radius:16px!important}
.stPyplot{margin:6px 0 18px!important}
.stPyplot img{display:block!important;width:100%!important;height:auto!important}
div[data-testid="stHorizontalBlock"]{gap:18px!important}
.stCaption{color:#7a8799!important}
.stMarkdown p{line-height:1.55}
button[kind="secondary"]{border:1px solid #d9e1ec!important;background:#fff!important;color:#334155!important;box-shadow:0 3px 10px rgba(16,35,63,.05)!important}
button[kind="secondary"]:hover{border-color:#9db7d7!important;background:#f7faff!important}

/* ============================================================
   LOGIN
   ============================================================ */
.login-hero{
  position:relative;
  overflow:hidden;
  min-height:470px;
  padding:38px;
  border-radius:22px;
  color:#fff;
  background:linear-gradient(145deg,#102d50,#174b7e 62%,#167f83);
  box-shadow:0 14px 34px rgba(16,35,63,.13);
}
.login-hero::after{
  content:"";
  position:absolute;
  right:-90px;bottom:-100px;
  width:330px;height:330px;
  border-radius:50%;
  border:55px solid rgba(255,255,255,.055);
}
.login-hero .logo{
  width:58px;height:58px;
  display:grid;place-items:center;
  border-radius:17px;
  background:rgba(255,255,255,.12);
  border:1px solid rgba(255,255,255,.14);
  font-size:25px;
  margin-bottom:22px;
}
.login-hero h1{
  color:#fff!important;
  font-size:2rem;
  line-height:1.13;
  margin:0 0 9px;
}
.login-hero p{
  color:rgba(255,255,255,.78);
  font-size:.94rem;
  margin:0 0 22px;
}
.feat{
  display:flex;
  align-items:flex-start;
  gap:10px;
  margin:11px 0;
  position:relative;
  z-index:1;
}
.feat i{
  width:33px;height:33px;
  flex:0 0 33px;
  display:grid;place-items:center;
  border-radius:10px;
  background:rgba(255,255,255,.105);
  font-style:normal;
}
.feat b{display:block;font-size:12.5px}
.feat span{display:block;font-size:10.5px;color:rgba(255,255,255,.65);margin-top:2px}
.login-title{
  color:var(--navy);
  font-weight:800;
  font-size:1.45rem;
  margin:.25rem 0 .1rem;
}
.login-sub{color:var(--muted);font-size:.86rem;margin-bottom:8px}

@media (max-width:1100px){
  section[data-testid="stSidebar"]{
    min-width:285px;
    max-width:285px;
  }
  .stat-grid{grid-template-columns:repeat(2,minmax(0,1fr));}
}
@media (max-width:900px){
  .page-head{min-height:96px;padding:17px 18px}
  .page-head h1{font-size:1.3rem}
}
/* ============================================================
   MOBILE RESPONSIVE — SPEIS
   UI ONLY — NO APPLICATION LOGIC CHANGES
   ============================================================ */

/* Tablets / small laptops */
@media (max-width:1100px){
  .block-container{
    padding-left:1.25rem;
    padding-right:1.25rem;
  }

  .stat-grid{
    grid-template-columns:repeat(2,minmax(0,1fr));
  }
}

/* ============================================================
   TABLET / MOBILE
   ============================================================ */
@media (max-width:768px){

  /* Main page spacing */
  .block-container{
    padding-top:1rem!important;
    padding-left:12px!important;
    padding-right:12px!important;
    padding-bottom:2rem!important;
  }

  /* Sidebar */
  section[data-testid="stSidebar"]{
    min-width:85vw!important;
    max-width:85vw!important;
    width:85vw!important;
  }

  section[data-testid="stSidebar"] > div:first-child{
    padding:18px 13px 20px!important;
  }

  /* Sidebar buttons */
  section[data-testid="stSidebar"] .stButton > button{
    min-height:44px!important;
    font-size:12px!important;
    padding:0 11px!important;
  }

  /* Main page header */
  .page-head{
    min-height:auto!important;
    padding:17px 16px!important;
    margin-bottom:15px!important;
    border-radius:16px!important;
  }

  .page-head .ph-row{
    gap:10px!important;
    align-items:flex-start!important;
  }

  .page-head .ph-ico{
    width:44px!important;
    height:44px!important;
    flex:0 0 44px!important;
    border-radius:12px!important;
    font-size:19px!important;
  }

  .page-head h1{
    font-size:1.15rem!important;
    line-height:1.25!important;
  }

  .page-head p{
    font-size:.75rem!important;
    line-height:1.4!important;
    margin-top:4px!important;
  }

  /* ==========================================================
     STREAMLIT COLUMNS
     Stack columns vertically on mobile.
     ========================================================== */

  [data-testid="stHorizontalBlock"]{
    flex-wrap:wrap!important;
    gap:0.75rem!important;
  }

  [data-testid="stHorizontalBlock"] > [data-testid="column"]{
    width:100%!important;
    min-width:100%!important;
    max-width:100%!important;
    flex:1 1 100%!important;
  }

  /* ==========================================================
     STAT CARDS
     ========================================================== */

  .stat-grid{
    grid-template-columns:repeat(2,minmax(0,1fr))!important;
    gap:9px!important;
    margin-bottom:16px!important;
  }

  .stat{
    padding:13px!important;
    border-radius:13px!important;
  }

  .stat .ico{
    width:31px!important;
    height:31px!important;
    font-size:15px!important;
    margin-bottom:7px!important;
  }

  .stat .lbl{
    font-size:9.5px!important;
  }

  .stat .val{
    font-size:19px!important;
  }

  .stat .hint{
    font-size:9px!important;
  }

  /* Streamlit metrics */
  div[data-testid="stMetric"]{
    padding:10px 12px!important;
    border-radius:12px!important;
  }

  div[data-testid="stMetric"] label{
    font-size:10px!important;
  }

  div[data-testid="stMetricValue"]{
    font-size:1.25rem!important;
  }

  /* ==========================================================
     CARDS
     ========================================================== */

  .card{
    padding:14px!important;
    border-radius:13px!important;
    margin-bottom:11px!important;
  }

  .card h4{
    font-size:13px!important;
  }

  .kv{
    gap:10px!important;
    font-size:11.5px!important;
    padding:8px 0!important;
  }

  .kv span:first-child{
    flex:0 0 auto;
  }

  .kv span:last-child{
    max-width:60%;
    overflow-wrap:anywhere;
  }

  /* ==========================================================
     SECTION TITLES
     ========================================================== */

  .section-title{
    margin:18px 0 9px!important;
    font-size:13px!important;
    gap:6px!important;
  }

  /* ==========================================================
     FORMS
     ========================================================== */

  div[data-testid="stForm"]{
    padding:14px!important;
    border-radius:13px!important;
  }

  /* All normal controls should use full mobile width */
  div[data-testid="stTextInput"],
  div[data-testid="stTextArea"],
  div[data-testid="stNumberInput"],
  div[data-testid="stSelectbox"],
  div[data-testid="stMultiSelect"],
  div[data-testid="stDateInput"],
  div[data-testid="stFileUploader"]{
    width:100%!important;
  }

  /* Buttons */
  div.stButton > button,
  div[data-testid="stFormSubmitButton"] > button,
  div[data-testid="stDownloadButton"] > button{
    width:100%!important;
    min-height:44px!important;
    font-size:12px!important;
  }

  /* ==========================================================
     TABS
     ========================================================== */

  [data-baseweb="tab-list"]{
    overflow-x:auto!important;
    overflow-y:hidden!important;
    flex-wrap:nowrap!important;
    -webkit-overflow-scrolling:touch!important;
    scrollbar-width:none!important;
  }

  [data-baseweb="tab-list"]::-webkit-scrollbar{
    display:none!important;
  }

  [data-baseweb="tab"]{
    white-space:nowrap!important;
    flex:0 0 auto!important;
    font-size:12px!important;
    padding-left:12px!important;
    padding-right:12px!important;
  }

  /* ==========================================================
     DATA TABLES
     ========================================================== */

  div[data-testid="stDataFrame"],
  div[data-testid="stTable"]{
    width:100%!important;
    max-width:100%!important;
    overflow-x:auto!important;
    -webkit-overflow-scrolling:touch!important;
  }

  /* Prevent long text from destroying the layout */
  table{
    font-size:11px!important;
  }

  /* ==========================================================
     EXPANDERS
     ========================================================== */

  div[data-testid="stExpander"]{
    border-radius:12px!important;
  }

  div[data-testid="stExpander"] summary{
    font-size:12px!important;
  }

  /* ==========================================================
     ALERTS
     ========================================================== */

  div[data-testid="stAlert"]{
    font-size:12px!important;
    border-radius:11px!important;
  }

  /* ==========================================================
     IMAGES / CHARTS
     ========================================================== */

  img{
    max-width:100%!important;
    height:auto!important;
  }

  div[data-testid="stImage"],
  div[data-testid="stPyplot"]{
    width:100%!important;
    max-width:100%!important;
    overflow:hidden!important;
  }

  /* ==========================================================
     LOGIN SCREEN
     ========================================================== */

  .login-hero{
    min-height:auto!important;
    padding:24px 18px!important;
    border-radius:16px!important;
  }

  .login-hero h1{
    font-size:1.35rem!important;
    line-height:1.25!important;
  }

  .login-sub{
    font-size:.78rem!important;
  }

  .login-title{
    font-size:1.3rem!important;
  }

  .feat{
    gap:8px!important;
    margin:9px 0!important;
  }

  .feat i{
    width:30px!important;
    height:30px!important;
    flex:0 0 30px!important;
  }

  .feat b{
    font-size:11.5px!important;
  }

  .feat span{
    font-size:9.5px!important;
  }

  /* Radio buttons */
  div[data-testid="stRadio"] label{
    font-size:11px!important;
  }

  /* Captions */
  .stCaption,
  [data-testid="stCaptionContainer"]{
    font-size:10px!important;
  }
}

/* ============================================================
   VERY SMALL PHONES
   ============================================================ */
@media (max-width:480px){

  .block-container{
    padding-left:9px!important;
    padding-right:9px!important;
  }

  /* One stat card per row on very small screens */
  .stat-grid{
    grid-template-columns:1fr!important;
    gap:8px!important;
  }

  .stat{
    padding:12px!important;
  }

  .page-head{
    padding:14px!important;
  }

  .page-head .ph-ico{
    width:40px!important;
    height:40px!important;
    flex-basis:40px!important;
    font-size:17px!important;
  }

  .page-head h1{
    font-size:1rem!important;
  }

  .page-head p{
    font-size:.7rem!important;
  }

  .card{
    padding:12px!important;
  }

  .section-title{
    font-size:12px!important;
  }

  /* Smaller mobile inputs */
  input,
  textarea,
  select{
    font-size:12px!important;
  }

  /* Keep long values inside cards */
  .kv{
    flex-direction:column!important;
    gap:3px!important;
  }

  .kv span:last-child{
    max-width:100%!important;
    text-align:left!important;
  }
}
</style>
"""


def inject_css():
    st.markdown(_CSS, unsafe_allow_html=True)


def style_matplotlib():
    """Clean, modern default look for every matplotlib chart in the app."""
    matplotlib.rcParams.update({
        "figure.facecolor": "white", "axes.facecolor": "white",
        "axes.edgecolor": LINE, "axes.labelcolor": MUTED, "axes.titlecolor": INK,
        "axes.titleweight": "bold", "axes.titlesize": 11, "axes.titlelocation": "left",
        "axes.spines.top": False, "axes.spines.right": False,
        "axes.grid": True, "grid.color": "#eef2f7", "grid.linewidth": .9, "axes.axisbelow": True,
        "xtick.color": MUTED, "ytick.color": MUTED, "font.size": 9,
        "legend.frameon": False, "axes.prop_cycle": matplotlib.cycler(color=CHART_COLORS),
        "figure.dpi": 110,
    })


# ── Components ────────────────────────────────────────────────────────────────
def _e(x):
    return html.escape(str(x))


def page_header(icon, title, sub=""):
    st.markdown(
        f'<div class="page-head"><div class="ph-row"><div class="ph-ico">{icon}</div>'
        f'<div><h1>{_e(title)}</h1><p>{_e(sub)}</p></div></div></div>',
        unsafe_allow_html=True)


def section(title, icon=""):
    st.markdown(f'<div class="section-title">{icon} {_e(title)}</div>', unsafe_allow_html=True)


def stat_cards(items):
    """items: list of (label, value, icon, hint, color_hex). hint/color optional."""
    out = ['<div class="stat-grid">']
    for it in items:
        label, value, icon = it[0], it[1], it[2]
        hint = it[3] if len(it) > 3 else ""
        color = it[4] if len(it) > 4 else PRIMARY
        out.append(
            f'<div class="stat" style="--c:{color}"><div class="ico">{icon}</div>'
            f'<div class="lbl">{_e(label)}</div><div class="val">{_e(value)}</div>'
            f'<div class="hint">{_e(hint)}</div></div>')
    out.append('</div>')
    st.markdown("".join(out), unsafe_allow_html=True)


def kv_card(title, rows):
    """rows: list of (label, value)."""
    body = "".join(f'<div class="kv"><span>{_e(k)}</span><span>{_e(v)}</span></div>' for k, v in rows)
    st.markdown(f'<div class="card"><h4>{_e(title)}</h4>{body}</div>', unsafe_allow_html=True)


def empty_state(icon, text):
    st.markdown(f'<div class="empty"><div class="e-ico">{icon}</div>{_e(text)}</div>', unsafe_allow_html=True)


def pill(text, kind="info"):
    return f'<span class="pill {kind}">{_e(text)}</span>'


def sidebar_collapsed():
    """Return the current SPEIS sidebar collapsed state."""
    return bool(st.session_state.get("speis_sidebar_collapsed", False))


def sidebar_brand():
    """Render the sidebar header and the full-sidebar collapse control."""
    if "speis_sidebar_collapsed" not in st.session_state:
        st.session_state.speis_sidebar_collapsed = False

    collapsed = bool(st.session_state.speis_sidebar_collapsed)
    toggle_icon = "▶" if collapsed else "◀"
    toggle_help = "Expand sidebar" if collapsed else "Minimize sidebar"

    # Apply a real class to the Streamlit sidebar so the ENTIRE sidebar
    # becomes a thin icon rail when collapsed.
    sidebar_class = "speis-sidebar-collapsed" if collapsed else "speis-sidebar-expanded"
    st.sidebar.markdown(
        f'<div class="speis-sidebar-state {sidebar_class}"></div>',
        unsafe_allow_html=True,
    )


    st.sidebar.markdown('<div class="sb-toggle-wrap">', unsafe_allow_html=True)
    if st.sidebar.button(toggle_icon, key="speis_sidebar_toggle", help=toggle_help):
        st.session_state.speis_sidebar_collapsed = not collapsed
        st.rerun()
    st.sidebar.markdown('</div>', unsafe_allow_html=True)

    st.sidebar.markdown(
        '<div class="sb-brand">'
        '<div class="sb-logo">🎓</div>'
        '<div class="sb-brand-text">'
        '<b>SPEIS</b>'
        '<small>School Intelligence Suite</small>'
        '</div>'
        '</div>',
        unsafe_allow_html=True
    )


def sidebar_user_chip(name, role_label):
    initials = "".join(
        w[0] for w in str(name).split()[:2]
    ).upper() or "?"

    st.sidebar.markdown(
        f'<div class="sb-user">'
        f'<div class="sb-avatar">{_e(initials)}</div>'
        f'<div class="sb-user-text">'
        f'<div class="n">{_e(name)}</div>'
        f'<div class="r">{_e(role_label)}</div>'
        f'</div>'
        f'</div>',
        unsafe_allow_html=True
    )


def sidebar_nav(options, key="speis_nav"):
    """Responsive SPEIS sidebar navigation.

    The actual page values remain unchanged.
    Only the displayed label changes when the sidebar is minimized.
    """

    if not options:
        return ""

    if key not in st.session_state or st.session_state[key] not in options:
        st.session_state[key] = options[0]

    collapsed = sidebar_collapsed()

    st.sidebar.markdown(
        '<div class="sb-label sb-nav-title">Navigation</div>',
        unsafe_allow_html=True
    )

    for i, option in enumerate(options):

        active = st.session_state[key] == option

        # Keep the original page value.
        # Only display the icon when collapsed.
        icon = option.split(" ", 1)[0] if " " in option else option
        display_label = icon if collapsed else option

        clicked = st.sidebar.button(
            display_label,
            key=f"{key}_{i}",
            width="stretch",
            type="primary" if active else "secondary",
            help=option if collapsed else None,
        )

        if clicked and st.session_state[key] != option:
            st.session_state[key] = option
            st.rerun()

    return st.session_state[key]

def login_hero():
    st.markdown("""
<div class="login-hero">
  <div class="logo">🎓</div>
  <h1>Student Performance &amp; Educational Intelligence</h1>
  <p>A digital assessment platform built for Sri Lankan schools.</p>
  <div class="feat"><i>📊</i><div><b>Marks &amp; analytics</b><span>Term, annual and class-wise insight</span></div></div>
  <div class="feat"><i>🎯</i><div><b>Career readiness</b><span>Track progress against career cut-offs</span></div></div>
  <div class="feat"><i>🔮</i><div><b>O/L &amp; A/L forecasts</b><span>Lightweight planning estimates</span></div></div>
  <div class="feat"><i>📄</i><div><b>Instant PDF reports</b><span>Generated securely in memory</span></div></div>
</div>""", unsafe_allow_html=True)
