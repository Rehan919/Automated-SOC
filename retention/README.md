# Retention: hot -> cold (forensic)

## Hot (Wazuh indexer, 30 days)
Apply the ISM policy once the indexer is up:
```
bash retention/apply-ism-policy.sh
```
New `wazuh-alerts-*` indices adopt `soc-lab-retention` (30d hot -> delete).

## Cold archive (immutable, hash-verified)
The `retention` service archives Wazuh alerts daily. One-shot demo run:
```
docker compose run --rm retention /archive.sh
```
Output layout:
```
retention/archive/2026/June/20260604T2100Z/
  logs.json.gz       # gzip of /var/ossec/logs/alerts/alerts.json
  manifest.sha256    # sha256 of logs.json.gz
  metadata.json      # export_date, source, events, compression, hash
```
Files are written read-only (0444). For real compliance use object storage with
**Object Lock / WORM** (e.g. S3 Object Lock) plus the manifest for integrity.

### Full raw archive (optional)
To archive ALL events (not just alerts), enable in the manager ossec.conf:
`<logall_json>yes</logall_json>` and point `SRC=/wazuh-logs/archives/archives.json`.

## Verify integrity
```
cd retention/archive/2026/June/<stamp>
sha256sum -c manifest.sha256
cat metadata.json
```

## Rehydration ("what happened 8 months ago")
1. Locate the archive by date folder; verify with `sha256sum -c manifest.sha256`.
2. `gunzip -k logs.json.gz`
3. Re-ingest for searching, e.g. bulk-load into a scratch Elasticsearch/OpenSearch:
   ```
   while read -r line; do
     curl -sk -u admin:$INDEXER_PASSWORD -H 'Content-Type: application/json' \
       -X POST https://127.0.0.1:9200/restored-alerts/_doc -d "$line" >/dev/null
   done < logs.json
   ```
   Then search the `restored-alerts` index in the dashboard.