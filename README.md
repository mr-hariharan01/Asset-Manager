# Asset Manager

## Environment Configuration

Set these environment variables before running the Flask app:

- `SECRET_KEY` (required in production): Flask session signing key.
- `ENABLE_DEMO_SEED` (optional): Must be set to `true` to allow demo-user seeding.
- `FLASK_ENV` / `APP_ENV` / `ENV` (optional): If set to `production`, demo-user seeding is blocked.

Example:

```bash
export SECRET_KEY='replace-with-a-strong-secret'
export FLASK_APP=app.py
```

## Demo User Seeding

Demo seeding is intentionally **not** executed during module import or app startup.
It must be triggered explicitly and is only allowed when:

1. `ENABLE_DEMO_SEED=true`
2. Environment is **not** production (`FLASK_ENV`, `APP_ENV`, or `ENV` not equal to `production`)

Run one of the dedicated seed commands:

```bash
ENABLE_DEMO_SEED=true flask --app app seed-demo-users
```

or

```bash
ENABLE_DEMO_SEED=true python scripts/seed_demo_users.py
```
