from stem.control import Controller
from stem import process, Signal
from random import randint
from os import getenv
import asyncio
import pproxy


def start_tor(socks: int, socks_port: int, control_port: int):

    control_ports = []
    socks_ports = []

    num_of_socks = range(socks)
    for i in num_of_socks:
        control_ports.append(f"{control_port + i}")
        socks_ports.append(f"{socks_port + i}")

    process.launch_tor_with_config(config={
        'ControlPort': control_ports,
        'SocksPort': socks_ports,
        'DNSPort': '53',
        'DNSListenAddress': '0.0.0.0'
    })


def reset_socks(socks: int, control_port: int):
    port = randint(control_port, control_port + socks)
    with Controller.from_port(port=port) as controller:
        controller.authenticate()
        controller.signal(Signal.NEWNYM)


def run_pproxy(socks: int, haproxy_port: int, socks_port: int):
    server = pproxy.Server(f'http://0.0.0.0:{haproxy_port}')

    num_of_socks = range(socks)
    remotes: list = []
    for i in num_of_socks:
        remotes.append(pproxy.Connection(f'socks5://localhost:{socks_port + i}'))

    args = dict(rserver=remotes,
                verbose=print, salgorithm="rr")

    loop = asyncio.get_event_loop()
    handler = loop.run_until_complete(server.start_server(args))
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        print('exit!')

    handler.close()
    loop.run_until_complete(handler.wait_closed())
    loop.run_until_complete(loop.shutdown_asyncgens())
    loop.close()


if __name__ == '__main__':

    number_of_socks: int = getenv("number_of_socks", 10)
    haproxy_port: int = getenv("haproxy_port", 5000)
    starting_socks_port: int = getenv("starting_socks_port", 6080)
    starting_control_port: int = getenv("starting_control_port", 7080)

    start_tor(
        socks=int(number_of_socks),
        socks_port=int(starting_socks_port),
        control_port=int(starting_control_port)
    )

    run_pproxy(
        socks=int(number_of_socks),
        haproxy_port=int(haproxy_port),
        socks_port=int(starting_socks_port)
    )
