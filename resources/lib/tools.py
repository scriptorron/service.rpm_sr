import xbmc
import xbmcaddon
import xbmcgui
import re
import json
import time
from datetime import datetime
from urllib.parse import parse_qsl
import platform
import subprocess
import os

addon = xbmcaddon.Addon()
addonpath = addon.getAddonInfo('path')
addonname = addon.getAddonInfo('name')
addonid = addon.getAddonInfo('id')
addonversion = addon.getAddonInfo('version')


STRING = 0
BOOL = 1
NUM = 2
BIN = 3

KEY_SELECT = 7

JSON_TIME_FORMAT = '%Y-%m-%d %H:%M:%S'

# binary Flags

isPWR = 0b10000     # Poweroff requested
isNET = 0b01000     # Network is active
isPRG = 0b00100     # Processes are active
isREC = 0b00010     # Recording is or becomes active
isEPG = 0b00001     # EPG grabbing is or becomes active
isUSR = 0b00000     # default


class Monitor(xbmc.Monitor):

    def __init__(self):
        self.settingsChanged = False
        self.abortRequested = False
        self.definitions = dict()        # {'setting_1': None, 'setting_2': BOOL, ...}

        self.setting = dict()            # returns {'setting_1': value_1, 'setting_2': value_2, ...}

    def onSettingsChanged(self):
        self.settingsChanged = True

    def onAbortRequested(self):
        self.abortRequested = True

    def getSettings(self):
        for setting in self.definitions:

            try:
                svalue = addon.getSetting(setting)
                if self.definitions[setting] == BOOL:
                    svalue = True if svalue.lower() == 'true' else False
                elif self.definitions[setting] == NUM:
                    try:
                        svalue = int(re.match(r'\d+', svalue).group())
                    except AttributeError:
                        svalue = 0
                else:
                    svalue = addon.getSetting(setting)

            except ValueError:
                log('Could not read settings for {}'.format(setting))
                if self.definitions[setting] == BOOL:
                    svalue = False
                elif self.definitions[setting] == NUM or self.definitions[setting] == BIN:
                    svalue = 0
                else:
                    svalue = ''

            self.setting.update({setting: svalue})

    def logSettings(self):
        for setting in self.setting:
            if self.definitions[setting] == BIN:
                log('{:>22}: {:08b}'.format(setting, self.setting[setting]))
            else:
                log('{:>22}: {:<}'.format(setting, self.setting[setting]))


class KeyMonitor(xbmcgui.WindowDialog):

    def __init__(self):
        log('create KeyMonitor object')
        self.abort = False
        xbmcgui.WindowDialog.__init__(self)
        self.show()

    def onAction(self, action):
        log('Keypress detected: %s' % action)
        if action == KEY_SELECT:
            self.abort = True


def log(message, level=xbmc.LOGDEBUG):
    xbmc.log('[{} {}]: {}'.format(addonid, addonversion, message), level)


def jsonrpc(query):
    rpc = {"jsonrpc": "2.0", "id": 1}
    rpc.update(query)
    try:
        response = json.loads(xbmc.executeJSONRPC(json.dumps(rpc, encoding='utf-8')))
        if 'result' in response:
            return response['result']
    except TypeError as e:
        log('Error executing JSON RPC: {}'.format(e), xbmc.LOGERROR)
    return False


def release():
    props = {'PLATFORM': platform.system(), 'HOSTNAME': platform.node()}
    if props['PLATFORM'] == 'Linux':
        with open('/etc/os-release', 'r') as _file:
            for line in _file:
                props.update(dict(parse_qsl(line.replace('"', '').strip())))
    return props


def getProcessPID(process):
    if not process: return False
    OS = release()
    if OS['PLATFORM'] == 'Linux':
        _syscmd = subprocess.Popen(['pidof', '-x', process], stdout=subprocess.PIPE)
        PID = _syscmd.stdout.read().strip()
        return PID if bool(PID) else False
    elif OS['platform'] == 'Windows':
        _tlcall = 'TASKLIST', '/FI', 'imagename eq {}'.format(os.path.basename(process))
        _syscmd = subprocess.Popen(_tlcall, shell=True, stdout=subprocess.PIPE)
        PID = _syscmd.stdout.read().splitlines()
        if len(PID) > 1 and os.path.basename(process) in PID[-1]:
            return PID[-1].split()[1]
        else:
            return False
    else:
        return False
