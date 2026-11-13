# Unit Test Report

Blood Bank Management System

- Date: 2026-11-08
- Code tested: c80a850 (main, after PR #50)
- Environment: Python 3.13.16, pytest 9.1.1, pytest-cov, Linux

- Command: `python -m pytest -v --junitxml=junit.xml`

## Summary

| Total | Passed | Failed | Skipped | Duration |
|---|---|---|---|---|
| 114 | 114 | 0 | 0 | 27.200 s |

## Results by test file

| Test file | Area | Tests | Passed | Failed | Time (s) |
|---|---|---|---|---|---|
| `tests/test_accounts.py` | Accounts, roles, signup, navigation | 19 | 19 | 0 | 5.16 |
| `tests/test_availability.py` | View / search availability | 8 | 8 | 0 | 1.93 |
| `tests/test_blood_issue.py` | Issue blood | 11 | 11 | 0 | 2.56 |
| `tests/test_donation_recording.py` | Record donation | 14 | 14 | 0 | 3.33 |
| `tests/test_donor_registration.py` | Register donor | 12 | 12 | 0 | 2.57 |
| `tests/test_management_logout.py` | Management logout | 1 | 1 | 0 | 0.36 |
| `tests/test_pbi12_operations.py` | Migrations, backup/restore, demo seed | 8 | 8 | 0 | 0.81 |
| `tests/test_reports_completion.py` | Reports and CSV export | 11 | 11 | 0 | 3.90 |
| `tests/test_reports_logout.py` | Reports logout | 1 | 1 | 0 | 0.33 |
| `tests/test_security_hardening.py` | Login throttling, timeout, audit, validation | 10 | 10 | 0 | 3.02 |
| `tests/test_validation.py` | Input validation | 19 | 19 | 0 | 2.16 |

## Individual results

### `tests/test_accounts.py` — Accounts, roles, signup, navigation

| Test | Result |
|---|---|
| `test_login_page_has_no_operational_menu_or_hours` | PASS |
| `test_login_password_has_accessible_show_hide_control` | PASS |
| `test_login_offers_signup_link_for_user_role` | PASS |
| `test_signup_page_loads` | PASS |
| `test_login_requires_selected_role_to_match_account` | PASS |
| `test_users_redirect_to_role_specific_landing_page` | PASS |
| `test_role_routes_and_navigation_are_restricted` | PASS |
| `test_first_management_setup_can_only_be_used_once` | PASS |
| `test_first_manager_is_sent_to_management_login_and_can_sign_in` | PASS |
| `test_login_requires_an_explicit_account_type` | PASS |
| `test_database_initialization_adds_account_fields_without_losing_users` | PASS |
| `test_user_signup_creates_account_and_allows_login` | PASS |
| `test_signup_rejects_password_mismatch_without_creating_account` | PASS |
| `test_signup_rejects_short_password` | PASS |
| `test_signup_rejects_duplicate_username` | PASS |
| `test_temporary_password_requires_change_before_using_other_pages` | PASS |
| `test_last_active_management_account_cannot_be_disabled` | PASS |
| `test_reset_password_requires_a_change_and_rejects_old_password` | PASS |
| `test_role_change_or_disabling_ends_existing_session` | PASS |

### `tests/test_availability.py` — View / search availability

| Test | Result |
|---|---|
| `test_ut01_no_filter_lists_every_group` | PASS |
| `test_ut02_search_valid_group_shows_only_that_group` | PASS |
| `test_ut03_zero_stock_message` | PASS |
| `test_ut04_invalid_group_rejected` | PASS |
| `test_it02_search_reflects_new_donation_immediately` | PASS |
| `test_st01_concurrent_readers_see_consistent_stock` | PASS |
| `test_st02_blank_criteria_returns_full_list` | PASS |
| `test_search_text_with_sql_is_just_invalid` | PASS |

### `tests/test_blood_issue.py` — Issue blood

| Test | Result |
|---|---|
| `test_ut01_issue_with_sufficient_stock` | PASS |
| `test_ut02_insufficient_stock_cancels_issue` | PASS |
| `test_ut03_zero_or_negative_quantity` | PASS |
| `test_ut04_no_stock_record` | PASS |
| `test_invalid_blood_group` | PASS |
| `test_it01_stock_decreases_by_issued_quantity` | PASS |
| `test_it02_issue_exact_stock_leaves_zero_and_search_shows_no_stock` | PASS |
| `test_it03_save_failure_leaves_stock_unchanged` | PASS |
| `test_stock_decrement_failure_rolls_back_issue_record` | PASS |
| `test_recipient_is_recorded_and_issue_reflected_in_availability` | PASS |
| `test_stock_can_never_go_negative_at_db_level` | PASS |

### `tests/test_donation_recording.py` — Record donation

| Test | Result |
|---|---|
| `test_ut01_valid_donation_recorded` | PASS |
| `test_confirmation_message_shown` | PASS |
| `test_ut02_unknown_donor` | PASS |
| `test_unknown_donor_offers_registration_link` | PASS |
| `test_invalid_input_rejected_and_stock_untouched[change0-Quantity must be greater than zero]` | PASS |
| `test_invalid_input_rejected_and_stock_untouched[change1-Quantity must be greater than zero]` | PASS |
| `test_invalid_input_rejected_and_stock_untouched[change2-Quantity exceeds maximum permissible donation limit]` | PASS |
| `test_invalid_input_rejected_and_stock_untouched[change3-Donation date cannot be in the future]` | PASS |
| `test_invalid_input_rejected_and_stock_untouched[change4-does not match the donor]` | PASS |
| `test_invalid_input_rejected_and_stock_untouched[change5-Invalid blood group selected]` | PASS |
| `test_it01_stock_increases_by_donated_quantity` | PASS |
| `test_it02_new_stock_record_created_for_new_group` | PASS |
| `test_it03_save_failure_rolls_back_donation_and_stock` | PASS |
| `test_st01_register_donate_then_stock_visible` | PASS |

### `tests/test_donor_registration.py` — Register donor

| Test | Result |
|---|---|
| `test_ut01_valid_donor_registered` | PASS |
| `test_invalid_input_rejected_and_not_saved[change0-Name is required]` | PASS |
| `test_invalid_input_rejected_and_not_saved[change1-Invalid blood group selected]` | PASS |
| `test_invalid_input_rejected_and_not_saved[change2-Age must be a positive number]` | PASS |
| `test_invalid_input_rejected_and_not_saved[change3-Age must be a positive number]` | PASS |
| `test_invalid_input_rejected_and_not_saved[change4-Donor must be at least 18 years old]` | PASS |
| `test_invalid_input_rejected_and_not_saved[change5-Enter a valid 10-digit phone number]` | PASS |
| `test_it01_registered_donor_is_listed` | PASS |
| `test_st01_new_donor_is_selectable_for_donation` | PASS |
| `test_donation_form_has_searchable_donor_selector` | PASS |
| `test_it02_duplicate_phone_rejected` | PASS |
| `test_sql_injection_text_is_stored_literally` | PASS |

### `tests/test_management_logout.py` — Management logout

| Test | Result |
|---|---|
| `test_management_pages_show_only_the_shared_logout_control` | PASS |

### `tests/test_pbi12_operations.py` — Migrations, backup/restore, demo seed

| Test | Result |
|---|---|
| `test_app_start_does_not_seed_demo_data_automatically` | PASS |
| `test_existing_data_survives_app_restart_and_migrations` | PASS |
| `test_backup_restore_recovers_database_and_saves_pre_restore_copy` | PASS |
| `test_restore_refuses_existing_database_without_confirmation` | PASS |
| `test_demo_seed_adds_complete_repeatable_dataset` | PASS |
| `test_seeded_demo_manager_can_log_in_and_is_prompted_to_change_password` | PASS |
| `test_demo_seed_rejects_password_shorter_than_eight_characters` | PASS |
| `test_database_migrations_are_idempotent_and_reject_unknown_version` | PASS |

### `tests/test_reports_completion.py` — Reports and CSV export

| Test | Result |
|---|---|
| `test_issue_and_combined_reports_include_issued_transaction` | PASS |
| `test_donation_report_filters_inclusive_date_range` | PASS |
| `test_issue_report_filters_by_inclusive_date_range` | PASS |
| `test_availability_report_shows_current_stock_snapshot` | PASS |
| `test_equal_or_reversed_date_ranges_show_required_message` | PASS |
| `test_empty_donation_issue_and_combined_reports_show_required_message` | PASS |
| `test_report_type_is_restricted_to_valid_options` | PASS |
| `test_only_management_can_generate_reports` | PASS |
| `test_recipient_cannot_generate_reports` | PASS |
| `test_csv_download_exports_selected_activity_without_contact_details` | PASS |
| `test_csv_download_rejects_invalid_date_range` | PASS |

### `tests/test_reports_logout.py` — Reports logout

| Test | Result |
|---|---|
| `test_reports_page_has_one_logout_control` | PASS |

### `tests/test_security_hardening.py` — Login throttling, timeout, audit, validation

| Test | Result |
|---|---|
| `test_five_failed_logins_block_account_until_lockout_expires` | PASS |
| `test_session_ends_after_fifteen_minutes_of_inactivity` | PASS |
| `test_generated_secret_key_is_persistent_and_not_a_fixed_fallback` | PASS |
| `test_app_uses_persistent_key_when_configuration_is_empty` | PASS |
| `test_underscored_age_huge_quantities_and_compact_dates_are_rejected` | PASS |
| `test_oversized_donation_numbers_and_compact_report_dates_are_rejected` | PASS |
| `test_audit_log_captures_sensitive_actions_without_passwords` | PASS |
| `test_failed_login_audit_does_not_store_password` | PASS |
| `test_request_larger_than_limit_returns_readable_413` | PASS |
| `test_management_account_changes_are_audited_without_temporary_passwords` | PASS |

### `tests/test_validation.py` — Input validation

| Test | Result |
|---|---|
| `test_phone_must_be_10_ascii_digits[]` | PASS |
| `test_phone_must_be_10_ascii_digits[12345]` | PASS |
| `test_phone_must_be_10_ascii_digits[98765432101]` | PASS |
| `test_phone_must_be_10_ascii_digits[98765abcde]` | PASS |
| `test_phone_must_be_10_ascii_digits[\u0669\u0669\u0669\u0669\u0669\u0669\u0669\u0669\u0669\u0669]` | PASS |
| `test_required_donor_fields_cannot_be_blank[name]` | PASS |
| `test_required_donor_fields_cannot_be_blank[age]` | PASS |
| `test_required_donor_fields_cannot_be_blank[blood_group]` | PASS |
| `test_required_donor_fields_cannot_be_blank[phone]` | PASS |
| `test_donor_age_must_be_positive_number[0]` | PASS |
| `test_donor_age_must_be_positive_number[-5]` | PASS |
| `test_donor_age_must_be_positive_number[abc]` | PASS |
| `test_invalid_donor_is_not_saved` | PASS |
| `test_donor_id_with_odd_characters_is_rejected_not_crashed` | PASS |
| `test_donation_date_cannot_be_in_the_future` | PASS |
| `test_issue_quantity_must_be_greater_than_zero[0]` | PASS |
| `test_issue_quantity_must_be_greater_than_zero[-1]` | PASS |
| `test_issue_quantity_must_be_greater_than_zero[abc]` | PASS |
| `test_issue_quantity_must_be_greater_than_zero[]` | PASS |

## Notes

- No failures or errors. Three `ResourceWarning` messages about unclosed SQLite connections come from the demo-seed tests and do not affect results.
- Lint: `ruff check .` passes.
- Test Plan mapping: see [`TEST_PLAN_EXECUTION.md`](TEST_PLAN_EXECUTION.md).
