from __future__ import annotations

import socket
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from Man10SocketServer.data_class.Connection import Connection
    from Man10SocketServer import Man10SocketServer


class ConnectionFunction:

    def information(self):
        pass

    def __init__(self, main: Man10SocketServer):
        self.main: Man10SocketServer = main
        self.name: str = ""
        self.function_type: str = ""
        self.mode: list[str] = []
        self.information()

    def handle_message(self, connection: Connection, json_message: dict):
        pass
