#!/bin/bash
# Keep HF Space alive by pinging /health every 47 hours
# Add to crontab: 0 */23 * * * /home/Aa/ugc/scripts/keepalive.sh

HF_URL="https://badjals-kopilampung.hf.space/health"
LOG="/home/Aa/ugc/data/keepalive.log"

RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "$HF_URL" 2>/dev/null)
echo "$(date -Iseconds) ping: HTTP $RESPONSE" >> "$LOG"

# Keep log small (last 100 lines)
tail -100 "$LOG" > "$LOG.tmp" && mv "$LOG.tmp" "$LOG"
