" generic fixtures "
from unittest.mock import AsyncMock, Mock
import asyncio
import pytest
from pytest_asyncio import fixture
import tomllib

import logging

logging.basicConfig(level=logging.DEBUG)

CONFIG_1 = tomllib.load(open("tests/sample_config.toml", "rb"))


class MockReader:
    "A StreamReader mock"

    def __init__(self):
        self.q = asyncio.Queue()

    async def readline(self, *a):
        return await self.q.get()

    read = readline


class MockWriter:
    "A StreamWriter mock"

    def __init__(self):
        self.write = Mock()
        self.drain = AsyncMock()
        self.close = Mock()
        self.wait_closed = AsyncMock()


orig_start_unix_server = asyncio.start_unix_server

hyprctl_mock = None
hyprevt_mock = None
pyprctrl_mock = None


misc_objects = {}


async def my_mocked_unix_server(reader, *a):
    misc_objects["control"] = reader
    mo = AsyncMock()
    mo.close = Mock()
    return mo


async def my_mocked_unix_connection(path):
    "Return a mocked reader & writer"
    if path.endswith(".socket.sock"):
        return hyprctl_mock
    elif path.endswith(".socket2.sock"):
        return hyprevt_mock
    else:
        raise ValueError()


@fixture
async def empty_config(monkeypatch):
    "Runs with no config"
    monkeypatch.setattr("tomllib.load", lambda x: {"pyprland": {"plugins": []}})
    yield


@fixture
async def sample1_config(monkeypatch):
    "Runs with no config"
    monkeypatch.setattr("tomllib.load", lambda x: CONFIG_1)
    yield


async def mocked_hyprctlJSON(command):
    if command == "monitors":
        return MONITORS
    raise NotImplemented()


@fixture
async def server_fixture(monkeypatch):
    "Handle server setup boilerplate"
    global hyprevt_mock, hyprctl_mock, pyprctrl_mock

    hyprctl_mock = (MockReader(), MockWriter())
    hyprevt_mock = (MockReader(), MockWriter())

    pyprctrl_mock = MockReader()

    monkeypatch.setenv("XDG_RUNTIME_DIR", "/tmp")
    monkeypatch.setenv("HYPRLAND_INSTANCE_SIGNATURE", "/tmp/will_not_be_used/")
    monkeypatch.setattr("pyprland.ipc.notify", AsyncMock())
    monkeypatch.setattr("pyprland.ipc.hyprctlJSON", mocked_hyprctlJSON)

    from pyprland.command import run_daemon
    from pyprland import ipc

    orig_open_unix_connection = asyncio.open_unix_connection
    asyncio.open_unix_connection = my_mocked_unix_connection
    asyncio.start_unix_server = my_mocked_unix_server

    ipc.init()

    # Use asyncio.gather to run the server logic concurrently with other async tasks
    server_task = asyncio.create_task(run_daemon())

    # Allow some time for the server to initialize
    await asyncio.sleep(0.5)  # Adjust the duration as needed

    yield  # The test runs at this point

    await pyprctrl_mock.q.put(b"exit\n")

    # Cleanup: Cancel the server task to stop the server
    server_task.cancel()

    # Wait for the server task to complete
    await server_task

    asyncio.open_unix_connection = orig_open_unix_connection
    asyncio.start_unix_server = orig_start_unix_server


MONITORS = [
    {
        "id": 1,
        "name": "DP-1",
        "description": "Microstep MAG342CQPV DB6H513700137 (DP-1)",
        "make": "Microstep",
        "model": "MAG342CQPV",
        "serial": "DB6H513700137",
        "width": 3440,
        "height": 1440,
        "refreshRate": 59.99900,
        "x": 0,
        "y": 1080,
        "activeWorkspace": {"id": 1, "name": "1"},
        "specialWorkspace": {"id": 0, "name": ""},
        "reserved": [0, 50, 0, 0],
        "scale": 1.00,
        "transform": 0,
        "focused": True,
        "dpmsStatus": True,
        "vrr": False,
        "activelyTearing": False,
    },
    {
        "id": 0,
        "name": "HDMI-A-1",
        "description": "BNQ BenQ PJ 0x01010101 (HDMI-A-1)",
        "make": "BNQ",
        "model": "BenQ PJ",
        "serial": "0x01010101",
        "width": 1920,
        "height": 1080,
        "refreshRate": 60.00000,
        "x": 0,
        "y": 0,
        "activeWorkspace": {"id": 4, "name": "4"},
        "specialWorkspace": {"id": 0, "name": ""},
        "reserved": [0, 50, 0, 0],
        "scale": 1.00,
        "transform": 0,
        "focused": False,
        "dpmsStatus": True,
        "vrr": False,
        "activelyTearing": False,
    },
]
