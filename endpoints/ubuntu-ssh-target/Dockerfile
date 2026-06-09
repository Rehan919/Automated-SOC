FROM ubuntu:22.04
ARG WAZUH_VERSION=4.9.2
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
      openssh-server rsyslog curl ca-certificates iptables lsb-release && \
    curl -so /tmp/wazuh-agent.deb \
      https://packages.wazuh.com/4.x/apt/pool/main/w/wazuh-agent/wazuh-agent_${WAZUH_VERSION}-1_amd64.deb && \
    WAZUH_MANAGER="wazuh.manager" dpkg -i /tmp/wazuh-agent.deb && \
    rm -f /tmp/wazuh-agent.deb && \
    useradd -m -s /bin/bash devops && echo 'devops:devops' | chpasswd && \
    mkdir -p /var/run/sshd && \
    apt-get clean && rm -rf /var/lib/apt/lists/*
COPY ossec.conf /var/ossec/etc/ossec.conf
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
EXPOSE 22
ENTRYPOINT ["/entrypoint.sh"]
