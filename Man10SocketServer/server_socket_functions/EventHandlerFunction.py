from __future__ import annotations

import socket
from typing import TYPE_CHECKING, Callable

from Man10SocketServer.data_class.ServerSocketFunction import ServerSocketFunction

if TYPE_CHECKING:
    from Man10SocketServer import Man10SocketServer


class EventHandlerFunction(ServerSocketFunction):
    name = "Event Handler Function"
    function_type = "event"

    def handle_message(self, json_message: dict, server: str):
        event_type = json_message.get("event")
        json_message["server"] = server
        for client in self.main.client_handlers.clients:
            if "*" in client.listening_event_types or event_type in client.listening_event_types:
                client.send_message(json_message)
