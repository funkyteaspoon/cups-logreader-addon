FROM ghcr.io/home-assistant/base:latest

RUN apk add --no-cache mosquitto-clients bash python3

COPY run.sh /run.sh
COPY track_pages.sh /track_pages.sh
COPY test_ui.py /test_ui.py
RUN chmod a+x /run.sh /track_pages.sh

CMD [ "/run.sh" ]
