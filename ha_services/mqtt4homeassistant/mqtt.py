import logging
import socket

import paho.mqtt.client as mqtt
from bx_py_utils.anonymize import anonymize
from cli_base.cli_tools.rich_utils import human_error
from rich import print

from ha_services import __version__
from ha_services.mqtt4homeassistant.data_classes import MqttSettings


logger = logging.getLogger(__name__)


class OnConnectCallback:
    def __init__(self, verbosity: int):
        self.verbosity = verbosity

    def __call__(self, client, userdata, flags, reason_code, properties):
        if self.verbosity:
            print(f'MQTT broker connect {reason_code=}', end=' ')

        if reason_code == 0:
            if self.verbosity:
                print('[green]OK')
        else:
            print('\n[red]MQTT Connection not successful!')
            print('[yellow]Please check your credentials\n')
            raise RuntimeError(f'MQTT connection {reason_code=} is not 0')

        if self.verbosity:
            print(f'\t{userdata=}')
            print(f'\t{flags=}')


def get_connected_client(settings: MqttSettings, verbosity: int, timeout=10) -> mqtt.Client:
    client_id = settings.main_uid

    if verbosity:
        print(f'\nConnect [cyan]{settings.host}:{settings.port}[/cyan] as "[magenta]{client_id}[/magenta]"', end='...')

    socket.setdefaulttimeout(timeout)  # Sadly: Timeout will not used in getaddrinfo()!
    try:
        info = socket.getaddrinfo(settings.host, settings.port)
    except socket.gaierror as err:
        human_error(
            message=f'{err}\n(Hint: Check you host/port settings)',
            title=f'[red]Error get address info from: [cyan]{settings.host}:{settings.port}[/cyan]',
            exception=err,
            exit_code=1,
        )
    else:
        if not info:
            print('[red]Resolve error: No info!')
        elif verbosity:
            print('Host/port test [green]OK')

    mqttc = mqtt.Client(
        mqtt.CallbackAPIVersion.VERSION2,
        client_id=client_id,
    )
    mqttc.on_connect = OnConnectCallback(verbosity=verbosity)
    mqttc.enable_logger(logger=logger)

    if settings.user_name and settings.password:
        if verbosity:
            print(
                f'login with user: {anonymize(settings.user_name)} password:{anonymize(settings.password)}',
                end='...',
            )
        mqttc.username_pw_set(settings.user_name, settings.password)

    mqttc.connect(settings.host, port=settings.port)

    if verbosity:
        print('[green]OK')
    return mqttc
