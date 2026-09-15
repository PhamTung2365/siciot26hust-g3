import json
import os
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from pi_server.mqtt_gateway import DoorGateway, FaceTrigger


class FakeClient:
    def subscribe(self, topics):
        self.subscribed = topics

    def publish(self, topic, payload, **kwargs):
        self.published = (topic, json.loads(payload), kwargs)
        return SimpleNamespace(rc=0)


class DoorGatewayTest(unittest.TestCase):
    def test_face_trigger_rearms_only_after_absence(self):
        trigger = FaceTrigger(rearm_seconds=2)
        self.assertTrue(trigger.should_open("Alice", now=0))
        self.assertFalse(trigger.should_open("Alice", now=1))
        self.assertFalse(trigger.should_open(None, now=2))
        self.assertFalse(trigger.should_open(None, now=4))
        self.assertTrue(trigger.should_open("Alice", now=5))

    @patch.dict(os.environ, {"MQTT_ENABLED": "true", "DOOR_COMMAND_COOLDOWN": "10"})
    def test_state_and_command_are_validated_and_throttled(self):
        client = FakeClient()
        gateway = DoorGateway(client)
        gateway._on_connect(client, None, None, 0, None)
        gateway._on_message(client, None, SimpleNamespace(
            topic=gateway.state_topic,
            payload=b'{"status":"closed","online":true}',
        ))
        self.assertEqual(gateway.snapshot()["status"], "closed")
        self.assertTrue(gateway.send("open", "alice", "web"))
        self.assertEqual(client.published[1]["action"], "open")
        self.assertFalse(gateway.send("open", "alice", "web"))
        self.assertTrue(gateway.send("lock", "alice", "web"))
        self.assertNotIn("open_seconds", client.published[1])


if __name__ == "__main__":
    unittest.main()
