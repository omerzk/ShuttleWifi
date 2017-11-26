import json
from wifi import Cell, Scheme, exceptions

SHUTTLE_PASSWORDS = ["15383888", "15384888", "52347399", "31659399", "52354399", "52940399", "72983877", "74394344",
                     "90136588", "90137588"]

INTERFACE = "wlan0"
SUTTLE_SSID = "Soofa"
JSONFILE = "./knowMacToPassword.json"


class ShuttleWiFiConnector:

    def __init__(self):
        with open(JSONFILE, "r") as jsonfile:
            self.MACToPassword = json.load(jsonfile)

    def __del__(self):
        with open(JSONFILE, "w") as jsonfile:
            json.dump(self.MACToPassword, jsonfile)

    """Get strongest signal cell of the requested SSID"""
    def getBestCell(self, ssid):
        ssidFilter = lambda cell: cell is not None and cell.ssid == ssid
        cells = Cell.where(INTERFACE, ssidFilter)

        if not cells:
            print("No", ssid, "network detected") #TODO: write to logfile
            return None

        return max(cells, key=lambda cell: cell.quality)

    def tryConnect(self, cell, password):
        schema = Scheme.for_cell(INTERFACE, SUTTLE_SSID, cell, password)
        try:
            schema.activate()
        except exceptions.ConnectionError:
            return False

        self.MACToPassword[cell.address] = password

        return True

    def TryConnectShuttle(self):
        cell = self.getBestCell(SUTTLE_SSID)

        i = 0
        connected = False

        if cell.address in self.MACToPassword:
            connected = self.tryConnect(cell, self.MACToPassword[cell.address])

        while i < len(SHUTTLE_PASSWORDS) and not connected:
            connected = self.tryConnect(cell, SHUTTLE_PASSWORDS[i])
            i += 1

        return connected
