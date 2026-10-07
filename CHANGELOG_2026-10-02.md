# SPEIS — Final Integration Changelog

- Preserved the supplied updated `app.py` student-registration/bulk-import logic.
- Added official per-subject O/L/A/L result history by exam year with A/B/C/S/W.
- Added explainable lightweight school/student pass-rate forecasting without sklearn.
- Added school O/L and A/L next-year estimates to Admin AI Predictions.
- Added student O/L and A/L forecast dashboard.
- Added teacher PDF export for an individual student's performance chart.
- Added student report ZIP pack containing available term, annual and performance PDFs.
- Added school forecast PDF.
- Added Streamlit production config and updated deployment documentation.
- Updated Prisma mirror schema to include the new exam-results model and fields.
- Verified all Python source files compile successfully.
- Verified SQLite initialization, student ID allocation, marks, exam results, forecasts and PDF generation with available runtime libraries.


## Career Path & AI Progress Update
- Added teacher-side student career-path management.
- Added current-vs-previous academic comparison against configured career cutoffs.
- Added improvement-priority insights for Teacher and Admin.
- Added downloadable Career Progress & Improvement PDF for both roles.


## Access-control and workflow update
- Admin class assignment now replaces the teacher's prior assignment, so reassignment is immediate.
- Teacher student, marks, reports, AI insight and career-path views are limited to assigned classes.
- Teacher Excel uploads are blocked if the workbook contains any unassigned class.
- The application continues to store password hashes only. Existing temporary passwords cannot be recovered from hashes; reset/reissue credentials rather than exposing stored plaintext passwords.
