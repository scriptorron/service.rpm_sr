import xbmc
import xbmcaddon
import xbmcgui
import json
from urllib.parse import parse_qsl
import platform
import subprocess
import os
from datetime import datetime

addon = xbmcaddon.Addon()
addonpath = addon.getAddonInfo('path')
addonname = addon.getAddonInfo('name')
addonid = addon.getAddonInfo('id')
addonversion = addon.getAddonInfo('version')
loc = addon.getLocalizedString


STRING = 'STRING'
BOOL = 'BOOL'
NUM = 'NUM'
INT = 'INT'
BIN = 'BIN'

KEY_SELECT = 7

TIME_OFFSET = round((datetime.now() - datetime.utcnow()).seconds, -1)
JSON_TIME_FORMAT = '%Y-%m-%d %H:%M:%S'
LOCAL_TIME_FORMAT = '{} - {}'.format(xbmc.getRegion('dateshort'), xbmc.getRegion('time'))

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
        self.abortBySys = False
        self.hasPVR = False
        self.nextTimer = 0
        self.nextEPG = 0

        self.definitions = dict()        # {'setting_1': None, 'setting_2': BOOL, ...}
        self.setting = dict()            # returns {'setting_1': value_1, 'setting_2': value_2, ...}

    def onSettingsChanged(self):
        self.settingsChanged = True
        log('Addon settings changed', xbmc.LOGINFO)

        # determine difference between current and new settings and log only these
        set_current = set(self.setting.items())

        # read new settings
        self.getAddonSettings()

        # log difference
        self.logSettings(dict(set(self.setting.items()) - set_current))

    def onAbortRequested(self):
        self.abortBySys = True
        log('Abort requested', xbmc.LOGINFO)

    def getAddonSettings(self):
        for setting in self.definitions:
            try:
                if self.definitions[setting] == BOOL:
                    svalue = addon.getSettingBool(setting)
                elif self.definitions[setting] == NUM:
                    svalue = addon.getSettingNumber(setting)
                elif self.definitions[setting] == INT:
                    svalue = int(addon.getSetting(setting))
                else:
                    svalue = addon.getSettingString(setting)
            except (TypeError, ValueError):
                svalue = addon.getSetting(setting)
                log('invalid type of {}:{} ({} expected)'.format(setting, svalue,
                                                                 self.definitions[setting]), xbmc.LOGERROR)
            self.setting.update({setting: svalue})

    def setAddonSetting(self, setting, value):
        if self.definitions[setting] == BOOL:
            addon.setSettingBool(setting, bool(value))
        elif self.definitions[setting] == NUM:
            addon.setSettingNumber(setting, float(value))
        elif self.definitions[setting] == INT or self.definitions[setting] == BIN:
            addon.setSetting(setting, int(value))

    def logSettings(self, sdict=None):
        if sdict is None:
            sdict = self.setting
        for setting in sdict:
            if self.definitions[setting] == BIN:
                log('{:>22}: {:08b} {}'.format(setting, sdict[setting], type(sdict[setting])))
            else:
                log('{:>22}: {:<} {}'.format(setting, sdict[setting], type(sdict[setting])))

    def calcNextEvent(self):
        if self.nextEPG > 0:
            if 0 < self.nextTimer < self.nextEPG:
                return (30018, self.nextTimer)
            else:
                return (30019, self.nextEPG)
        elif self.nextTimer > 0:
            if 0 < self.nextEPG < self.nextTimer:
                return (30019, self.nextEPG)
            else:
                return (30018, self.nextTimer)
        return False


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


def notify(header, locstring, icon=xbmcgui.NOTIFICATION_INFO, disptime=5000):
    xbmcgui.Dialog().notification(header, locstring, icon=icon, time=disptime)


def jsonrpc(query):
    rpc = {"jsonrpc": "2.0", "id": 1}
    rpc.update(query)
    try:
        response = json.loads(xbmc.executeJSONRPC(json.dumps(rpc)))
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
    if not process:
        return False
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


def getPorts(port):
    _syscmd = subprocess.Popen(
        'netstat -an | grep -iE "(established|verbunden)" | grep -v "127.0.0.1" | grep ":{} "'.format(port),
        shell=True, stdout=subprocess.PIPE)
    aport = _syscmd.stdout.read().strip()
    return port if bool(aport) else False
