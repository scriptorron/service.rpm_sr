from resources.lib.settings import *
from resources.lib.tools import *

Mon = Monitor()
Mon.definitions = settingsdefs
Mon.getSettings()
log('Settings loaded')
Mon.logSettings()

cycle = 30

def getPvrStatus():

    # check for recordings
    query = {'method': 'PVR.GetProperties', 'params': {'properties': ['recording']}}
    response = jsonrpc(query)
    if response and response.get('recording', False):
        return isREC

    # check for timers
    query = {'method': 'PVR.GetTimers', 'params': {'properties': ['starttime', 'startmargin', 'istimerrule', 'state']}}
    response = jsonrpc(query)
    if response and response.get('timers', False):
        for timer in response.get('timers'):
            if timer['istimerrule'] or timer['state'] == 'disabled':
                continue
            if time.mktime(time.strptime(timer['starttime'], JSON_TIME_FORMAT)) < time.mktime(time.gmtime()):
                continue
            elif time.mktime(time.strptime(timer['starttime'], JSON_TIME_FORMAT)) - Mon.setting['margin_start'] - \
                    Mon.setting['margin_stop'] < time.mktime(time.gmtime()):
                return isREC
    return isUSR

def getEpgStatus():

    # Check for EPG update
    if Mon.setting['epgtimer_interval'] > 0:
        __next = time.localtime() + (int(time.strftime('%j')) % Mon.setting['epgtimer_interval']) * 86400
        __n = datetime.fromtimestamp(__next).replace(hour=Mon.setting['epgtimer_time'],
                                                     minute=0, second=0, microsecond=0)
        if datetime.timestamp(__n) - Mon.setting['margin_start'] - \
                Mon.setting['margin_stop'] < \
                time.mktime(time.localtime()) < datetime.timestamp(__n) + (Mon.setting['epgtimer_duration'] * 60):
            return isEPG
    return isUSR

def getProcessStatus():
    if Mon.setting['check_post_processes']:
        processes = Mon.setting['monitored_processes'].split(',')

        for proc in processes:
            if getProcessPID(proc):
                return isPRG
    return isUSR

def getNetworkStatus():
    pass

def getStatusFlags():
    flags = isUSR
    flags |= getPvrStatus(flags)

def service():
    while Mon.waitForAbort(1):
        walker = 0
        while walker < cycle:
            if Mon.abortRequested:
                log('Abort requested')
                break
            if Mon.settingsChanged:
                log('SettingsChanged')
                break
            walker += 1
        if Mon.abortRequested:
            break
        if Mon.settingsChanged:
            Mon.getSettings()
            Mon.settingsChanged = False

