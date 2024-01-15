from __future__ import annotations

import socket
from typing import TYPE_CHECKING, Callable

from Man10SocketServer.data_class.ConnectionFunction import ConnectionFunction

if TYPE_CHECKING:
    from Man10SocketServer.data_class.Connection import Connection
    from Man10SocketServer import Man10SocketServer


class RequestFunction(ConnectionFunction):

    def information(self):
        self.name = "Custom Request Function"
        self.function_type = "request"
        self.mode = ["server"]

    def handle_message(self, connection: Connection, json_message: dict):
        if "target" not in json_message:
            return "error_invalid_args_target", None
        if "path" not in json_message:
            return "error_invalid_args_path", None
        if "data" not in json_message:
            return "error_invalid_args_data", None
        json_message["server"] = connection.name

        target_client = self.main.connection_handler.get_socket(json_message["target"])
        if target_client is None:
            return "error_target_not_found", None

        def reply_callback(data: dict, reply_id: str):
            connection.send_reply_message("success", data["message"], reply_id)

        if "replyId" in json_message:
            target_client.send_message(json_message, callback=reply_callback,
                                       reply_arguments=(json_message["replyId"],))
        else:
            target_client.send_message(json_message)
