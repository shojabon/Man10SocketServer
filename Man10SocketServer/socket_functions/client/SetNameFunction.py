from __future__ import annotations

import socket
from typing import TYPE_CHECKING, Callable

from Man10SocketServer.data_class.ConnectionFunction import ConnectionFunction

if TYPE_CHECKING:
    from Man10SocketServer.data_class.Connection import Connection
    from Man10SocketServer import Man10SocketServer


class SetNameFunction(ConnectionFunction):

    def information(self):
        self.name = "Set client name function"
        self.function_type = "set_name"
        self.mode = ["client"]

    def handle_message(self, connection: Connection, json_message: dict):
        if "name" not in json_message:
            return "invalid_args_name", None
        name = json_message["name"]
        connection.name = name
        if name not in self.main.connection_handler.same_name_sockets:
            self.main.connection_handler.same_name_sockets[name] = []
        self.main.connection_handler.same_name_sockets[name].append(connection.socket_id)
        return "success", None
