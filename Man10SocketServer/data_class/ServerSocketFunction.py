from __future__ import annotations

import socket
from typing import TYPE_CHECKING, Callable

from Man10SocketServer.data_class.SocketClient import SocketClient

if TYPE_CHECKING:
    from Man10SocketServer import Man10SocketServer

class ServerSocketFunction:

    name: str = None
    function_type: str = None

    def __init__(self, main: Man10SocketServer):
        self.main: Man10SocketServer = main

    def handle_message(self, json_message: dict, server: str):
        pass
