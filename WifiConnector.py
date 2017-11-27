import json
import subprocess

from wifi import Cell, Scheme, exceptions
from pathlib import Path

INTERFACE = "wlan0"
SHUTTLE_SSID = "Soofa"
SHUTTLE_PASSWORDS = ["15383888", "15384888", "52347399", "31659399", "52354399", "52940399", "72983877", "74394344", "90136588", "90137588"]
JSONFILE = "./knowMacToPassword.json"


class ShuttleWiFiConnector:

    def __init__(self):
        if Path(JSONFILE).is_file():
            with open(JSONFILE, "r") as jsonfile:
                self.MACToPassword = json.load(jsonfile)
        else:
            self.MACToPassword = dict()

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
        schema = Scheme.for_cell(INTERFACE, SHUTTLE_SSID, cell, password)
        subprocess.call(["ifdown", "wlan0"])
        try:
            subprocess.check_call(["ifup", "wlan0"] + schema.as_args())
        except Exception as e:
            print(e)
            return False

        self.MACToPassword[cell.address] = password

        return True

    def TryConnectShuttle(self):
        connected = False
        cell = self.getBestCell(SHUTTLE_SSID)

        if cell:
            i = 0
            if cell.address in self.MACToPassword:
                connected = self.tryConnect(cell, self.MACToPassword[cell.address])

            while i < len(SHUTTLE_PASSWORDS) and not connected:
                connected = self.tryConnect(cell, SHUTTLE_PASSWORDS[i])
                i += 1

        return connected
