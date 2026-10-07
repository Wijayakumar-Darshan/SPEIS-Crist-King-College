# SPEIS Update – 2026-10-04

## Teacher class-based access control
- Admin assignment now replaces the teacher's previous assignment, so the teacher has one current assigned Grade/Class.
- Teacher student lists, performance views, AI insights, career-path management and class-performance drill-downs use only the currently assigned class.
- Teacher mark editing is protected at the database layer and rejects attempts to save marks for students outside the assigned class.
- Teacher Excel upload is blocked when the workbook contains a class outside the current assignment.

## Student temporary credentials
- Student accounts created from Excel imports now retain the temporary password in a dedicated Admin-only credential table while `must_change_password=1`.
- Manually added students also receive a temporary login automatically if they do not already have a student account.
- Admin can view credentials under **Manage Users → Student Credentials**.
- Admin can reset a student's temporary password at any time.
- When a student changes their password, the plaintext temporary password is removed from the credential table.

## Credential PDF
- Admin can filter credentials by Grade and Class.
- A class-wise PDF can be downloaded containing Student ID, name, class, username, temporary password and credential status.

## Feedback / form behaviour
- Successful actions that rerun the Streamlit page use a flash message so the success message remains visible after the form disappears.
- Failed student saves, teacher assignments, account creation and mark saves show an activity-specific error without clearing the user's entered form data.
- Invalid mark submissions are rejected as a group; existing saved marks remain unchanged.

## Lightweight design
- No new heavyweight framework or service was introduced.
- The existing Streamlit + SQLite + in-memory PDF architecture is retained.

## Temporary Student Login Fix
- Fixed temporary student credentials being rejected with `Invalid credentials or role mismatch` when the stored password hash was out of sync with the Admin-visible temporary credential.
- `database.verify_login()` now checks the active temporary credential only for student accounts marked `must_change_password=1` and repairs the password hash after a successful temporary-credential authentication.
- Student first-login onboarding uses the same safe temporary-credential fallback for credentials issued by older SPEIS builds.
- Temporary credentials remain invalid after the student changes the password because the plaintext credential record is deleted.


## Temporary login reliability hardening – final
- Username lookup is now case-insensitive and ignores accidental leading/trailing spaces.
- Temporary credentials are matched by the linked student registration number and fall back to the credential username for older/migrated accounts.
- A valid active temporary credential repairs the student's bcrypt password hash and restores the student link when it is missing.
- Password changes remove the temporary credential by both registration number and username, preventing reuse.
- Role comparison at the login UI is normalized to avoid harmless case/whitespace mismatches.
- Streamlit CORS configuration was aligned with XSRF protection, removing the startup warning.

## 2026-10-04 – Temporary Student Password Fix (Final)
- Unified Student main-login and first-login temporary-password verification.
- Active Admin-issued temporary credentials are now authoritative until the student changes the password.
- Added copy/paste-safe normalization for invisible whitespace characters.
- Temporary credential lookup now works by student registration number or username for legacy accounts.
- A valid temporary credential automatically repairs the stored bcrypt hash and first-login flag.
- Removed dependency on a stale `must_change_password` flag when validating an active temporary credential.
- Student password changes still invalidate and remove the temporary credential.
