#!/usr/bin/with-contenv bashio

INTERVAL=$(bashio::config 'poll_interval_seconds')
export MQTT_HOST=$(bashio::config 'mqtt_host')
export MQTT_PORT=$(bashio::config 'mqtt_port')
export MQTT_USER=$(bashio::config 'mqtt_user')
export MQTT_PASS=$(bashio::config 'mqtt_password')
export QUEUES=$(bashio::config 'queues')

bashio::log.info "Starting CUPS log reader, polling every ${INTERVAL}s"

# Background: the test-publish web UI (ingress)
python3 /test_ui.py &

# Foreground: the actual polling loop
while true; do
  /track_pages.sh
  sleep "$INTERVAL"
done
