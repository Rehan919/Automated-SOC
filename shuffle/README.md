# Shuffle SOAR

## Setup
```
copy shuffle\.env.example shuffle\.env       # then replace every CHANGE_ME
docker compose -f shuffle/docker-compose.yml up -d
```
Open http://127.0.0.1:3001 and log in with SHUFFLE_DEFAULT_USERNAME / SHUFFLE_DEFAULT_PASSWORD.

## Verify (Task 8 demo)
Create a workflow with a single "Repeat back to me" action and run it once.

## Notes
- OpenSearch is internal-only (not published) to avoid clashing with the Wazuh
  indexer on 9200. UI=3001, backend API=5001 (bound to 127.0.0.1).
- `OPENSEARCH_INITIAL_ADMIN_PASSWORD` and `SHUFFLE_OPENSEARCH_PASSWORD` must match.
- The webhook trigger created in Task 9 yields a URL like
  http://shuffle-backend:5001/api/v1/hooks/webhook_<id> -> put it in the root
  .env as SHUFFLE_WEBHOOK_URL (used by the Wazuh integration).