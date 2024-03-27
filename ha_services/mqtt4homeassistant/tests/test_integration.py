import json
from unittest import TestCase

import frozendict
from bx_py_utils.test_utils.snapshot import assert_snapshot

from ha_services.mqtt4homeassistant.components.sensor import Sensor
from ha_services.mqtt4homeassistant.data_classes import ComponentConfig, ComponentState
from ha_services.mqtt4homeassistant.device import MainMqttDevice, MqttDevice
from ha_services.mqtt4homeassistant.mocks import HostSystemMock
from ha_services.mqtt4homeassistant.mocks.mqtt_client_mock import MqttClientMock


class IntergrationTestCase(TestCase):

    def test_main_sub(self):
        with HostSystemMock(), self.assertLogs('ha_services', level='DEBUG'):
            main_device = MainMqttDevice(
                name='Main Device',
                uid='main_uid',
            )
            device = MqttDevice(
                main_device=main_device,
                name='Sub Device',
                uid='sub_uid',
            )
            test_sensor = Sensor(
                device=device,
                name='Test Sensor',
                uid='sensor_uid',
            )
            self.assertEqual(
                test_sensor.get_state(),
                ComponentState(
                    topic='homeassistant/sensor/main_uid-sub_uid/main_uid-sub_uid-sensor_uid/state',
                    payload=None,
                ),
            )
            test_sensor.set_state(123)
            self.assertEqual(
                test_sensor.get_state(),
                ComponentState(
                    topic='homeassistant/sensor/main_uid-sub_uid/main_uid-sub_uid-sensor_uid/state',
                    payload=123,
                ),
            )

            self.assertEqual(
                test_sensor.get_config(),
                ComponentConfig(
                    topic='homeassistant/sensor/main_uid-sub_uid/main_uid-sub_uid-sensor_uid/config',
                    payload={
                        'component': 'sensor',
                        'device': frozendict.frozendict(
                            {
                                'name': 'Sub Device',
                                'identifiers': 'main_uid-sub_uid',
                                'via_device': 'main_uid',
                            }
                        ),
                        'device_class': None,
                        'json_attributes_topic': (
                            'homeassistant/sensor/main_uid-sub_uid/main_uid-sub_uid-sensor_uid/attributes'
                        ),
                        'name': 'Test Sensor',
                        'state_class': None,
                        'state_topic': 'homeassistant/sensor/main_uid-sub_uid/main_uid-sub_uid-sensor_uid/state',
                        'unique_id': 'main_uid-sub_uid-sensor_uid',
                        'unit_of_measurement': None,
                    },
                ),
            )

            mqtt_client_mock = MqttClientMock()
            main_device.poll_and_publish(mqtt_client_mock)

        first_message = mqtt_client_mock.messages[0]
        self.assertEqual(first_message['topic'], 'homeassistant/sensor/main_uid/main_uid-hostname/config')
        self.assertEqual(
            json.loads(first_message['payload']),
            {
                'component': 'sensor',
                'device': {'identifiers': 'main_uid', 'name': 'Main Device'},
                'device_class': None,
                'json_attributes_topic': 'homeassistant/sensor/main_uid/main_uid-hostname/attributes',
                'name': 'Hostname',
                'origin': {
                    'name': 'ha-services-tests',
                    'support_url': 'https://pypi.org/project/ha_services/',
                    'sw_version': '1.2.3',
                },
                'state_class': None,
                'state_topic': 'homeassistant/sensor/main_uid/main_uid-hostname/state',
                'unique_id': 'main_uid-hostname',
                'unit_of_measurement': None,
            },
        )

        for message in mqtt_client_mock.messages:
            topic = message['topic']
            payload = message['payload']
            self.assertIsInstance(payload, (int, float, str), message)

            if topic.endswith('/state') and 'eth0' in topic:
                message['payload'] = '<mocked eth0 values>'

        assert_snapshot(got=mqtt_client_mock.messages)
