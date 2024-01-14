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

        self.functions: list[ConnectionFunction] = []
        self.__register_socket_function(CommandFunction(self.main.main))
        self.__register_socket_function(SCommandFunction(self.main.main))
        self.__register_socket_function(SetNameFunction(self.main.main))
        self.__register_socket_function(SubscribeToEventHandlerFunction(self.main.main))

        self.__register_socket_function(ReplyFunction(self.main.main))

        self.__register_socket_function(EventHandlerFunction(self.main.main))

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

    def __register_socket_function(self, socket_function: ConnectionFunction):
        self.functions.append(socket_function)

    def __send_message_internal(self, message: dict):
        message_string = json.dumps(message, ensure_ascii=False) + "<E>"
        self.socket_object.sendall(message_string.encode('utf-8'))

    def send_message(self, message: dict, reply: bool = False, callback: Callable = None, reply_timeout: int = 1,
                     reply_arguments: typing.Tuple = None) -> str | None:
        if reply or callback is not None:
            reply = True
            reply_id = str(uuid.uuid4())

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
                            print("Received message:", json_message)
                            self.handle_message(json_message)
                        except Exception as e:
                            print("Error parsing message:", e)
                            traceback.print_exc()
                else:
                    break
            except Exception as e:
                print("Error receiving data:", e)
                break

    def handle_message(self, message: dict):
        for function in self.functions:
            if function.function_type == message["type"] and (self.mode in function.mode or "*" in function.mode):
                function.handle_message(self, message)
                return
