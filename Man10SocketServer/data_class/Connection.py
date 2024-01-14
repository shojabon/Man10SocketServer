from __future__ import annotations

import json
import socket
import threading
import traceback
import typing
import uuid
from queue import Queue
from threading import Thread
from typing import TYPE_CHECKING, Callable

from expiring_dict import ExpiringDict

from Man10SocketServer.data_class.ConnectionFunction import ConnectionFunction
from Man10SocketServer.socket_functions.both.ReplyFunction import ReplyFunction
from Man10SocketServer.socket_functions.client.CommandFunction import CommandFunction
from Man10SocketServer.socket_functions.client.SCommandFunction import SCommandFunction
from Man10SocketServer.socket_functions.client.SetNameFunction import SetNameFunction
from Man10SocketServer.socket_functions.client.SubscribeToEventHandlerFunction import SubscribeToEventHandlerFunction
from Man10SocketServer.socket_functions.server.EventHandlerFunction import EventHandlerFunction
from Man10SocketServer.socket_functions.server.RequestFunction import RequestFunction

if TYPE_CHECKING:
    from Man10SocketServer.data_class.ConnectionHandler import ConnectionHandler
    from Man10SocketServer import Man10SocketServer


class Connection:

    def __init__(self, main: ConnectionHandler, socket_object: socket.socket, socket_id: str, mode: str = "server", name: str = None):
        self.main = main
        self.socket_object = socket_object
        self.socket_id = socket_id
        self.mode = mode

        self.name = name
        self.listening_event_types: list[str] = []

        self.reply_data = ExpiringDict(5)
        self.reply_lock = ExpiringDict(5)
        self.reply_callback = ExpiringDict(5)
        self.reply_arguments = ExpiringDict(5)

        self.message_queue = Queue()

        self.functions: dict[str, ConnectionFunction] = {}
        self.main.register_function_on_connect(self)

        def send_message_thread():
            while True:
                try:
                    message = self.message_queue.get()
                    self.__send_message_internal(message)
                    self.message_queue.task_done()
                except Exception as e:
                    print(e)

        self.send_message_thread = Thread(target=send_message_thread)
        self.send_message_thread.daemon = True
        self.send_message_thread.start()

        thread = Thread(target=self.receive_messages)
        thread.daemon = True
        thread.start()

    def register_socket_function(self, socket_function: ConnectionFunction):
        self.functions[socket_function.function_type] = socket_function

    def __send_message_internal(self, message: dict):
        message_string = json.dumps(message, ensure_ascii=False) + "<E>"
        self.socket_object.sendall(message_string.encode('utf-8'))

    def send_message(self, message: dict, reply: bool = False, callback: Callable = None, reply_timeout: int = 1,
                     reply_arguments: typing.Tuple = None) -> str | None:
        if reply or callback is not None:
            reply = True
            reply_id = str(uuid.uuid4())[:8]

            if reply_id:
                message["replyId"] = reply_id
                if callback is not None:
                    self.reply_callback[reply_id] = callback
                    self.reply_arguments[reply_id] = () if reply_arguments is None else reply_arguments
                else:
                    response_event = threading.Event()
                    self.reply_lock[reply_id] = response_event

        self.message_queue.put(message)

        if reply and callback is None:
            # Wait for the event to be set or timeout after 1 second
            event_triggered = response_event.wait(reply_timeout)
            reply = None
            if event_triggered:
                # Event was set, response received
                reply = self.reply_data.get(reply_id, None)

            # Clean up the reply data
            self.clean_reply_data(reply_id)
            return reply

    def clean_reply_data(self, reply_id: str):
        if reply_id in self.reply_data: del self.reply_data[reply_id]
        if reply_id in self.reply_lock: del self.reply_lock[reply_id]
        if reply_id in self.reply_callback: del self.reply_callback[reply_id]
        if reply_id in self.reply_arguments: del self.reply_arguments[reply_id]

    def send_reply_message(self, status: str, message, reply_id: str):
        self.send_message({"type": "reply", "replyId": reply_id, "message": message, "status": status})

    def receive_messages(self):
        buffer = ""
        while True:
            try:
                data = self.socket_object.recv(1024 * 10).decode('utf-8')
                if data:
                    buffer += data
                    while "<E>" in buffer:
                        message, buffer = buffer.split("<E>", 1)
                        try:
                            json_message = json.loads(message)
                            print("accepted message", json_message)
                            self.handle_message(json_message)
                        except Exception as e:
                            print("Error parsing message:", e)
                            traceback.print_exc()
                else:
                    break
            except Exception as e:
                print("Error receiving data:", e)
                break
        self.socket_close()

    def socket_close(self):
        try:
            self.socket_object.close()
            if self.socket_id in self.main.sockets:
                del self.main.sockets[self.socket_id]

            for name in self.main.same_name_sockets:
                if self.socket_id in self.main.same_name_sockets[name]:
                    self.main.same_name_sockets[name].remove(self.socket_id)
                    if len(self.main.same_name_sockets[name]) == 0:
                        del self.main.same_name_sockets[name]



            print("Socket closed", self.name)
        except Exception as e:
            print("Error closing socket:", e)

    def handle_message(self, message: dict):
        message_type = message["type"]
        function = self.functions.get(message_type, None)
        if function is None:
            return
        reply = function.handle_message(self, message)
        if reply is not None and len(reply) == 2 and "replyId" in message:
            self.send_reply_message(status=reply[0], message=reply[1], reply_id=message["replyId"])
