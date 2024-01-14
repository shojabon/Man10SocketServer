from __future__ import annotations

import socket
from typing import TYPE_CHECKING, Callable

from Man10SocketServer.data_class.ConnectionFunction import ConnectionFunction
from Man10SocketServer.data_class.ServerSocketFunction import ServerSocketFunction

if TYPE_CHECKING:
    from Man10SocketServer.data_class.Connection import Connection
    from Man10SocketServer import Man10SocketServer


class EventHandlerFunction(ConnectionFunction):

    def information(self):
        self.name = "Event Handler Function"
        self.function_type = "event"
        self.mode = ["server"]

    def handle_message(self, connection: Connection, json_message: dict):
        event_type = json_message.get("event")
        json_message["server"] = connection.name
        for client in self.main.client_handlers.clients:
            if "*" in client.listening_event_types or event_type in client.listening_event_types:
                client.send_message(json_message)
