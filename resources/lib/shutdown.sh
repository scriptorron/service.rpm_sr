#! /bin/sh

echo 0 > /sys/class/rtc/rtc0/wakealarm
case "$2" in
    0)
        # shutdown_method "Kodi"
        echo $1 > /sys/class/rtc/rtc0/wakealarm
        sync
        sync
        sync
    ;;
    1)
        # shutdown_method "OS"
        echo $1 > /sys/class/rtc/rtc0/wakealarm
        sync
        sync
        sync
        case "$3" in
            0)
            # shutdown_mode "Power Off"
            shutdown -h now "PVR Manager shutdown the system"
            ;;
            1)
            # shutdown_mode "Suspend"
            systemctl suspend
            ;;
            2)
            # shutdown_mode "Hibernate"
            systemctl suspend
            ;;
        esac
    ;;
    2)
        # shutdown_method "Y.A.R.D.2"
        yard2wakeup -I $1
        sync
        sync
        sync
        case "$3" in
            0)
            # shutdown_mode "Power Off"
            shutdown -h now "PVR Manager shutdown the system"
            ;;
            1)
            # shutdown_mode "Suspend"
            systemctl suspend
            ;;
            2)
            # shutdown_mode "Hibernate"
            systemctl suspend
            ;;
        esac
    ;;
esac
sleep 1
exit 0
