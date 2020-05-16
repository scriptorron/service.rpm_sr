from resources.lib.settings import *
from resources.lib.tools import *

Mon = Monitor()
Mon.definitions = setting_definitions
Mon.setAddonSetting('pwr_requested', True)
Mon.setAddonSetting('pwr_notified', False)
