import json
import time
from threading import Thread
from typing import Callable

from tqdm import tqdm

from Man10SocketServer.data_class.Connection import Connection
from Man10SocketServer.data_class.ConnectionHandler import ConnectionHandler
from Man10SocketServer.socket_functions.both.ReplyFunction import ReplyFunction
from Man10SocketServer.socket_functions.client.CommandFunction import CommandFunction
from Man10SocketServer.socket_functions.client.SCommandFunction import SCommandFunction
from Man10SocketServer.socket_functions.client.SetNameFunction import SetNameFunction
from Man10SocketServer.socket_functions.client.SubscribeToEventHandlerFunction import SubscribeToEventHandlerFunction
from Man10SocketServer.socket_functions.server.EventHandlerFunction import EventHandlerFunction
from Man10SocketServer.socket_functions.server.RequestFunction import RequestFunction


class Man10SocketServer:

    def __init__(self):
        self.config = open("config/config.json", "r")
        self.config = json.load(self.config)

        def register_function(connection: Connection):
            connection.register_socket_function(CommandFunction(self))
            connection.register_socket_function(SCommandFunction(self))
            connection.register_socket_function(SetNameFunction(self))
            connection.register_socket_function(SubscribeToEventHandlerFunction(self))

            connection.register_socket_function(ReplyFunction(self))

            connection.register_socket_function(EventHandlerFunction(self))
            connection.register_socket_function(RequestFunction(self))

        self.connection_handler: ConnectionHandler = ConnectionHandler()
        self.connection_handler.register_function_on_connect = register_function
        self.connection_handler.open_socket_client("0.0.0.0", 5000)

        def check_open_socket_count_thread():
            while True:
                for server in self.config["servers"]:
                    open_sockets = [x for x in self.connection_handler.sockets.values() if x.name == server["name"]]
                    if len(open_sockets) < self.config["consecutiveSockets"]:
                        print("Opening socket", server["name"])
                        # open sockets until there are enough
                        for _ in range(self.config["consecutiveSockets"] - len(open_sockets)):
                            open_socket = self.connection_handler.socket_open_server(server["name"], server["host"],
                                                                                     server["port"])
                            if open_socket is None:
                                print("Failed to open socket", server["name"])
                time.sleep(1)

        self.check_open_socket_count_thread = Thread(target=check_open_socket_count_thread)
        self.check_open_socket_count_thread.daemon = True
        self.check_open_socket_count_thread.start()

        # self.servers: dict[str, Server] = {}
        # for server in self.config["servers"]:
        #     self.servers[server["name"]] = Server(self, server["name"], server["host"], server["port"])

        # self.client_handlers = ClientHandler(self)

        # start_time = time.time()
        # for x in tqdm(range(10000)):
        #     def callback(data):
        #         print(time.time() - start_time)
        #     res = self.connection_handler.get_server_socket_round_robin("main").send_message({
        #         "type": "sCommand",
        #         "command": "mshop moneyGive ffa9b4cb-ada1-4597-ad24-10e318f994c8 1",
        #     }, reply=True)
        #     # print(res)
        #
        #
        # print("done" + str(time.time() - start_time))

        time.sleep(100000)


