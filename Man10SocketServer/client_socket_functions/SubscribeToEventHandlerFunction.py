from __future__ import annotations

import socket
from typing import TYPE_CHECKING, Callable

from Man10SocketServer.data_class.SocketClient import SocketClient
from Man10SocketServer.data_class.SocketFunction import SocketFunction

if TYPE_CHECKING:
    from Man10SocketServer import Man10SocketServer

class SubscribeToEventHandlerFunction(SocketFunction):
    name = "Subscribe to event handler Function"
    function_type = "subscribe"
    def handle_message(self, json_message: dict, client_socket: SocketClient):
        if "event_type" not in json_message:
            return "invalid_args_event_type", None
        event_type = json_message["event_type"]
        if event_type not in client_socket.listening_event_types:
            client_socket.listening_event_types.append(event_type)