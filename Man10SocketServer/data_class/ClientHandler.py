from __future__ import annotations

import json
import socket
import threading
import time
import typing
import uuid
from queue import Queue
from threading import Thread
from typing import TYPE_CHECKING, Callable

from expiring_dict import ExpiringDict

from Man10SocketServer.data_class.Client import Client
from Man10SocketServer.data_class.SocketFunction import SocketFunction
if TYPE_CHECKING:
    from Man10SocketServer import Man10SocketServer


class ClientHandler:

    def __init__(self, main: Man10SocketServer):
        self.main: Man10SocketServer = main

        self.clients: list[Client] = []

        self.socket_functions: dict[str, SocketFunction] = {}
        self.__register_socket_function(CommandFunction(self.main))
        self.__register_socket_function(SCommandFunction(self.main))
        self.__register_socket_function(SubscribeToEventHandlerFunction(self.main))
        self.__register_socket_function(SetNameFunction(self.main))

        def start_server():
            port = self.main.config["listeningPort"]
            host = "0.0.0.0"
            server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_socket.bind((host, port))
            server_socket.listen()

            print(f"Listening on {host}:{port}...")

            try:
                while True:
                    client_socket, addr = server_socket.accept()
                    client_thread = threading.Thread(target=self.handle_client, args=(client_socket,))
                    client_thread.start()
            finally:
                server_socket.close()

        self.server_thread = Thread(target=start_server)
        self.server_thread.daemon = True
        self.server_thread.start()


    def __register_socket_function(self, function: SocketFunction):
        self.socket_functions[function.function_type] = function
        print(f"Registered socket function: {function.name} ({function.function_type})")

    def handle_client(self, client_socket: socket.socket):
        buffer = ""
        client_object = Client(client_socket)
        self.clients.append(client_object)
        while True:
            try:
                data = client_socket.recv(1024 * 10).decode('utf-8')
                if data:
                    buffer += data
                    # Split messages using a specific end tag "<E>"
                    while "<E>" in buffer:
                        message, buffer = buffer.split("<E>", 1)
                        try:
                            # Try to parse the message as JSON
                            json_message = json.loads(message)
                            self.handle_message(json_message, client_object)
                        except json.JSONDecodeError:
                            print("Failed to decode message as JSON")
            except ConnectionResetError:
                self.clients.remove(client_object)
                break

    def handle_message(self, message: dict, client_object: Client):
        message_type = message["type"]
        if message_type not in self.socket_functions:
            print(f"Unknown message :", message)
            return
        reply = self.socket_functions[message_type].handle_message(message, client_object)
        if reply is not None and len(reply) == 2 and "replyId" in message:
            client_object.send_reply_message(status=reply[0], message=reply[1], reply_id=message["replyId"])


