#!/usr/bin/env bash
set -e
echo "[retention] daily cold-archive loop started"
while true; do
  /archive.sh || echo "[retention] archive run failed"
  sleep 86400
done