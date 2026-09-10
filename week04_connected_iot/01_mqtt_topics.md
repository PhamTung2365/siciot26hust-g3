# MQTT Topic Plan

| Topic | Publisher | Subscriber | QoS | Payload |
|---|---|---|---:|---|
| `project/device01/telemetry` | Edge | Backend | 0/1 | JSON |
| `project/device01/state` | Edge | Backend | 0/1 | JSON |
| `project/device01/alert` | Edge | Backend | 1 | JSON |
| `project/device01/command` | Backend | Edge | 1 | JSON |

## Lưu ý
QoS 1 là **at least once delivery** và có thể có message trùng. Nên dùng `event_id`/`message_id` để deduplicate.
