from __future__ import annotations

import socket
from typing import TYPE_CHECKING, Callable

from Man10SocketServer.data_class.ConnectionFunction import ConnectionFunction

if TYPE_CHECKING:
    from Man10SocketServer.data_class.Connection import Connection
    from Man10SocketServer import Man10SocketServer


class ReplyFunction(ConnectionFunction):
    def information(self):
        self.name = "reply function"
        self.function_type = "reply"
        self.mode = ["*"]

    def handle_message(self, connection: Connection, json_message: dict):
        response_id = json_message.get("replyId") if "replyId" in json_message else None
        if response_id is None:
            return
        if response_id in connection.reply_callback:
            connection.reply_callback.get(response_id)(json_message, *connection.reply_arguments.get(response_id))
            # Store the response
        if response_id in connection.reply_lock:
            connection.reply_data[response_id] = json_message
            # Trigger the event to unblock the waiting thread
            connection.reply_lock[response_id].set()
