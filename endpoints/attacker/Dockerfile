FROM alpine:3.20
RUN apk add --no-cache hydra openssh-client
COPY passwords.txt /opt/passwords.txt
COPY attack.sh /opt/attack.sh
RUN chmod +x /opt/attack.sh
ENTRYPOINT ["/opt/attack.sh"]