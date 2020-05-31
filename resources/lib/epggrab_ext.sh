#! /bin/sh
#
# Please place your command line for grabbing epg-data from external provider here
# Make sure all grabbers are configured properly and choose the appropriate socket
# of tvheadend!
#
# More information about XMLTV: http://wiki.xmltv.org/index.php/Main_Page
# XMLTV Project Page: http://sourceforge.net/projects/xmltv/files/
#
# Arguments: SOCKET: path of PyEPG/XMLTV socket of tvheadend
#
SOCKET=/storage/.kodi/userdata/addon_data/service.tvheadend42/epggrab/xmltv.sock
# Provider: epgdata.com
# tv_grab_eu_epgdata --days=4 | nc -U $SOCKET
#
# Provider: Egon zappt (german)
tv_grab_eu_egon --days=4 | nc -w 5 -U $SOCKET
exit 0
