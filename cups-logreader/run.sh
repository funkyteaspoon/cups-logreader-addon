#!/usr/bin/with-contenv bashio

INTERVAL=$(bashio::config 'poll_interval_seconds')

bashio::log.info "Starting CUPS log reader, polling every ${INTERVAL}s"

while true; do
  /track_pages.sh
  sleep "$INTERVAL"
done
