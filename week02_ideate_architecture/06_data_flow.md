# 6. Data Flow

## Telemetry / Measurement
`Sensor → Edge → Network → Backend → DB → Dashboard`

## Command
`User/App → Backend/Broker → Edge → Actuator`

## State
`Actuator/Device → Edge → Backend → Dashboard`

## Alert/Event
`Edge/Backend Rule → Alert → User`

## JSON mẫu
```json
{
  "device_id": "device01",
  "timestamp": "YYYY-MM-DDTHH:MM:SSZ",
  "type": "telemetry",
  "value": 0
}
```
