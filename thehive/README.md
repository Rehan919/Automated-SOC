# TheHive 5

## Bring up (after `.env` is filled)
```
docker compose -f thehive/docker-compose.yml up -d
```
Wait for all three services healthy (`docker compose ps`), then open
http://127.0.0.1:9000

## First login & MANDATORY password rotation
Default super-admin: `admin@thehive.local` / `secret`.
1. Log in, then immediately change the password to `THEHIVE_ADMIN_PASSWORD` (.env):
   profile menu -> Settings -> Password.
2. Create an organisation (e.g. `soc-lab`) and an org user/service account.

## API key for Shuffle (used in Task 10)
As the org user: profile -> Settings -> API keys -> Create.
Copy the key into `.env` as `THEHIVE_API_KEY`.

## Notes
- ES runs with xpack.security disabled (lab only, localhost bind).
- Cortex connector is added in Task 7 (compose `command` gains
  `--cortex-hostnames cortex --cortex-keys ${CORTEX_API_KEY}`,
  replacing `--no-config-cortex`).