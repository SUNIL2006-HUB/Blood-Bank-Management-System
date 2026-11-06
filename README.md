# Blood Bank Management System

Layered (presentation / service / repository / SQLite) Flask app. Requirements and design live in [`Documents/`](Documents/README.md).

## Run

```bash
pip install -r requirements.txt
flask --app app run --debug
```

Optional env vars (see `.env.example`): `SECRET_KEY` and `DATABASE_PATH` (default
`instance/bloodbank.db`). If `SECRET_KEY` is unset, the app creates a persistent random key file
beside the database; keep that file private and backed up. Create the first management account
through the one-time setup link on the login page. User accounts can sign up from the login page;
staff and additional management accounts are managed from the management Users page.

User signup creates an account with a username and password. Email verification is not required.

After five failed login attempts for the same username and client address within 15 minutes,
login is blocked for 15 minutes. Authenticated sessions expire after 15 minutes of inactivity.
Security-relevant authentication, account, donor, donation, issue, and report actions are written
to the audit log; passwords and session tokens are never recorded. Form input is validated on the
server, including strict date and numeric formats.

## Test

```bash
python -m pytest
```

## Implemented PBIs

| PBI | Feature | Routes |
| --- | --- | --- |
| PBI-01 | Donor Registration | `/donors/register`, `/donors` |
| PBI-02 | Donation Recording (+ automatic stock increase) | `/donations/new`, `/donations` |
| PBI-03 | View/Search Blood Availability | `/availability`, `/availability?blood_group=O+` |
| PBI-04 | Blood Issuance (+ automatic stock decrease) | `/issues/new`, `/issues` |
| PBI-05 | Donation & Availability Reporting | `/reports` (management role) |
| PBI-09 | User Accounts & Role-Based Access | `/auth/login`, `/auth/setup`, `/users` |
| PBI-10 | Security Hardening & Input Safety | Login throttling, session expiry, audit logging, strict input validation |

Donation reports accept optional inclusive start and end dates; leaving both blank includes all
donations. Availability reports show a current stock snapshot because the inventory table does not
store historical stock levels. Only logged-in management accounts can access report generation.

Login offers User, Staff, and Management account types; each role has access only to its permitted
pages. Newly created accounts must change their temporary password at first login.
