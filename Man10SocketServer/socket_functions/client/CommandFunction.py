from __future__ import annotations

import socket
from typing import TYPE_CHECKING, Callable

from Man10SocketServer.data_class.ConnectionFunction import ConnectionFunction

if TYPE_CHECKING:
    from Man10SocketServer.data_class.Connection import Connection
    from Man10SocketServer import Man10SocketServer


class CommandFunction(ConnectionFunction):

    def information(self):
        self.name = "Command Function"
        self.function_type = "command"
        self.mode = ["client"]

    def handle_message(self, connection: Connection, json_message: dict):
        options = {}
        if "command" not in json_message:
            return "invalid_args_command", None
        if "server" not in json_message:
            return "invalid_args_server", None
        server = json_message["server"]
        if "replyId" in json_message:
            options["callback"] = lambda message: connection.send_reply_message(message["status"], message["message"],
                                                                                json_message["replyId"])
        server_socket = self.main.connection_handler.get_server_socket_round_robin(server)
        if server_socket is None:
            return "server_not_found", None
        server_socket.send_message({"type": "sCommand", "command": json_message["command"]}, **options)