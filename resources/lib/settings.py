from resources.lib.tools import STRING, INT, BOOL

addon_settings = dict({'pvr_delay': INT, 'margin_start': INT, 'margin_stop': INT,
                       'main_activity': BOOL, 'main_activity_start': INT, 'main_activity_stop': INT,
                       'ignore_useractivity': BOOL, 'notification_time': INT, 'shutdown_method': INT, 'sudo': BOOL,
                       'idle_time': INT, 'idle_time_playing': INT, 'shutdown_mode': INT, 'show_next_sched': BOOL, 'check_network': BOOL,
                       'monitored_ports': STRING, 'check_postprocesses': BOOL, 'monitored_processes': STRING,
                       'epgtimer_interval': INT, 'epgtimer_time': INT, 'epgtimer_duration': INT,
                       'epg_mode': INT, 'epg_script': STRING, 'epg_file': STRING, 'epg_socket': STRING})
