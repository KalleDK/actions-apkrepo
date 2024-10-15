FROM alpine:edge
RUN apk update
RUN apk add abuild sudo
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]