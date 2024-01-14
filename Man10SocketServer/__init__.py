import json
import time

from Man10SocketServer.data_class.Server import Server


class Man10SocketServer:

    def __init__(self):
        self.config = open("config/config.json", "r")
        self.config = json.load(self.config)

        self.servers: dict[str, Server] = {}
        for server in self.config["servers"]:
            self.servers[server["name"]] = Server(self, server["name"], server["host"], server["port"])

        start_time = time.time()
        for x in range(10000):
            res = self.servers["main"].execute_scommand("mshop moneyGive ffa9b4cb-ada1-4597-ad24-10e318f994c8 1")
            # print(res)


        print("done" + str(time.time() - start_time))

        time.sleep(100000)


