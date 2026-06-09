# Windows endpoint: Wazuh agent + Sysmon

The Windows host is the third endpoint (native install, not a container).

## 1. Install the Wazuh agent (run elevated)
Download the 4.9.2 agent MSI from https://packages.wazuh.com/4.x/windows/wazuh-agent-4.9.2-1.msi
then register against the manager published on localhost:
```
msiexec.exe /i wazuh-agent-4.9.2-1.msi /q ^
  WAZUH_MANAGER="127.0.0.1" ^
  WAZUH_REGISTRATION_SERVER="127.0.0.1" ^
  WAZUH_AGENT_NAME="windows-endpoint"
NET START WazuhSvc
```
(The Wazuh manager exposes 1514/1515 on 127.0.0.1 via Docker Desktop.)

## 2. Install Sysmon
```
powershell -ExecutionPolicy Bypass -File .\install-sysmon.ps1
```

## 3. Forward Sysmon events to Wazuh
Open `C:\Program Files (x86)\ossec-agent\ossec.conf` and add the `<localfile>`
block from `wazuh-agent-ossec-snippet.xml` inside `<ossec_config>`, then:
```
Restart-Service WazuhSvc
```

## 4. Verify
In the Wazuh dashboard the agent `windows-endpoint` should be **Active**, and
Sysmon process-creation events (Event ID 1) should appear in the alerts/events.