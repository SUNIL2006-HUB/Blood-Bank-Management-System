# Deviations from the Submitted Documents

Blood Bank Management System — status after **Sprint-1** (PBI-01 to PBI-04).
Compared against the submitted SRS, Software Architecture (SAD), Use Case Flow, Security Requirements and Test Plan.

Legend: **Added** = implemented but not in the documents · **Changed** = implemented differently from the documents · **Deferred** = in the documents, planned for Sprint-2.

| # | Area | Documents say | Implementation | Type | Reason / plan |
|---|------|---------------|----------------|------|---------------|
| 1 | Technology | SAD describes a layered 3-tier web architecture and does not name a stack | Python Flask web app with SQLite. Layers match the SAD: routes (presentation) → services (business logic) → repositories (data access) → database | Choice | Documents left the stack open. SQLite needs no server setup |
| 2 | Login and roles (NFR-04, SEC-01, SEC-04, SEC-05) | Users log in; staff, recipient/hospital and management have different access | No login or roles yet. Every screen is open | Deferred | PBI-07 (Sprint-2). Test cases that need roles (Issue Blood ST_02, "Staff is logged in" pre-conditions, hospital read-only IT_01) are verified for behaviour only, not for access control |
| 3 | Reports (UC6, FR-08) | Management generates donation and availability reports | Not implemented | Deferred | PBI-05 (Sprint-2). Issue Blood ST_01 (issue appears in a report) cannot run until then |
| 4 | Security extras (SEC-02, 03, 09, 10, 11, 14) | Password hashing, login throttling, session timeout, HTTPS, audit logging, backup procedure | Not implemented | Deferred | Depend on login (PBI-07). Audit logging and backup are optional backlog items |
| 5 | Donor age (UT_05) | Minimum age 18 | Minimum 18 **and** maximum 65 | Added | Common donation-eligibility rule; stored as constants `MIN_DONOR_AGE`/`MAX_DONOR_AGE` |
| 6 | Maximum donation (UT_04) | Test uses 600 ml as "exceeds the maximum permissible limit" | Limit set to 500 ml per donation | Choice | Documents give no exact limit; 500 ml is below the 600 ml test value, so UT_04 behaves as expected |
| 7 | Donation blood group (UC2 step 5) | Staff enter blood group, quantity and date | Blood group must also match the donor's registered group, otherwise rejected | Added | Prevents wrong stock being added |
| 8 | Donor identification (UC2 steps 2–4) | System requests donor identification | Donor is chosen from a dropdown list. An unknown donor ID (UT_02) can only happen on a hand-made request; it shows "Donor not found" and a link to register the donor | Changed | Simpler and avoids typing mistakes. The error path is covered by automated tests |
| 9 | Issue form (UC5 step 2) | Staff enter blood group and quantity | Extra optional field: recipient / hospital name | Added | The Security Requirements list issue records of who received blood |
| 10 | Availability list (UC4) | Full list of blood groups and quantities | All 8 groups are always shown, with 0 ml for groups that have no stock record | Choice | Gives a complete view; search on a zero-stock group shows "No stock available for <group>" |
| 11 | Test execution | Test Plan is a manual plan with blank "Actual Result" columns | Most Sprint-1 test cases are also automated with pytest (43 tests in total). Save-failure cases (Donation IT_03, Issue IT_03) are simulated in code | Added | Tests run automatically in GitHub Actions on every pull request |
| 12 | Delivery pipeline | Not in the documents | GitHub Actions CI (lint, tests on Python 3.11/3.12, secret scan), CD that builds a Docker image, Dependabot, PR template and CODEOWNERS | Added | Sprint-1 requirement to automate pull requests and commits |

## Test Plan coverage in Sprint-1

| Module | Test cases implemented |
|--------|------------------------|
| Register Donor | UT_01–UT_06, IT_01, IT_02 (ST_01 "donor selectable in Record Donation" is checked manually in the demo) |
| Record Donation | UT_01–UT_05, IT_01–IT_03, ST_01 |
| View/Search Availability | UT_01–UT_04, IT_02, IT_03, ST_01, ST_02 (IT_01 "hospital read-only access" needs login, so it is only checked as a read-only page) |
| Issue Blood | UT_01–UT_04, IT_01–IT_03 (ST_01 needs reports, ST_02 needs login) |

## To update in Sprint-2
Re-check rows 2, 3 and 4 when PBI-05, PBI-06, PBI-07 and PBI-08 are merged, and add any new deviations.
