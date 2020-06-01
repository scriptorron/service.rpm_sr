from resources.lib.tools import *
import sys

if __name__ == '__main__':
    try:
        p = sys.argv[1]
        if p.lower() == 'poweroff':
            setProperty('pwr_requested', True)
            setProperty('pwr_notified', False)
        else:
            notify(addonname, loc(30029))
    except IndexError:
        log('no parameter provided, exiting')
        xbmcgui.Dialog().ok(addonname, loc(30002).format(addonname))

        # comment this out or delete it (testing)
        setProperty('pwr_requested', True)
        setProperty('pwr_notified', False)
