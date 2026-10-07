# SPEIS UI Redesign — 2026-10-05

## School-focused professional UI refresh

This build introduces a full visual redesign while preserving the existing Streamlit application logic.

### Navigation
- Reworked the sidebar styling around Streamlit's native radio navigation.
- Removed the previous fragile visual treatment that could make navigation items behave inconsistently.
- Clear active-state indicator and hover state.
- Improved spacing, typography, click targets and scrollbar.
- Stable expanded sidebar width for desktop school-office use.
- Cleaner sign-out action.

### Visual system
- New school-friendly navy / blue / teal palette.
- Modern cards, statistics, forms, tables, tabs and alerts.
- Softer shadows and borders for a professional administrative feel.
- Improved page headers with restrained visual accents.
- Responsive layouts for smaller screens.

### Login
- Redesigned login hero to match the new school-management identity.
- Kept the existing login/authentication workflow unchanged.

### Compatibility
- No database schema changes.
- No authentication changes.
- No changes to marks, analytics, AI, reports or Excel import logic.
- `ui.py` and `app.py` pass Python syntax compilation.
- Requires the existing `requirements.txt` dependencies.
