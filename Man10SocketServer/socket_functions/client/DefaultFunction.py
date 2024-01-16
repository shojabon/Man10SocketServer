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

        # target to player server
        if target is not None and target in self.main.minecraft_server_manager.players:
            target = self.main.minecraft_server_manager.get_player(target).get_server()

        if reply_id is None:
            if target is None:
                return
            target_socket = self.main.connection_handler.get_socket(target)
            if target_socket is None:
                return
            target_socket.send_message(json_message)
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
                target_socket = self.main.connection_handler.get_socket(reply_target)
                if target_socket is None:
                    return
                target_socket.send_message(json_message)
                del self.reply_target[reply_id]
                return

            if reply_id in connection.reply_callback:
                connection.reply_callback.get(reply_id)(json_message, *connection.reply_arguments.get(reply_id))
                # Store the response
            if reply_id in connection.reply_lock:
                connection.reply_data[reply_id] = json_message
                # Trigger the event to unblock the waiting thread
                connection.reply_lock[reply_id].set()

