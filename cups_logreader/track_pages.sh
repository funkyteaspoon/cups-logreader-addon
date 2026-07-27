#!/usr/bin/with-contenv bashio

SLUG=$(bashio::config 'cups_addon_slug')
MQTT_HOST=$(bashio::config 'mqtt_host')
MQTT_PORT=$(bashio::config 'mqtt_port')
MQTT_USER=$(bashio::config 'mqtt_user')
MQTT_PASS=$(bashio::config 'mqtt_password')

LOG_PATH="/addon_configs/${SLUG}/cups/page_log"
STATE_FILE="/config/last_line_count"

if [ ! -f "$LOG_PATH" ]; then
  bashio::log.warning "page_log not found at ${LOG_PATH} yet, skipping this run"
  exit 0
fi

TOTAL_LINES=$(wc -l < "$LOG_PATH")
LAST_LINES=$(cat "$STATE_FILE" 2>/dev/null || echo 0)

if [ "$TOTAL_LINES" -le "$LAST_LINES" ]; then
  exit 0
fi

NEW_LINES=$(tail -n +"$((LAST_LINES + 1))" "$LOG_PATH")

echo "$NEW_LINES" | awk '
{
  queue = $1
  user = $2
  pagefield = $6
  copies = $7
  host = $8

  if (pagefield == "total") {
    pages_this_line = copies
  } else {
    pages_this_line = 1
  }

  total_pages[queue] += pages_this_line
  ts = $4 " " $5
  gsub(/\[|\]/, "", ts)
  last_ts[queue] = ts
  last_user[queue] = user
  last_host[queue] = host
}
END {
  for (q in total_pages) {
    print q "\t" total_pages[q] "\t" last_ts[q] "\t" last_user[q] "\t" last_host[q]
  }
}' | while IFS=$'\t' read -r queue pages ts user host; do
  # Escape backslashes and quotes so the values are valid inside JSON strings
  user_esc=$(printf '%s' "$user" | sed 's/\\/\\\\/g; s/"/\\"/g')
  host_esc=$(printf '%s' "$host" | sed 's/\\/\\\\/g; s/"/\\"/g')

  bashio::log.info "Publishing ${pages} pages for queue ${queue}"
  payload=$(printf '{"pages": %s, "last_printed": "%s", "last_user": "%s", "last_ip": "%s"}' \
    "$pages" "$ts" "$user_esc" "$host_esc")
  mosquitto_pub -h "$MQTT_HOST" -p "$MQTT_PORT" \
    ${MQTT_USER:+-u "$MQTT_USER"} ${MQTT_PASS:+-P "$MQTT_PASS"} \
    -t "cups/${queue}/status" -m "$payload"
done

echo "$TOTAL_LINES" > "$STATE_FILE"
