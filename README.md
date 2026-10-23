# Blood Bank Management System

Layered (presentation / service / repository / SQLite) Flask app. Requirements and design live in [`Documents/`](Documents/README.md).

## Run

```bash
pip install -r requirements.txt
flask --app app run --debug
```

Optional env vars (see `.env.example`): `SECRET_KEY`, `DATABASE_PATH` (default `instance/bloodbank.db`).

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
