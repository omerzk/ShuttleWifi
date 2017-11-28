import json
import subprocess
from time import sleep
from wifi import Cell, Scheme, exceptions
from pathlib import Path

INTERFACE = "wlan0"
SHUTTLE_SSID = "Soofa"
SHUTTLE_PASSWORDS = ["15383888", "15384888", "52347399", "31659399", "52354399", "52940399", "72983877", "74394344", "90136588", "90137588"]
JSONFILE = "./knowMacToPassword.json"
GOOGLE_DNS_SERVER_IP = "8.8.8.8"
SECONDS_TO_CONNECTION = 10
PING_AMOUNT = '1'

def getbestcell(ssid):
    ssidFilter = lambda cell: cell is not None and cell.ssid == ssid
    cells = Cell.where(INTERFACE, ssidFilter)

    if not cells:
        print("No", ssid, "network detected") #TODO: write to logfile
        return None

    return max(cells, key=lambda cell: cell.quality)


class ShuttleWiFiConnector:

    def __init__(self):
        if Path(JSONFILE).is_file():
            with open(JSONFILE, "r") as jsonfile:
                self.MACToPassword = json.load(jsonfile)
        else:
            self.MACToPassword = dict()

    def __exit__(self):
        with open(JSONFILE, "w") as jsonfile:
            json.dump(self.MACToPassword, jsonfile)

    """Get strongest signal cell of the requested SSID"""

    def try_connect(self, cell, password):
        schema = Scheme.for_cell(INTERFACE, SHUTTLE_SSID, cell, password)

        try:
            schema.activate()
        except Exception as e:
            print(e)

        sleep(SECONDS_TO_CONNECTION)

        ping = subprocess.Popen(["ping", GOOGLE_DNS_SERVER_IP, "-c", PING_AMOUNT], stdout=subprocess.PIPE)

        if ping.wait() == 0:
            self.MACToPassword[cell.address] = password
            return True
        
        return False


    def try_connect_shuttle(self):
        connected = False
        cell = getbestcell(SHUTTLE_SSID)

        if cell:
            i = 0
            if cell.address in self.MACToPassword:
                connected = self.try_connect(cell, self.MACToPassword[cell.address])

            while i < len(SHUTTLE_PASSWORDS) and not connected:
                connected = self.try_connect(cell, SHUTTLE_PASSWORDS[i])
                i += 1

        return connected
