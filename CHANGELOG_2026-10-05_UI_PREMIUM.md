# SPEIS Premium UI Refresh — 2026-10-05

## What changed
- Reworked the shared UI layer for a premium dark-professional school administration experience.
- Sidebar navigation now uses stable Streamlit buttons and no longer depends on private radio DOM/CSS.
- Added a visible sidebar-collapsed control so users can reopen the sidebar when a browser session has it collapsed.
- Increased workspace width and removed the overly narrow centered content effect.
- Improved page headers, cards, statistics, forms, tabs, alerts, tables and chart surfaces.
- Improved sidebar spacing, active navigation state, profile card and sign-out area.
- Added responsive breakpoints for desktop, tablet and mobile.
- Kept existing database, authentication, AI, marks, reports and navigation logic intact.

## Localhost vs network URL
Streamlit stores sidebar expanded/collapsed state per browser session. Therefore localhost and a network URL can show different sidebar states even when the application code is identical. This version adds a visible collapsed-sidebar control and keeps `initial_sidebar_state="expanded"`.

## Run
```powershell
streamlit run app.py
```
