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
if TYPE_CHECKING:
    from Man10SocketServer import MinecraftServerManager


class Player:

    def __init__(self, main: MinecraftServerManager, player_data: dict):
        self.main = main
        self.__player_data = player_data

    def set_server(self, server_name: str | None):
        self.__player_data["server"] = server_name

    def get_server(self):
        return self.__player_data.get("server", None)

    def get_uuid(self):
        return self.__player_data["uuid"]

    def get_name(self):
        return self.__player_data["name"]

    def is_online(self):
        return self.get_server() is not None

    def get_player_json(self):
        return self.__player_data
