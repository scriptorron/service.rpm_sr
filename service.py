import datetime as datetime

from resources.lib.settings import *
from resources.lib.tools import *

import time

SHUTDOWN_CMD = xbmc.translatePath(os.path.join(addonpath, 'resources', 'lib', 'shutdown.sh'))
EXTGRABBER = xbmc.translatePath(os.path.join(addonpath, 'resources', 'lib', 'epggrab_ext.sh'))

Mon = Monitor()
Mon.definitions = setting_definitions
Mon.setAddonSetting('pwr_requested', False)
Mon.setAddonSetting('pwr_notified', False)

osv = release()
log('OS ID is {} {}'.format(osv['ID'], osv['VERSION_ID']), xbmc.LOGINFO)
if ('libreelec' or 'openelec' or 'coreelec') in osv['ID'].lower() and Mon.setting('sudo'):
    Mon.setAddonSetting('sudo', False)
    log('Reset wrong setting \'sudo\' to False')

Mon.settingsChanged = False
Mon.getAddonSettings()
Mon.logSettings()

cycle = 30


def checkPvrPresence(quiet=False):

    # check PVR presence
    if not quiet:
        notify(loc(30040), loc(30027), icon=xbmcgui.NOTIFICATION_INFO, disptime=3000)
    _delay = Mon.setting['pvr_delay']
    Mon.hasPVR = False

    while _delay > 0 and not Mon.hasPVR:
        query = {'method': 'PVR.GetProperties', 'params': {'properties': ['available']}}
        response = jsonrpc(query)
        if response:
            Mon.hasPVR = response.get('available', False)
        xbmc.sleep(1000)
        _delay -= 1

    if not Mon.hasPVR:
        log('No response from PVR', xbmc.LOGERROR)
        if not quiet:
            notify(loc(300409), loc(30032), icon=xbmcgui.NOTIFICATION_WARNING)
    return Mon.hasPVR


def getPvrStatus():

    if not checkPvrPresence(quiet=True):
        return isUSR

    # check for recordings
    query = {'method': 'PVR.GetProperties', 'params': {'properties': ['recording']}}
    response = jsonrpc(query)

    if response.get('recording', False):
        return isREC

    # check for timers
    Mon.nextTimer = 0
    query = {'method': 'PVR.GetTimers', 'params': {'properties': ['starttime', 'startmargin', 'istimerrule', 'state']}}
    response = jsonrpc(query)
    if response.get('timers', False):
        for timer in response.get('timers'):
            if timer['istimerrule'] or timer['state'] == 'disabled':
                continue
            if time.mktime(time.strptime(timer['starttime'], JSON_TIME_FORMAT)) < time.mktime(time.gmtime()):
                continue
            elif time.mktime(time.strptime(timer['starttime'], JSON_TIME_FORMAT)) - Mon.setting['margin_start'] - \
                    Mon.setting['margin_stop'] < time.mktime(time.gmtime()):
                return isREC
            else:
                Mon.nextTimer = time.mktime(time.strptime(timer['starttime'], JSON_TIME_FORMAT))
    return isUSR


def getEpgStatus():

    # Check for EPG update
    Mon.nextEPG = 0
    if Mon.setting['epgtimer_interval'] > 0:
        __next = time.mktime(time.localtime()) + (int(time.strftime('%j')) % Mon.setting['epgtimer_interval']) * 86400
        __n = datetime.fromtimestamp(__next).replace(hour=Mon.setting['epgtimer_time'],
                                                     minute=0, second=0, microsecond=0)
        if datetime.timestamp(__n) - Mon.setting['margin_start'] - \
                Mon.setting['margin_stop'] < \
                time.mktime(time.localtime()) < datetime.timestamp(__n) + (Mon.setting['epgtimer_duration'] * 60):
            return isEPG
        Mon.nextEPG = datetime.timestamp(__n) - TIME_OFFSET
    return isUSR


def getProcessStatus():

    # check for running processes
    if Mon.setting['check_postprocesses']:
        processes = Mon.setting['monitored_processes'].split(',')

        for proc in processes:
            if getProcessPID(proc.strip()):
                return isPRG
    return isUSR


def getNetworkStatus():

    # check for active network connection(s)
    if Mon.setting['check_network']:
        ports = Mon.setting['monitored_ports'].split(',')

        for port in ports:
            if getPorts(port.strip()):
                return isNET
    return isUSR

def getPwrStatus():
    if Mon.setting['pwr_requested']:
        return isPWR
    return isUSR

def getStatusFlags(flags):

    _flags = isUSR | getPvrStatus() | getEpgStatus() | getProcessStatus() | getNetworkStatus() | getPwrStatus()
    if _flags ^ flags:
        log('Status changed: {:05b} (PWR/NET/PRG/REC/EPG)'.format(_flags), xbmc.LOGINFO)
    return _flags


def service():

    flags = isUSR
    checkPvrPresence()

    while not Mon.waitForAbort(1):
        walker = 0
        while walker < cycle:
            if Mon.abortRequested():
                break
            if Mon.settingsChanged:
                break
            xbmc.sleep(1000)
            walker += 1

        if Mon.settingsChanged:
            Mon.getAddonSettings()
            Mon.settingsChanged = False

        flags = getStatusFlags(flags)
        if flags & isPWR:
            if not Mon.setting['pwr_notified']:
                if flags & isREC:
                    notify(loc(30015), loc(30020), icon=xbmcgui.NOTIFICATION_WARNING)  # Notify 'Recording in progress'
                elif flags & isEPG:
                    notify(loc(30015), loc(30021), icon=xbmcgui.NOTIFICATION_WARNING)  # Notify 'EPG-Update'
                elif flags & isPRG:
                    notify(loc(30015), loc(30022), icon=xbmcgui.NOTIFICATION_WARNING)  # Notify 'Postprocessing'
                elif flags & isNET:
                    notify(loc(30015), loc(30023), icon=xbmcgui.NOTIFICATION_WARNING)  # Notify 'Network active'
                Mon.setAddonSetting('pwr_notified', True)

            if not flags & (isREC | isEPG | isPRG | isNET):
                # power off
                if Mon.calcNextEvent():
                    _m, _t = Mon.calcNextEvent()
                    _ft = datetime.strftime(datetime.fromtimestamp(_t + TIME_OFFSET), LOCAL_TIME_FORMAT)
                    log('next schedule: {}'.format(_ft))
                    notify(loc(30024), loc(_m).format(_ft))
                else:
                    log('no schedules')
                    notify(loc(30040), loc(30014))




if __name__ == '__main__':
    service()
    log('Execution finished', xbmc.LOGINFO)
