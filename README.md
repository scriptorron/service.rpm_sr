Credits
=======

This is a fork of the genius "service.rpm" (https://github.com/b-jesch/service.rpm) made by Birger Jesch.

service.rpm_sr
==============

PVR 'Recording- & Power Manager NG²' for Kodi. This addon turns your Kodi on a Linux installation (pure Linux, Open-/LibreELEC) 
into a full featured video recorder (TV server and TV card required).

This addon handles power management for current active recordings and wakeup procedures for future schedules using 
the JSON-RPC-Interface of Kodi. The addon starts and shut down the HTPC if a recording needs to be scheduled.

The addon starts the system periodically on a user defined cycle and time for e.g. EPG-updates too if there is a longer 
inactivity time of the system or user. To collect the individual EPG data the script "epggrab_ext.sh" can be adapted to your needs.

The "service.rpm_sr" is a fork of the "service.rpm" addon. It handles the power management slightly different.

The addon runs an idle timer. Each user activity restarts this idle timer. User activities can be:
- inputs on keyboard, remote, mouse, game-pad or joystick or
- one or more of the monitored ports are open.

When the timer expires the addon checks if:
- a recording is running,
- an EPG update is running,
- the actual time is within the main activity time,
- a monitored process is running.

If one of these conditions is fulfilled the idle timer gets restarted again. Otherwise a countdown is shown on the screen, the next wake-up time is set and the HTPC shuts down.
Default idle time is 20 minutes (when Kodi does nothing) or 4 hours (when Kodi plays a media). The default setup for the monitored ports is for ssh, rsync Samba and DLNA/UPnP.

Examples for use cases are:
- After watching TV or a video you go to bed. It does not matter if you stopped playing, the addon will shutdown the HTPC for you.
- You have your music library on the HTPC and use Kodi as a DLNA/UPnP server. For listening music you switch on your HTPC and use an app on your mobile phone to select the music you want to hear on your WIFI speaker. Your HTPC will shutdown automatically when you finished listening music.
- You want your PVR to make timer based recordings. But you do not want to run you HTPC all the time. The addon will wake-up your HTPC for the recordings and shut it down when finished.
- You maintain your HTPC remotely with ssh, Samba or rsync. The HTPC will not shutdown as long as one of these remote connections are open.

Some installation notes
-----------------------
1.  THIS ADDON WORKS ONLY ON x86 BASED HARDWARE AS IT WRITES WAKEUP INFORMATIONS INTO THE HARDWARE (BIOS) RTC. IT DOESN'T WORK 
    ON AML NOR ARM BASED HARDWARE (ANDROID BOXES, RASPBERRY OR SIMILAR HARDWARE)
2.	YOU KNOW WHAT A TERMINAL CONSOLE IS AND YOU ARE ABLE TO USE IT.
3.	THIS ADDON USE ACPI-WAKEUP OVER RTC. YOUR MAINBOARD MUST SUPPORT THIS PROPERLY. NOTE THAT IN YOUR APM-SETTINGS OF 
    YOUR BOARD THE RTC WAKEUP SHOULD BE SET TO ‘by OS’ OR ‘disabled’. YOU CAN ALSO USE A SPECIAL USB REMOTE CONTROLLER 'Y.A.R.D.2'. 
    IF THIS IS CHOOSEN, THE RTC OF Y.A.R.D.2 IS USED. USEFULL FOR BOARDS WITHOUT RTC (RASPBERRY & CO.)
4.	PURE LINUX: THIS README USES ```kodi``` AS THE DEFAULT USER. IF KODI IS RUNNING WITH A DIFFERENT USERNAME, CHANGE ALL 
    OCCURENCES OF ```/home/kodi/``` TO ```/home/yourusername/``` IN YOUR PATHNAMES/NAMES.
5.  DO NOT ENABLE THE KODI "SHUTDOWN FUNCTION TIMER" IN "SETTINGS->SYSTEM->POWER SAVING". THIS ADDON IS A REPLACEMENT FOR THE
    "SHUTDOWN FUNCTION TIMER". THE KODI TIMER WILL NOT START YOUR HTPC FOR RECORDINGS.

Installation
------------

1.	Install this Addon from ZIP or from Repository

2.	If You are using OpenElec/LibreElec, the following step isn’t necessary. Skip to step 3. All others: As the shellscript ‘shutdown.sh’ is a wrapper to poweroff the system, it needs root privileges to run properly. We make it possible that ‘shutdown.sh’ runs under root/sudo privileges without needing to type in a password:


      sudo visudo
    
   add at the end of the file:
        
      Cmnd_Alias PVR_CMDS = /home/kodi/.kodi/addons/service.rpm_sr/resources/lib/shutdown.sh
      kodi ALL=NOPASSWD: PVR_CMDS
    
   Store your changes (CTRL+O, CTRL+X)

3. Change your remote.xml to point the addon when "Power" on remote is pressed. If you don't have a remote control you can also define a special key on your keyboard as power button (here as example F12).

        
   Create a remote.xml if it doesn't exists:
    
      nano $HOME/.kodi/userdata/keymaps/remote.xml
    
   and copy/paste following code into the editor: 
    
            <keymap>
                <global>
                    <!-- This is the keyboard section -->
                    <keyboard>
                        <f12>RunScript(service.rpm_sr,poweroff)</f12>
                    </keyboard>
                    <!-- This is the remote section -->
                    <remote>
                        <power>RunScript(service.rpm_sr,poweroff)</power>
                    </remote>
                </global>
            </keymap>

4.	Store (CTRL+O, CTRL+X), restart Kodi and enjoy!


Y.A.R.D.2
_________

You have to make sure that your system knows the path to the yard2wakeup executable. Insert this line into the .profile file in your user folder:

    nano $HOME/.profile
    
and add

     PATH="$PATH:$HOME/yard2
     
In this case $HOME/yard2 points to the installation folder of yard2wakeup. On *Elec systems this could be /storage/yard2


HOW TO FIND YOUR DLNA/UPNP PORT
-------------------------------

The addon monitors the DLNA/UPnP streaming port to avoid a shutdown during streaming. The default for this port is 1349. But this port number is not standardized and can differ on other installations. To find the port for your installation do:
1. Start Kodi but do not do DLNA/UPnP streaming.
2. Wait some time to allow other processes (for instance EPG update, OS update) to finish.
2. Log in to your HTPC and do on command line:

   `netstat -an | grep -iE "(established|verbunden)" | grep -v "127.0.0.1" > temp_before.txt`
3. Start DLNA/UPnP streaming and do within 5 seconds after playing a new track:

   `netstat -an | grep -iE "(established|verbunden)" | grep -v "127.0.0.1" > temp_after.txt ; diff temp_before.txt temp_after.txt`
4. The output will be one or more lines similar to:

   `> tcp        0      0 192.168.188.72:1349     192.168.188.30:39782    VERBUNDEN `

   Search the line were the second IP address (`192.168.188.30` in the example above) is your rendering device (the one you play the track). The first IP address (`192.168.188.72`) is your Kodi server. The DLNA/UPnP streaming port number follows the IP address of your Kodi server (`1349` in this example).

You need to do step 3 relatively quickly after the start of a new track because many render devices download and buffer the stream within the first seconds and close the streaming port until the playback of the track is finished.


ADDITIONAL FOR EXPERTS
----------------------

If you want to add a hook to the shutdown menu of kodi (this changes the behaviour of the power button), edit the ‘DialogButtonMenu.xml’ 
(or similar) in the xml part of the skin addon and look for a xml tag like (note the &lt;onclick&gt;Powerdown()&lt;/onclick&gt; inside here):

        <item>
            <label>$LOCALIZE[13016]</label>
            <onclick>Powerdown()</onclick>
            <visible>System.CanPowerDown</visible>
        </item>

and change this to:

        <item>
            <label>$LOCALIZE[13016]</label>
            <onclick>Powerdown()</onclick>
            <visible>System.CanPowerDown + !System.HasAddon(service.rpm_sr)</visible>
        </item>
        <item>
            <label>$LOCALIZE[13016]</label>
            <onclick>RunScript(service.rpm_sr,poweroff)</onclick>
            <visible>System.CanPowerDown + System.HasAddon(service.rpm_sr)</visible>
        </item>

Don’t forget to store. Remember that you have to repeat this when the skin has updated.

Please send Comments and Bugreports to no_spam@partyheld.de

HINT: If your OS is OpenELEC/LibreELEC you have to turn off ‘Shutdown requires admin privileges’ as OpenELEC/LibreELEC doesn’t need sudo! 
This should be done automatically by the addon in most cases.
