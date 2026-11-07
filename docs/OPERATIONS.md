# Operations

## Database and migrations

The application stores data in the SQLite file selected by `DATABASE_PATH`; the default is
`instance/bloodbank.db`. Each app startup applies any pending, versioned migrations in order and
records them in `schema_migrations`. Existing donor, donation, issue, stock, and account rows are
preserved. Keep the database file and the adjacent `instance/.secret_key` private.

## Back up and restore

Run commands from the repository root. Backups use SQLite's online backup API and are integrity
checked after creation. If no destination is specified, a UTC timestamped backup is created beside
the database.

```powershell
python scripts\manage_db.py backup .\instance\before-upgrade.backup
```

For restore, stop the Flask/Gunicorn process first and point `DATABASE_PATH` at the intended
database. Restore refuses to replace an existing database unless `--yes` is supplied. When it
replaces one, it first writes and verifies a uniquely named `.pre-restore` safety backup.

```powershell
$env:DATABASE_PATH = ".\instance\bloodbank.db"
python scripts\manage_db.py restore .\instance\before-upgrade.backup --yes
```

Copy backups to protected storage separate from the machine or Docker volume that contains the
live database. The database backup does not include `.secret_key`; keep a separate secure copy of
that key if restoring to a new data directory and preserving existing sessions is required.

## Demo dataset

Seeding is explicit and is never part of app startup. Run the command in an interactive terminal;
it prompts for a password without echoing it. Use a unique password of at least 8 characters.

```powershell
python scripts\manage_db.py seed-demo
```

The command inserts 25 donors, 25 donations, eight issues, nonzero stock for all eight blood
groups, and `demo_manager`, `demo_staff`, and `demo_recipient` accounts. The provided password is
stored as a password hash. All three demo accounts are marked to require a password change at
first login. The operation is one transaction and a database marker makes subsequent runs no-ops.
It refuses to proceed if reserved demo usernames or donor phone numbers are already present but
there is no completed seed marker; resolve the collision rather than overwriting existing records.

## Docker persistence

The image stores the database and generated secret key under `/data`. Mount a named or bind volume
there so data survives container replacement:

```powershell
docker build -t blood-bank:local .
docker volume create bloodbank_data
docker run -d --name blood-bank -p 8000:8000 `
  -e SECRET_KEY="<provide-a-private-random-secret>" `
  -v bloodbank_data:/data blood-bank:local
```

The named volume contains both `/data/bloodbank.db` and `/data/.secret_key`. Back up data outside
the container:

```powershell
docker exec blood-bank python scripts/manage_db.py backup /data/bloodbank.backup
docker cp blood-bank:/data/bloodbank.backup .\bloodbank.backup
```

To restore, stop the running application first, put the backup file in the current directory,
then run a one-off container with the same volume:

```powershell
docker stop blood-bank
docker run --rm -v bloodbank_data:/data -v "${PWD}:/backups:ro" `
  -e DATABASE_PATH=/data/bloodbank.db blood-bank:local `
  python scripts/manage_db.py restore /backups/bloodbank.backup --yes
docker start blood-bank
```

Run the demo seed in a terminal attached to the container so the password prompt remains private:

```powershell
docker exec -it blood-bank python scripts/manage_db.py seed-demo
```

## Test and lint

From the repository root:

```powershell
python -m pytest
ruff check .
```

The suite uses temporary SQLite databases. It includes migration/data-preservation, restart,
backup/restore, idempotent demo seeding, account/role/menu/signup, reporting, login throttling, and
session inactivity-expiry coverage.
