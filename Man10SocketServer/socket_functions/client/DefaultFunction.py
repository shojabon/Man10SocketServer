from __future__ import annotations

import socket
from typing import TYPE_CHECKING, Callable

from expiring_dict import ExpiringDict

from Man10SocketServer.data_class.ConnectionFunction import ConnectionFunction

if TYPE_CHECKING:
    from Man10SocketServer.data_class.Connection import Connection
    from Man10SocketServer import Man10SocketServer


class DefaultFunction(ConnectionFunction):

    def __init__(self, main: Man10SocketServer):
        super().__init__(main)

        self.reply_target = ExpiringDict(5)

    def information(self):
        self.name = "DefaultFunction Function"
        self.function_type = "default"
        self.mode = ["*"]

    def handle_message(self, connection: Connection, json_message: dict):
        message_type = json_message.get("type")
        target = json_message.get("target")
        reply_id = json_message.get("replyId")
        if reply_id is None:
            if target is None:
                return
            self.main.connection_handler.get_socket(target).send_message(json_message)
            return
        # delete target tag
        if target is not None:
            del json_message["target"]

        if message_type != "reply":

            self.reply_target[reply_id] = connection.name
            target_socket = self.main.connection_handler.get_socket(target)
            if target_socket is None:
                return "error_invalid_args_target", None
            target_socket.send_message(json_message)
            return

        if message_type == "reply":
            reply_target = self.reply_target.get(reply_id)
            if reply_target is not None:
                self.main.connection_handler.get_socket(reply_target).send_message(json_message)
                del self.reply_target[reply_id]
                return

