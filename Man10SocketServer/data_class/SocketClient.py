from __future__ import annotations

import json
from queue import Queue
from threading import Thread
from typing import TYPE_CHECKING, Callable
import socket

if TYPE_CHECKING:
    from Man10SocketServer import Man10SocketServer


class SocketClient:

    def __init__(self, socket: socket.socket):
        self.socket = socket
        self.message_queue = Queue()

        self.listening_event_types = []

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

    def send_message(self, message: dict):
        self.message_queue.put(message)

    def send_reply_message(self, status: str, message, reply_id: str):
        self.send_message({"type": "reply", "replyId": reply_id, "message": message, "status": status})

    def __send_message_internal(self, message: dict):
        message = json.dumps(message, ensure_ascii=False)
        message += "<E>"
        self.socket.sendall(message.encode('utf-8'))