FROM alpine:edge
RUN apk update
RUN apk add alpine-sdk sudo
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENTRYPOINT /entrypoint.sh