from __future__ import annotations

import socket
from typing import TYPE_CHECKING, Callable

from Man10SocketServer.data_class.SocketClient import SocketClient
from Man10SocketServer.data_class.SocketFunction import SocketFunction

if TYPE_CHECKING:
    from Man10SocketServer import Man10SocketServer

class SCommandFunction(SocketFunction):
    name = "SCommand Function"
    function_type = "sCommand"
    def handle_message(self, json_message: dict, client_socket: SocketClient):
        options = {}
        if "command" not in json_message:
            return "invalid_args_command", None
        if "server" not in json_message:
            return "invalid_args_server", None
        server = json_message["server"]
        if server not in self.main.servers:
            return "invalid_server", None
        if "replyId" in json_message:
            options["callback"] = lambda message: client_socket.send_reply_message(message["status"], message["message"], json_message["replyId"])
        self.main.servers[server].execute_scommand(json_message["command"], **options)