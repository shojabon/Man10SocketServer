import json
import time

from tqdm import tqdm

from Man10SocketServer.data_class.ClientHandler import ClientHandler
from Man10SocketServer.data_class.Server import Server


class Man10SocketServer:

    def __init__(self):
        self.config = open("config/config.json", "r")
        self.config = json.load(self.config)

        self.servers: dict[str, Server] = {}
        for server in self.config["servers"]:
            self.servers[server["name"]] = Server(self, server["name"], server["host"], server["port"])

        self.client_handlers = ClientHandler(self)

        # start_time = time.time()
        # for x in tqdm(range(10000)):
        #     def callback(data):
        #         print(time.time() - start_time)
        #     res = self.servers["main"].execute_scommand("mshop moneyGive ffa9b4cb-ada1-4597-ad24-10e318f994c8 1", callback=callback)
        #     # print(res)


        # print("done" + str(time.time() - start_time))

        time.sleep(100000)


