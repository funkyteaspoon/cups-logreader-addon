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

echo "$NEW_LINES" | awk '{print $1}' | sort | uniq -c | while read -r count queue; do
  bashio::log.info "Publishing ${count} pages for queue ${queue}"
  mosquitto_pub -h "$MQTT_HOST" -p "$MQTT_PORT" \
    ${MQTT_USER:+-u "$MQTT_USER"} ${MQTT_PASS:+-P "$MQTT_PASS"} \
    -t "cups/${queue}/pages_added" -m "$count"
done

echo "$TOTAL_LINES" > "$STATE_FILE"
