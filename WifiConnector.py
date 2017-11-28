import json
import subprocess
from time import sleep
from wifi import Cell, Scheme
from pathlib import Path
import logging

# Paths
LOGPATH = "/var/log/wifiConnector.log"
JSON_PATH = "./knowMacToPassword.json"

# Wifi config values
INTERFACE = "wlan0"
SHUTTLE_SSID = "Soofa"
SHUTTLE_PASSWORDS = ["15383888", "15384888", "52347399", "31659399", "52354399", "52940399", "72983877", "74394344",
                     "90136588", "90137588"]

# Connection test Ping config
GOOGLE_DNS_SERVER_IP = "8.8.8.8"
SECONDS_TO_CONNECTION = 10
PING_AMOUNT = '1'


def init_shuttle_logger(logpath):
    logging.basicConfig(filename=logpath, filemode='a', level=logging.DEBUG, format='%(asctime)s %(message)s - ')
    logger = logging.getLogger(__name__)
    return logger


"""Get strongest signal cell of the requested SSID"""


def get_best_cell(ssid, logger):
    cells = Cell.where(INTERFACE, lambda cell: cell is not None and cell.ssid == ssid)
    logger.info("Number of " + ssid + "Networks detected: " + str(len(cells)))

    if not cells:
        logger.error("No " + ssid + "network detected")
        return None

    return max(cells, key=lambda cell: cell.quality)


class ShuttleWiFiConnector:
    def __enter__(self):
        if Path(JSON_PATH).is_file():
            with open(JSON_PATH, "r") as jsonfile:
                self.MACToPassword = json.load(jsonfile)
        else:
            self.MACToPassword = dict()

        self.logger = init_shuttle_logger(LOGPATH)

    def __exit__(self):
        with open(JSON_PATH, "w") as jsonfile:
            json.dump(self.MACToPassword, jsonfile)

    def try_connect(self, cell, password):
        schema = Scheme.for_cell(INTERFACE, SHUTTLE_SSID, cell, password)

        self.logger.info("Restarting interface with networks params")
        schema.activate()
        self.logger.info("Finished Restarting interface with networks params")

        sleep(SECONDS_TO_CONNECTION)

        ping = subprocess.Popen(["ping", GOOGLE_DNS_SERVER_IP, "-c", PING_AMOUNT], stdout=subprocess.PIPE)

        if ping.wait() == 0:
            self.MACToPassword[cell.address] = password
            self.logger("Ping success, connected to network")
            return True
        self.logger("Ping failed, failed to connect. Ping output" + ping.stdout.read())
        return False

    def try_connect_shuttle(self):
        connected = False
        cell = get_best_cell(SHUTTLE_SSID, self.logger)
        if cell:
            i = 0
            # Try to connect from memorized mac
            if cell.address in self.MACToPassword:
                connected = self.try_connect(cell, self.MACToPassword[cell.address])

            # If not connected try to connect using configured passwords
            while i < len(SHUTTLE_PASSWORDS) and not connected:
                connected = self.try_connect(cell, SHUTTLE_PASSWORDS[i])
                i += 1

        return connected
