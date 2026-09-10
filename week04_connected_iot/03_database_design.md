# Database Design

## devices
- device_id
- name
- location
- status
- last_seen

## measurements
- id
- device_id
- timestamp
- metric
- value

## events
- event_id
- device_id
- timestamp
- event_type
- severity
- status

## commands
- command_id
- device_id
- timestamp
- command
- requested_state
- actual_state
