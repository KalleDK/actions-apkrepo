FROM alpine:edge
RUN apk --no-cache add abuild sudo python3 py3-rich py3-pydantic
COPY entrypoint.sh /entrypoint.sh
COPY apk-indexer/apk-indexer.py /apk-indexer.py
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]