from __future__ import annotations

import socket
from typing import TYPE_CHECKING, Callable

from Man10SocketServer.data_class.Connection import Connection
from Man10SocketServer.data_class.ConnectionFunction import ConnectionFunction
from Man10SocketServer.data_class.ServerSocketFunction import ServerSocketFunction

if TYPE_CHECKING:
    from Man10SocketServer import Man10SocketServer


class RequestFunction(ConnectionFunction):

    def information(self):
        self.name = "Custom Request Function"
        self.function_type = "request"
        self.mode = ["server"]

    def handle_message(self, connection: Connection, json_message: dict):
        if "target" not in json_message:
            return "invalid_args_target", None
        if "path" not in json_message:
            return "invalid_args_path", None
        if "data" not in json_message:
            return "invalid_args_data", None
        json_message["server"] = connection.name
        client_found = False

        for client in self.main.client_handlers.clients:
            if client.name == json_message["target"]:
                client_found = True
                def reply_callback(data: dict):
                    client.send_reply_message("success", data, json_message["replyId"])
                client.send_message(json_message, reply_callback)

        if not client_found:
            return "target_not_found", None
