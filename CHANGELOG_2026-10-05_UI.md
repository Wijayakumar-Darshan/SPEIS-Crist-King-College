# SPEIS UI Refresh – 2026-10-05

UI-only change. Database, authentication, parsing, AI and PDF logic are untouched.

- New `ui.py` design system: theme CSS, matplotlib chart style, reusable components.
- Login: split-screen hero + sign-in card, horizontal role picker.
- Sidebar: brand, user avatar chip, pill-style navigation, sign-out button.
- Page headers: gradient header with icon; compact section titles replace oversized headings.
- Dashboards: stat cards (Admin, Teacher, Student); Admin grade-average chart.
- Student: new Overview page; profile shown as clean key/value cards.
- Charts: unified indigo/amber palette, no top/right borders, light grid.
- Sidebar toggle no longer hidden (previously the whole header was hidden).
- Mobile-responsive tweaks, empty states, themed tabs/inputs/buttons.
- `requirements.txt`: streamlit>=1.50 (code already used `width="stretch"`).
- `.streamlit/config.toml`: light theme added.
