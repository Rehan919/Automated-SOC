FROM alpine:3.20
RUN apk add --no-cache bash coreutils gzip
COPY archive.sh /archive.sh
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /archive.sh /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]