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
HOME = 10000

TIME_OFFSET = round((datetime.now() - datetime.utcnow()).seconds, -1)
JSON_TIME_FORMAT = '%Y-%m-%d %H:%M:%S'
LOCAL_TIME_FORMAT = '{} - {}'.format(xbmc.getRegion('dateshort'), xbmc.getRegion('time'))

# binary Flags

isPWR = 0b100000     # Poweroff requested
isATF = 0b010000     # Time Frame is active
isNET = 0b001000     # Network is active
isPRG = 0b000100     # Processes are active
isREC = 0b000010     # Recording is or becomes active
isEPG = 0b000001     # EPG grabbing is or becomes active
isUSR = 0b000000     # default


def setProperty(key, value):
    xbmcgui.Window(10000).setProperty(str(key), str(value))


def getProperty(key):
    return xbmcgui.Window(10000).getProperty(str(key))


def str2bool(value):
    return True if value.lower() == 'true' else False


class Monitor(xbmc.Monitor):

    def __init__(self):
        self.settingsChanged = False
        self.hasPVR = False
        self.waitForShutdown = True
        self.observe = False
        self.nextTimer = 0
        self.nextEPG = 0

        self.settings = dict()        # {'setting_1': None, 'setting_2': BOOL, ...}
        self.setting = dict()         # returns {'setting_1': value_1, 'setting_2': value_2, ...}

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
        log('Abort requested', xbmc.LOGINFO)

    def getAddonSettings(self):
        for setting in self.settings:
            try:
                if self.settings[setting] == BOOL:
                    svalue = addon.getSettingBool(setting)
                elif self.settings[setting] == NUM:
                    svalue = addon.getSettingNumber(setting)
                elif self.settings[setting] == INT:
                    svalue = int(addon.getSetting(setting))
                else:
                    svalue = addon.getSettingString(setting)
            except (TypeError, ValueError):
                svalue = addon.getSetting(setting)
                log('invalid type of {}:{} ({} expected)'.format(setting, svalue,
                                                                 self.settings[setting]), xbmc.LOGERROR)
            self.setting.update({setting: svalue})

    def setSetting(self, setting, value):
        if self.settings[setting] == BOOL:
            addon.setSettingBool(setting, bool(value))
        elif self.settings[setting] == NUM:
            addon.setSettingNumber(setting, float(value))
        elif self.settings[setting] == INT or self.settings[setting] == BIN:
            addon.setSetting(setting, int(value))

    def logSettings(self, sdict=None):
        if sdict is None:
            sdict = self.setting
        for setting in sdict:
            if self.settings[setting] == BIN:
                log('{:>22}: {:08b} type {}'.format(setting, sdict[setting], self.settings[setting]))
            else:
                log('{:>22}: {:<} type {}'.format(setting, sdict[setting], self.settings[setting]))

    def calcNextEvent(self):
        if self.nextEPG > 0:
            if 0 < self.nextTimer < self.nextEPG:
                return 30018, self.nextTimer
            else:
                return 30019, self.nextEPG
        elif self.nextTimer > 0:
            if 0 < self.nextEPG < self.nextTimer:
                return 30019, self.nextEPG
            else:
                return 30018, self.nextTimer
        return False

    def checkPvrPresence(self, quiet=False):

        # check PVR presence
        _delay = self.setting['pvr_delay']
        self.hasPVR = False

        while _delay > 0 and not self.hasPVR:
            query = {'method': 'PVR.GetProperties', 'params': {'properties': ['available']}}
            response = jsonrpc(query)
            if response:
                self.hasPVR = response.get('available', False)
            xbmc.sleep(1000)
            _delay -= 1

        if not self.hasPVR:
            log('No response from PVR', xbmc.LOGERROR)
            if not quiet:
                notify(loc(30040), loc(30032), icon=xbmcgui.NOTIFICATION_WARNING)


class ProgressBar(object):
    """
    creates a dialog progressbar with optional reverse progress
        :param header: heading line of progressbar
        :param msg: additional countdown message
        :param duration: duration of countdown
        :param steps: amount of steps of the countdown, choosing a value of 2*duration is perfect (actualising
               every 500 msec)
        :param reverse: reverse countdown (progressbar from 100 to 0)
        :returns true if cancel button was pressed, otherwise false
    """

    def __init__(self, header, msg, duration=10, steps=20, reverse=False):

        self.header = header
        self.msg = msg
        self.timeout = 1000 * duration // steps
        self.steps = 100 // steps
        self.reverse = reverse
        self.iscanceled = False

        self.pb = xbmcgui.DialogProgress()

        self.max = 0
        if self.reverse:
            self.max = 100

        self.pb.create(self.header, self.msg)
        self.pb.update(self.max, self.msg)

    def show_progress(self):

        percent = 100
        while percent >= 0:
            self.pb.update(self.max, self.msg)
            if self.pb.iscanceled():
                self.iscanceled = True
                break

            percent -= self.steps
            self.max = 100 - percent
            if self.reverse:
                self.max = percent
            xbmc.sleep(self.timeout)

        self.pb.close()
        xbmc.sleep(self.timeout)
        return self.iscanceled


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


def messageOk(header, locstring):
    xbmcgui.Dialog().ok(header, locstring)


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
    props = {'PLATFORM': platform.system(), 'HOSTNAME': platform.node(), 'ARCH': platform.machine()}
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
    elif OS['PLATFORM'] == 'Windows':
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
