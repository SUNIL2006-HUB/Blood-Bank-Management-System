from .v001_account_fields import migrate as migrate_account_fields
from .v002_security_tables import migrate as migrate_security_tables
from .v003_verified_recipient_signup import migrate as migrate_verified_recipient_signup
from .v004_demo_seed_state import migrate as migrate_demo_seed_state

MIGRATIONS = (
    (1, migrate_account_fields),
    (2, migrate_security_tables),
    (3, migrate_verified_recipient_signup),
    (4, migrate_demo_seed_state),
)
