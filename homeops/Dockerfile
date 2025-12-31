ARG BUILD_FROM
FROM $BUILD_FROM

# Install Python 3 (used for the tiny web server)
RUN \
  apk add --no-cache \
    python3

WORKDIR /app

# Copy add-on runtime
COPY run.sh /run.sh
COPY server.py /app/server.py

RUN chmod a+x /run.sh

CMD [ "/run.sh" ]
