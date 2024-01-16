from __future__ import annotations

import json
import time
import typing
from threading import Thread
from typing import TYPE_CHECKING, Callable

from Man10SocketServer.MinecraftServerManager.data_class.Player import Player

if TYPE_CHECKING:
    from Man10SocketServer import Man10SocketServer


class MinecraftServerManager:

    def __init__(self, main: Man10SocketServer):
        self.main: Man10SocketServer = main
        self.players: dict[str, Player] = {}

        @self.main.event_handler.listener("player_join")
        def player_join(connection, json_message):
            data = json_message.get("data", {})
            player_data = data.get("player", {})
            player_uuid = player_data.get("uuid", None)
            if player_uuid is None:
                return
            if player_uuid not in self.players:
                self.players[player_uuid] = Player(self, player_data)

            self.get_player(player_uuid).set_server(connection.name)

        @self.main.event_handler.listener("player_quit")
        def player_quit(connection, json_message):
            data = json_message.get("data", {})
            player_data = data.get("player", {})
            player_uuid = player_data.get("uuid", None)
            if player_uuid is None:
                return
            if player_uuid not in self.players:
                self.players[player_uuid] = Player(self, player_data)

            self.get_player(player_uuid).set_server(None)

        # refresh player information every 10 seconds
        def task():
            while True:
                self.refresh_player_information()
                time.sleep(10)

        Thread(target=task, daemon=True).start()

    def get_player(self, player_uuid: str) -> Player:
        return self.players.get(player_uuid, None)

    def refresh_player_information(self):
        def callback_task(message: dict, information_of_server: str):
            data = json.loads(message.get("data", "[]"))
            for player in data:
                if player["uuid"] not in self.players:
                    self.players[player["uuid"]] = Player(self, player)
                self.get_player(player["uuid"]).set_server(information_of_server)

        for target in self.main.list_target_servers():
            self.main.connection_handler.get_socket(target).send_message({
                "type": "sCommand",
                "command": "man10socket playersInfo"
            }, callback=callback_task, reply_arguments=(target,))

    def execute_command(self, target: str, command: str, reply: bool = False, callback: Callable = None, reply_timeout: int = 1, reply_arguments: typing.Tuple = None):
        if target in self.players:
            target = self.get_player(target).get_server()

        target_socket = self.main.connection_handler.get_socket(target)
        if target_socket is None:
            raise Exception("target server not found")
        return target_socket.send_message({
            "type": "command",
            "command": command
        }, reply=reply, callback=callback, reply_timeout=reply_timeout, reply_arguments=reply_arguments)

    def execute_sCommand(self, target: str, command: str, reply: bool = False, callback: Callable = None, reply_timeout: int = 1, reply_arguments: typing.Tuple = None):
        if target in self.players:
            target = self.get_player(target).get_server()

        target_socket = self.main.connection_handler.get_socket(target)
        if target_socket is None:
            raise Exception("target server not found")
        return target_socket.send_message({
            "type": "sCommand",
            "command": command
        }, reply=reply, callback=callback, reply_timeout=reply_timeout, reply_arguments=reply_arguments)
