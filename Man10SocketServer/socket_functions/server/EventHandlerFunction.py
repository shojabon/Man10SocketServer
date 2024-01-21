from __future__ import annotations

import socket
import traceback
from typing import TYPE_CHECKING, Callable

from Man10SocketServer.data_class.ConnectionFunction import ConnectionFunction

if TYPE_CHECKING:
    from Man10SocketServer.data_class.Connection import Connection
    from Man10SocketServer import Man10SocketServer


class EventHandlerFunction(ConnectionFunction):
    listeners: dict[str, list[Callable[[Connection, dict], None]]] = {}

    def information(self):
        self.name = "Event Handler Function"
        self.function_type = "event"
        self.mode = ["server"]

    def handle_message(self, connection: Connection, json_message: dict):
        event_type = json_message.get("event")
        json_message["server"] = connection.name

        data = json_message.get("data", {})
        if "player" in data:
            if data["player"] not in self.main.minecraft_server_manager.players:
                return
            if isinstance(data["player"], str):
                data["player"] = self.main.minecraft_server_manager.get_player(data["player"]).get_player_json()

        if event_type in self.listeners:
            for listener in self.listeners[event_type]:
                try:
                    listener(connection, json_message)
                except Exception as e:
                    traceback.print_exc()

        for client in self.main.connection_handler.sockets.values():
            if "*" in client.listening_event_types or event_type in client.listening_event_types:
                client.send_message(json_message)
                # print("send event to", client.name, json_message)

    def listener(self, event_type: str):
        def decorator(func: Callable[[Connection, dict], None]):
            if event_type not in self.listeners:
                self.listeners[event_type] = []
            self.listeners[event_type].append(func)
            return func

        return decorator
