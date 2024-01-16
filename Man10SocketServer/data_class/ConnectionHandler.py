from __future__ import annotations

import json
import socket
import threading
import traceback
import uuid
from threading import Thread
from typing import TYPE_CHECKING, Callable

from Man10SocketServer.data_class.Connection import Connection

if TYPE_CHECKING:
    from Man10SocketServer import Man10SocketServer


class ConnectionHandler:

    def __init__(self):

        self.sockets: dict[str, Connection] = {}
        self.same_name_sockets: dict[str, list[str]] = {}
        self.get_counter = 0

        def empty(connection):
            pass

        self.register_function_on_connect: Callable[[Connection], None] = empty

    def socket_open_server(self, name, host, port) -> socket.socket | None:
        socket_id = str(uuid.uuid4())
        if name not in self.same_name_sockets:
            self.same_name_sockets[name] = []
        try:
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

            client_socket.connect((host, port))
            print("Socket opened", name)
            self.sockets[socket_id] = Connection(self, client_socket, socket_id=socket_id, mode="server", name=name)
            self.same_name_sockets[name].append(socket_id)
            return client_socket
        except Exception as e:
            print(e)
            return None

    def open_socket_client(self, host, port):
        def start_server():
            server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_socket.bind((host, port))
            server_socket.listen()

            print(f"Listening on {host}:{port}...")

            try:
                while True:
                    client_socket, addr = server_socket.accept()
                    socket_id = str(uuid.uuid4())
                    self.sockets[socket_id] = Connection(self, client_socket, socket_id, "client")
            finally:
                server_socket.close()

        self.server_thread = Thread(target=start_server)
        self.server_thread.daemon = True
        self.server_thread.start()

    def get_server_socket(self, socket_id) -> Connection:
        return self.sockets[socket_id]

    def get_socket(self, name: str) -> Connection | None:
        if name not in self.same_name_sockets:
            return None
        return self.sockets[self.same_name_sockets[name][0]]

