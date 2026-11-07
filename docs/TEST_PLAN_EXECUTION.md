# Test Plan Execution Record

Execution date: 2026-11-07
Branch: `feature/pbi-12-persistence-quality`
Method: automated pytest regressions mapped to each documented Test Plan scenario. This records
automated verification; it is not a claim that a person manually clicked through all 44 UI flows.

## Donor Registration

| Test Plan case | Actual result | Automated evidence |
|---|---|---|
| UT_01 | PASS — valid donor saved and confirmation shown | `test_ut01_valid_donor_registered` |
| UT_02 | PASS — blank name rejected without saving | `test_invalid_input_rejected_and_not_saved[change0]` |
| UT_03 | PASS — invalid blood group rejected without saving | `test_invalid_input_rejected_and_not_saved[change1]` |
| UT_04 | PASS — negative age rejected without saving | `test_invalid_input_rejected_and_not_saved[change2]` |
| UT_05 | PASS — underage donor rejected without saving | `test_invalid_input_rejected_and_not_saved[change4]` |
| UT_06 | PASS — invalid phone rejected without saving | `test_invalid_input_rejected_and_not_saved[change5]` |
| IT_01 | PASS — saved donor appears in donor records | `test_it01_registered_donor_is_listed` |
| IT_02 | PASS — duplicate phone rejected | `test_it02_duplicate_phone_rejected` |
| ST_01 | PASS — newly registered donor appears in donation selector | `test_st01_new_donor_is_selectable_for_donation` |

## Donation Recording

| Test Plan case | Actual result | Automated evidence |
|---|---|---|
| UT_01 | PASS — valid donation saved | `test_ut01_valid_donation_recorded` |
| UT_02 | PASS — unknown donor rejected | `test_ut02_unknown_donor` |
| UT_03 | PASS — zero quantity rejected | `test_invalid_input_rejected_and_stock_untouched[change0]` |
| UT_04 | PASS — quantity over limit rejected | `test_invalid_input_rejected_and_stock_untouched[change2]` |
| UT_05 | PASS — future donation date rejected | `test_invalid_input_rejected_and_stock_untouched[change3]` |
| IT_01 | PASS — donation increases stock by its quantity | `test_it01_stock_increases_by_donated_quantity` |
| IT_02 | PASS — missing stock row is created | `test_it02_new_stock_record_created_for_new_group` |
| IT_03 | PASS — save failure rolls back donation and stock | `test_it03_save_failure_rolls_back_donation_and_stock` |
| ST_01 | PASS — registered donor can donate and updated stock appears in availability | `test_st01_register_donate_then_stock_visible` |

## Availability Viewing

| Test Plan case | Actual result | Automated evidence |
|---|---|---|
| UT_01 | PASS — unfiltered view lists all eight blood groups | `test_ut01_no_filter_lists_every_group` |
| UT_02 | PASS — valid group filter returns the selected group | `test_ut02_search_valid_group_shows_only_that_group` |
| UT_03 | PASS — zero-stock result is explained | `test_ut03_zero_stock_message` |
| UT_04 | PASS — invalid group filter rejected | `test_ut04_invalid_group_rejected` |
| IT_01 | PASS — recipient role can view availability | `test_role_routes_and_navigation_are_restricted` |
| IT_02 | PASS — new donation is reflected in availability | `test_it02_search_reflects_new_donation_immediately` |
| IT_03 | PASS — issued quantity is reflected in availability | `test_recipient_is_recorded_and_issue_reflected_in_availability` |
| ST_01 | PASS — concurrent readers see the same stock snapshot | `test_st01_concurrent_readers_see_consistent_stock` |
| ST_02 | PASS — blank search criteria returns the complete list | `test_st02_blank_criteria_returns_full_list` |

## Blood Issuance

| Test Plan case | Actual result | Automated evidence |
|---|---|---|
| UT_01 | PASS — issue succeeds when stock is sufficient | `test_ut01_issue_with_sufficient_stock` |
| UT_02 | PASS — insufficient stock prevents issue | `test_ut02_insufficient_stock_cancels_issue` |
| UT_03 | PASS — zero quantity rejected | `test_ut03_zero_or_negative_quantity` |
| UT_04 | PASS — missing stock row prevents issue | `test_ut04_no_stock_record` |
| IT_01 | PASS — issue decreases stock by its quantity | `test_it01_stock_decreases_by_issued_quantity` |
| IT_02 | PASS — issuing exact stock leaves zero | `test_it02_issue_exact_stock_leaves_zero_and_search_shows_no_stock` |
| IT_03 | PASS — save failure rolls back issue and stock change | `test_it03_save_failure_leaves_stock_unchanged` |
| ST_01 | PASS — issued activity appears in issue and combined reports | `test_issue_and_combined_reports_include_issued_transaction` |
| ST_02 | PASS — recipient role cannot access issue actions | `test_role_routes_and_navigation_are_restricted` |

## Reporting

| Test Plan case | Actual result | Automated evidence |
|---|---|---|
| UT_01 | PASS — donation report honors a valid inclusive date range | `test_donation_report_filters_inclusive_date_range` |
| UT_02 | PASS — availability report shows current stock snapshot | `test_availability_report_shows_current_stock_snapshot` |
| UT_03 | PASS — donation, issue, and combined reports work without a date range | `test_issue_and_combined_reports_include_issued_transaction` |
| UT_04 | PASS — equal or reversed date range rejected | `test_equal_or_reversed_date_ranges_show_required_message` |
| IT_01 | PASS — empty period reports a clear no-records result | `test_empty_donation_issue_and_combined_reports_show_required_message` |
| IT_02 | PASS — combined report includes donations and issues | `test_issue_and_combined_reports_include_issued_transaction` |
| ST_01 | PASS — management can generate reports | `test_issue_and_combined_reports_include_issued_transaction` |
| ST_02 | PASS — staff and recipient roles cannot generate reports | `test_only_management_can_generate_reports`, `test_recipient_cannot_generate_reports` |

## PBI-12 verification and outcomes

The full automated suite completed with **113 passed**. It includes account login, role permissions,
navigation menus, signup, Users-page behavior, report access, login throttling, session inactivity
expiry, and the PBI-12 operations tests for schema versions, existing-data preservation, app restart,
verified backup/restore, and repeatable demo seeding. `ruff check .` and `git diff --check` also
passed.

The command-line smoke check created a verified backup, restored it over an existing temporary
database with `--yes`, and confirmed that the pre-restore safety backup was produced.

The first targeted backup/restore run exposed a Windows file-lock failure: SQLite's connection
context manager commits but does not close the connection. The integrity-check helper was changed
to close its connection explicitly; the focused tests and subsequent full suite passed.

No unresolved test failures remain. The test plan's UI flows were verified by their automated
functional equivalents listed above; no separate manual browser session was recorded.
