# System Validation Report

Blood Bank Management System

- Date: 2026-11-08
- Code tested: c80a850 (main, after PR #50)
- Environment: Python 3.13.16, pytest 9.1.1, pytest-cov, Linux
- Method: the Test Plan's 44 cases (unit, integration and system level) executed against the running Flask application with a fresh database per case. Each case records the HTTP result, database state and message checked.


## Summary

| Total Test Plan cases | Passed | Failed |
|---|---|---|
| 44 | 44 | 0 |

| Module | Cases | Passed |
|---|---|---|
| Register Donor | 9 | 9 |
| Record Donation | 9 | 9 |
| View / Search Availability | 9 | 9 |
| Issue Blood | 9 | 9 |
| Reports | 8 | 8 |

## Register Donor

| Case | Result | Evidence observed |
|---|---|---|
| UT_01 | PASS | HTTP 302; rows=1; msg=Donor registered successfully |
| UT_02 | PASS | HTTP 400; saved=0; shows 'Name is required': True |
| UT_03 | PASS | HTTP 400; saved=0; shows 'Invalid blood group selected': True |
| UT_04 | PASS | HTTP 400; saved=0; shows 'Age must be a positive number': True |
| UT_05 | PASS | HTTP 400; saved=0; shows 'Donor must be at least 18 years old': True |
| UT_06 | PASS | HTTP 400; saved=0; shows 'Enter a valid 10-digit phone number': True |
| IT_01 | PASS | donor listed in /donors |
| IT_02 | PASS | HTTP 400; rows=1 |
| ST_01 | PASS | donor appears in Record Donation list |

## Record Donation

| Case | Result | Evidence observed |
|---|---|---|
| UT_01 | PASS | HTTP 302; confirmation shown |
| UT_02 | PASS | HTTP 400; 'Donor not found' shown: True |
| UT_03 | PASS | HTTP 400; saved=0; msg shown: True |
| UT_04 | PASS | HTTP 400; saved=0; msg shown: True |
| UT_05 | PASS | HTTP 400; saved=0; msg shown: True |
| IT_01 | PASS | stock=2350 |
| IT_02 | PASS | stock record AB-=350 |
| IT_03 | PASS | HTTP 200; donations=0; stock=None; msg= Record donation · Blood Bank Management body{font-family:system-ui,sans-serif;margin:0;color:#222;b |
| ST_01 | PASS | stock=350; visible on availability page: True |

## View / Search Availability

| Case | Result | Evidence observed |
|---|---|---|
| UT_01 | PASS | all 8 groups listed |
| UT_02 | PASS | O+ 1500 shown; A+ hidden=True |
| UT_03 | PASS | msg shown=True |
| UT_04 | PASS | HTTP 400; msg=True |
| IT_01 | PASS | view=200; register donor=403; issue page=403 |
| IT_02 | PASS | O+ 350 visible immediately |
| IT_03 | PASS | stock=250 |
| ST_01 | PASS | identical responses: True |
| ST_02 | PASS | HTTP 200 |

## Issue Blood

| Case | Result | Evidence observed |
|---|---|---|
| UT_01 | PASS | HTTP 302; stock=2000; msg=confirmation |
| UT_02 | PASS | HTTP 400; issues saved=0; msg shown=True |
| UT_03 | PASS | HTTP 400; issues saved=0; msg shown=True |
| UT_04 | PASS | HTTP 400; issues saved=0; msg shown=True |
| IT_01 | PASS | stock=2000 |
| IT_02 | PASS | HTTP 302; stock=0 |
| IT_03 | PASS | HTTP 200; issues=0; stock=2350 |
| ST_01 | PASS | issue report type available: True; HTTP 200; report_type 'issue' ->  Generate reports · Blood Bank Management body{font-family:system-ui,sans-serif;margin:0;c |
| ST_02 | PASS | GET=403; POST=403 |

## Reports

| Case | Result | Evidence observed |
|---|---|---|
| UT_01 | PASS | HTTP 200; only August donation listed |
| UT_02 | PASS | HTTP 200; O+ 550 shown=True |
| UT_03 | PASS | HTTP 200; both donations listed |
| UT_04 | PASS | HTTP 400; error shown: '['Invalid date range']' |
| IT_01 | PASS | shows: clusive) Generate report Download CSV Donation report 0 donations · 0 ml total No records found for the selected period |
| IT_02 | PASS | HTTP 200; 2026-08-10 Ramesh Kumar O+ 350 2026-09-15 Ramesh Kumar O+ 200 Issues No issues found for the selected period. |
| ST_01 | PASS | GET=200; POST=200 |
| ST_02 | PASS | staff=403; hospital=403; anonymous=302 |

## Failures found and fixed during the testing period

The first execution of this Test Plan on `main` as merged at the end of Sprint-2 passed 35 of 44 cases. The nine failures, their causes and how they were solved:

| Failed case(s) | Why it failed | How it was solved | Result |
|---|---|---|---|
| Reports UT_01, UT_02, UT_03, ST_01, ST_02 | A merge conflict dropped the reports blueprint registration, so `/reports` returned 404 and every page crashed with HTTP 500 for a management user | Restored the import and `register_blueprint` call; added regression tests for management page access and for 200 / 403 on reports | Passed |
| Reports UT_04, IT_01 | Error and empty-result messages did not match the wording in the Test Plan | Messages changed to the Test Plan wording | Passed |
| Reports IT_02 | No combined donation + issue report existed | Combined activity report added (PBI-11) | Passed |
| Issue Blood ST_01 | Issued blood never appeared in any report | Issue and combined reports added (PBI-11) | Passed |

After the fixes and the Sprint-3 stories (PBI-09 roles, PBI-10 security, PBI-11 reporting) were merged, the Test Plan was re-run and passed 44 of 44. It still passes 44 of 44 on current `main`.

## Limitations

- Cases are driven through Flask's test client, not a human using a browser. A separate browser-driven check (Playwright) of the main flows also passed.
- HTTPS (SEC-10) is a deployment setting and is not exercised here.
