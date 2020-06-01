from resources.lib.settings import *
from resources.lib.tools import *

import time

SHUTDOWN_CMD = xbmc.translatePath(os.path.join(addonpath, 'resources', 'lib', 'shutdown.sh'))
EXTGRABBER = xbmc.translatePath(os.path.join(addonpath, 'resources', 'lib', 'epggrab_ext.sh'))

Mon = Monitor()
Mon.settings = addon_settings

setProperty('pwr_requested', False)
setProperty('pwr_notified', False)

osv = release()
log('OS ID is {} {}'.format(osv['ID'], osv['VERSION_ID']), xbmc.LOGINFO)
if ('libreelec' or 'openelec' or 'coreelec') in osv['ID'].lower() and Mon.setting('sudo'):
    Mon.setSetting('sudo', False)
    log('Reset wrong setting \'sudo\' to False')

Mon.settingsChanged = False
Mon.getAddonSettings()
Mon.logSettings()

cycle = 5


def countDown():
    pbar = ProgressBar(loc(30010), loc(30011).format(loc(30040)),
                       Mon.setting['notification_time'], Mon.setting['notification_time'], reverse=True)
    return not pbar.show_progress()


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

    # check for recordings and timers
    Mon.nextTimer = 0
    query = {'method': 'PVR.GetTimers', 'params': {'properties': ['starttime', 'startmargin', 'istimerrule', 'state']}}
    response = jsonrpc(query)
    if response.get('timers', False):
        for timer in response.get('timers'):
            if timer['istimerrule'] or timer['state'] == 'disabled':
                continue
            if timer['state'] == 'recording':
                return isREC
            elif time.mktime(time.strptime(timer['starttime'], JSON_TIME_FORMAT)) - \
                    Mon.setting['margin_start'] - \
                    Mon.setting['margin_stop'] - \
                    Mon.setting['notification_time'] - \
                    (timer['startmargin'] * 60) + TIME_OFFSET < int(time.time()):
                return isREC
            else:
                Mon.nextTimer = time.mktime(time.strptime(timer['starttime'], JSON_TIME_FORMAT)) - \
                                Mon.setting['margin_start'] - (timer['startmargin'] * 60)
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
                time.mktime(time.localtime()) < datetime.timestamp(__n) + \
                (Mon.setting['epgtimer_duration'] * 60):
            return isEPG
        Mon.nextEPG = datetime.timestamp(__n) - Mon.setting['margin_start'] - TIME_OFFSET
        if Mon.nextEPG + Mon.setting['epgtimer_duration'] * 60 < time.mktime(time.localtime()):
            Mon.nextEPG += Mon.setting['epgtimer_interval'] * 86400
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
    if str2bool(getProperty('pwr_requested')):
        return isPWR
    return isUSR


def getStatusFlags(flags):

    _flags = isUSR | getPvrStatus() | getEpgStatus() | getProcessStatus() | getNetworkStatus() | getPwrStatus()
    if _flags ^ flags:
        log('Status changed: {:05b} (PWR/NET/PRG/REC/EPG)'.format(_flags), xbmc.LOGINFO)
    return _flags


def service():

    flags = getStatusFlags(isUSR)
    pwr_requested = False
    checkPvrPresence()

    # This is the initial startup after boot, if flags isREC | isEPG are set, a recording
    # or EPG update is immediately started. set isPWR to true, also set pwr-notified to true
    # avoiding notifications on initial startup

    if flags & (isREC | isEPG):
        setProperty('pwr_requested', True)
        setProperty('pwr_notified', True)

    while not Mon.waitForAbort(1):
        walker = 0
        while walker < cycle:
            if Mon.abortRequested():
                break
            if Mon.settingsChanged:
                break
            if str2bool(getProperty('pwr_requested')) ^ pwr_requested:
                walker = 0
                setProperty('pwr_notified', False)
                pwr_requested = str2bool(getProperty('pwr_requested'))
                break

            xbmc.sleep(2000)
            walker += 2

        if Mon.settingsChanged:
            Mon.getAddonSettings()
            Mon.settingsChanged = False

        if (xbmc.getGlobalIdleTime() < walker) and str2bool(getProperty('pwr_requested')):
            setProperty('pwr_requested', False)
            log('user activity detected, reset power status')

        flags = getStatusFlags(flags)
        if flags & isPWR:
            if not str2bool(getProperty('pwr_notified')):
                if flags & isREC:
                    notify(loc(30015), loc(30020), icon=xbmcgui.NOTIFICATION_WARNING)  # Notify 'Recording in progress'
                elif flags & isEPG:
                    notify(loc(30015), loc(30021), icon=xbmcgui.NOTIFICATION_WARNING)  # Notify 'EPG-Update'
                elif flags & isPRG:
                    notify(loc(30015), loc(30022), icon=xbmcgui.NOTIFICATION_WARNING)  # Notify 'Postprocessing'
                elif flags & isNET:
                    notify(loc(30015), loc(30023), icon=xbmcgui.NOTIFICATION_WARNING)  # Notify 'Network active'
            setProperty('pwr_notified', True)

            if not flags & (isREC | isEPG | isPRG | isNET):

                if not countDown():
                    setProperty('pwr_requested', False)
                    continue

                # power off
                _t = 0
                if Mon.calcNextEvent():
                    _m, _t = Mon.calcNextEvent()
                    _ft = datetime.strftime(datetime.fromtimestamp(_t + TIME_OFFSET), LOCAL_TIME_FORMAT)
                    log('next schedule: {}'.format(_ft))
                    notify(loc(30024), loc(_m).format(_ft))
                else:
                    log('no schedules')
                    notify(loc(30040), loc(30014))

                xbmc.sleep(5000)
                log('set RTC to {}'.format(_t))
                if osv['PLATFORM'] == 'Linux':
                    sudo = 'sudo ' if Mon.setting['sudo'] else ''
                    os.system('%s%s %s %s %s' % (sudo, SHUTDOWN_CMD, _t,
                                                 Mon.setting['shutdown_method'],
                                                 Mon.setting['shutdown_mode']))

                if Mon.setting['shutdown_method'] == 0 or osv['platform'] == 'Windows':
                    xbmc.shutdown()


if __name__ == '__main__':
    service()
    log('Execution finished', xbmc.LOGINFO)
