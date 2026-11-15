# Deviations from the Submitted Documents

Blood Bank Management System — final deviations after Sprint-1, Sprint-2 and Sprint-3.
Compared against the submitted SRS, Software Architecture (SAD), Use Case Flow, Security Requirements and Test Plan.

Legend: **Added** = implemented but not in the documents · **Changed** = implemented differently from the documents · **Choice** = the documents left it open · **Not implemented** = in the documents, left out, with the reason.

## A. Technology and design

| # | Area | Documents say | Implementation | Type | Reason |
|---|------|---------------|----------------|------|--------|
| 1 | Technology | SAD describes a layered 3-tier web architecture and does not name a stack | Python Flask web app with SQLite. Layers match the SAD: routes (presentation) → services (business logic) → repositories (data access) → database | Choice | Documents left the stack open. SQLite needs no server setup |
| 2 | Database changes | Not in the documents | Numbered, transactional migrations (`app/migrations/`) with a `schema_migrations` table | Added | Lets the database be upgraded without losing records |

## B. Functional behaviour

| # | Area | Documents say | Implementation | Type | Reason |
|---|------|---------------|----------------|------|--------|
| 3 | Donor age (UT_05) | Minimum age 18 | Minimum 18 **and** maximum 65 | Added | Common donation-eligibility rule; stored as constants `MIN_DONOR_AGE` / `MAX_DONOR_AGE` |
| 4 | Maximum donation (UT_04) | Test uses 600 ml as "exceeds the maximum permissible limit" | Limit set to 500 ml per donation | Choice | Documents give no exact limit; 500 ml is below the 600 ml test value, so UT_04 behaves as expected |
| 5 | Donation blood group (UC2 step 5) | Staff enter blood group, quantity and date | Blood group must also match the donor's registered group, otherwise rejected | Added | Prevents wrong stock being added |
| 6 | Donor identification (UC2 steps 2–4) | System requests donor identification | Donor is chosen from a dropdown list. An unknown donor ID (UT_02) can only happen on a hand-made request; it shows "Donor not found" and a link to register the donor | Changed | Simpler and avoids typing mistakes |
| 7 | Issue form (UC5 step 2) | Staff enter blood group and quantity | Extra optional field: recipient / hospital name | Added | The Security Requirements list issue records of who received blood |
| 8 | Availability list (UC4) | Full list of blood groups and quantities | All 8 groups are always shown, with 0 ml for groups that have no stock record | Choice | Gives a complete view; search on a zero-stock group shows "No stock available for <group>" |
| 9 | Reports (UC6, FR-08) | Management generates donation and availability reports | Management-only donation, issue, combined activity and current availability reports, with date filtering | Changed | Issue and combined reports were added so that issued blood appears in a report (Issue Blood ST_01) |
| 10 | Report export | Not in the documents | Reports can be downloaded as CSV | Added | Lets management use the data in a spreadsheet |
| 11 | Operating hours | Not in the documents | None. An "open / closed" banner with fixed hours was tried in Sprint-1 and removed in Sprint-3 | Not implemented | The SRS defines no operating hours, so the banner invented a rule |

## C. Accounts, roles and security

| # | Area | Documents say | Implementation | Type | Reason |
|---|------|---------------|----------------|------|--------|
| 12 | Login and roles (NFR-04, SEC-01, SEC-04, SEC-05) | Users log in; staff, recipient/hospital and management have different access | Login page offers User (recipient), Staff and Management; the choice is checked against the account's real role. Menus and routes depend on the role. Logged-out visitors see only the login page | Added | Sprint-2/3 (PBI-07, PBI-09) |
| 13 | Account creation | Not specified | Recipients / hospital users sign up themselves on the login page. Staff and management accounts are created by management only. The first management account is created on a first-run setup page | Added | A recipient sees only blood group and quantity, so open signup is low risk. Staff and management need controlled access |
| 14 | Passwords | SEC-02: password hashing | Passwords are hashed (scrypt) and need at least 8 characters. Accounts created by management must change the password at first login | Added | Meets SEC-02 and avoids shared default passwords |
| 15 | Login throttling, session timeout (SEC-03, SEC-09) | Limit failed logins; expire idle sessions | 5 failed logins in 15 minutes lock the login for a while; sessions expire after 15 minutes of inactivity; the account is re-checked on every request | Added | PBI-10 |
| 16 | Audit logging (SEC-11) | Audit log of important actions | Logins (success, failure, blocked), account creation and changes, donor registration, donations, issues, report generation and password changes are written to an `audit_log` table | Added | PBI-10 |
| 17 | Backup and restore (SEC-14) | Backup procedure | Verified SQLite backup and restore commands (`scripts/manage_db.py`), with a safety backup before every restore. A repeatable demo-data seed is also provided | Added | PBI-12 |
| 18 | Input safety | Not specified in detail | Server-side validation of all forms, parameterised SQL queries, SameSite session cookies | Added | PBI-10 |

## D. Planned in the documents but not implemented

| # | Area | Documents say | Implementation | Type | Reason |
|---|------|---------------|----------------|------|--------|
| 19 | HTTPS (SEC-10) | HTTPS for all traffic | The application serves plain HTTP. HTTPS is expected to be provided by the hosting layer (for example a reverse proxy). The Docker image was not built or tested in the final environment | Not implemented | Deployment setting, not application code. Not part of the demo |
| 20 | Email one-time password | Raised during planning, not in the SRS | Not built. An unused database table and columns for it (migration v003) remain | Not implemented | Out of scope for the semester. Kept only to avoid breaking databases that already ran the migration |
| 21 | CSRF tokens | Not specified | Not implemented. SameSite cookies give partial protection | Not implemented | Listed as a known limitation |
| 22 | Change password | Not specified | A logged-in user can change their password without entering the old one | Not implemented | Known limitation; low risk because the session is already authenticated |
| 23 | Audit log viewer | Not specified | The audit log is stored but there is no page to view it | Not implemented | Known limitation; the data can be read from the database |
| 24 | Username case | Not specified | Usernames are case-sensitive, so `Admin` and `admin` can both exist | Not implemented | Known limitation |

## E. Process and tooling

| # | Area | Documents say | Implementation | Type | Reason |
|---|------|---------------|----------------|------|--------|
| 25 | Test execution | Test Plan is a manual plan with 44 cases | All 44 cases were also automated and run; all pass. 38 more cases were added for accounts, roles, security, CSV export, operations and non-functional requirements (37 pass, 1 not run: HTTPS). The whole automated suite has 114 tests, with 92% statement and 78.6% branch coverage. Save-failure cases (Donation IT_03, Issue IT_03) are simulated in code. Results are in the Test Plan and in `docs/` (Unit Test Report, System Validation Report, coverage screenshots) | Added | Tests run automatically in GitHub Actions on every pull request |
| 26 | Delivery pipeline | Not in the documents | GitHub Actions CI (lint, tests on Python 3.11 and 3.12, secret scan), CD that builds a Docker image, Dependabot, PR template and CODEOWNERS | Added | Sprint-1 requirement to automate pull requests and commits |
| 27 | Sprint-3 | Two sprints were planned | A third sprint was added for the work that spilled over: accounts and roles (PBI-09), security (PBI-10), reporting (PBI-11) and persistence and demo data (PBI-12) | Added | Allowed for spill-over work by the course |
| 28 | Documents | SRS, SAD and Test Plan were first written in our own layout | The SRS, SAD and Test Plan were rewritten in the course templates to match the final system. They add requirements FR-09 to FR-19, NFR-05, NFR-06, security objectives, STRIDE, API tables, sequence diagrams and a traceability matrix | Changed | The course provided templates for the final submission; the documents now match the implementation |

## Sprint summary

| Sprint | What it delivered |
|--------|-------------------|
| Sprint-1 | Register donor, record donation, view and search availability, issue blood, CI/CD |
| Sprint-2 | First login and role work, reports |
| Sprint-3 | Final accounts and role-based access, security hardening, report completion with CSV, data persistence, backup/restore and demo data |
