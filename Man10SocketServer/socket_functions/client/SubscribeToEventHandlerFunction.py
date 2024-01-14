from __future__ import annotations

import socket
from typing import TYPE_CHECKING, Callable

from Man10SocketServer.data_class.Client import Client
from Man10SocketServer.data_class.ConnectionFunction import ConnectionFunction
from Man10SocketServer.data_class.SocketFunction import SocketFunction

if TYPE_CHECKING:
    from Man10SocketServer.data_class.Connection import Connection
    from Man10SocketServer import Man10SocketServer


class SubscribeToEventHandlerFunction(ConnectionFunction):

    def information(self):
        self.name = "Subscribe to event handler Function"
        self.function_type = "subscribe"
        self.mode = ["client"]

    def handle_message(self, connection: Connection, json_message: dict):
        if "event_type" not in json_message:
            return "invalid_args_event_type", None
        event_type = json_message["event_type"]
        if event_type not in connection.listening_event_types:
            connection.listening_event_types.append(event_type)
