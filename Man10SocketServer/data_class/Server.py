from __future__ import annotations

import json
import socket
import threading
import time
import traceback
import typing
import uuid
from queue import Queue
from threading import Thread
from typing import TYPE_CHECKING, Callable

from expiring_dict import ExpiringDict

from Man10SocketServer.data_class.ServerSocketFunction import ServerSocketFunction
from Man10SocketServer.data_class.SocketFunction import SocketFunction
from Man10SocketServer.server_socket_functions.EventHandlerFunction import EventHandlerFunction
from Man10SocketServer.server_socket_functions.RequestFunction import RequestFunction

if TYPE_CHECKING:
    from Man10SocketServer import Man10SocketServer


class Server:

    def __init__(self, main: Man10SocketServer, name: str, host: str, port: int):
        self.main: Man10SocketServer = main
        self.name = name
        self.host = host
        self.port = port

        self.reply_data = ExpiringDict(5)
        self.reply_lock = ExpiringDict(5)
        self.reply_callback = ExpiringDict(5)
        self.reply_arguments = ExpiringDict(5)

        self.socket_functions: dict[str, ServerSocketFunction] = {}
        self.__register_socket_function(EventHandlerFunction(self.main))
        self.__register_socket_function(RequestFunction(self.main))

        self.message_queue = Queue()

        self.message_round_robin = 0

        self.sockets: list[socket.socket] = []

        for x in range(main.config["consecutiveSockets"]):
            open_socket = self.socket_open()
            if open_socket is None:
                continue
            self.sockets.append(open_socket)

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

        self.check_open_socket_count_thread = Thread(target=self.check_open_socket_count_thread)
        self.check_open_socket_count_thread.daemon = True
        self.check_open_socket_count_thread.start()

    def __register_socket_function(self, function: ServerSocketFunction):
        self.socket_functions[function.function_type] = function
        print(f"Registered server socket function: {function.name} ({function.function_type})")

    def check_open_socket_count_thread(self):
        while True:
            if len(self.sockets) < self.main.config["consecutiveSockets"]:
                self.sockets.append(self.socket_open())
            time.sleep(1)

    def socket_open(self) -> socket.socket | None:
        try:
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

            client_socket.connect((self.host, self.port))
            thread = Thread(target=self.receive_messages, args=(client_socket,))
            thread.daemon = True
            thread.start()
            print("Socket opened", self.name)
            return client_socket
        except Exception as e:
            return None

    def receive_messages(self, sock: socket.socket):
        buffer = ""
        while True:
            try:
                data = sock.recv(1024 * 10).decode('utf-8')
                if data:
                    buffer += data
                    while "<E>" in buffer:
                        message, buffer = buffer.split("<E>", 1)
                        try:
                            json_message = json.loads(message)
                            message_type = json_message.get("type")
                            if message_type == "reply":
                                response_id = json_message.get("replyId") if "replyId" in json_message else None
                                if response_id is None:
                                    continue
                                if response_id in self.reply_callback:
                                    self.reply_callback.get(response_id)(json_message, *self.reply_arguments.get(response_id))
                                    # Store the response
                                if response_id in self.reply_lock:
                                    self.reply_data[response_id] = json_message
                                    # Trigger the event to unblock the waiting thread
                                    self.reply_lock[response_id].set()
                            else:
                                if message_type in self.socket_functions:
                                    self.socket_functions[message_type].handle_message(json_message, self.name)
                                else:
                                    print("Unknown message:", json_message)
                        except Exception as e:
                            print("Error parsing message:", e)
                            traceback.print_exc()
                else:
                    break
            except Exception as e:
                print("Error receiving data:", e)
                break
        self.socket_close(sock)

    def socket_close(self, sock: socket.socket):
        try:
            sock.close()
            self.sockets.remove(sock)
            print("Socket closed", self.name)
        except Exception as e:
            print("Error closing socket:", e)

    # =========

    def __send_message_internal(self, message: dict):
        message_string = json.dumps(message, ensure_ascii=False) + "<E>"
        if self.message_round_robin >= len(self.sockets):
            self.message_round_robin = 0
        self.sockets[self.message_round_robin].sendall(message_string.encode('utf-8'))
        self.message_round_robin += 1

    def send_message(self, message: dict, reply: bool = False, callback: Callable = None, reply_timeout: int = 1, reply_arguments: typing.Tuple = None) -> str | None:
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


    # =========

    def execute_command(self, command: str, reply: bool = False, callback: Callable = None, reply_arguments: typing.Tuple = None) -> str | None:
        return self.send_message(
            {
                "type": "command",
                "command": command
            },
            reply=reply,
            callback=callback,
            reply_arguments=reply_arguments
        )

    def execute_scommand(self, command: str, reply: bool = False, callback: Callable = None, reply_arguments: typing.Tuple = None) -> str | None:
        return self.send_message(
            {
                "type": "sCommand",
                "command": command
            },
            reply=reply,
            callback=callback,
            reply_arguments=reply_arguments
        )
