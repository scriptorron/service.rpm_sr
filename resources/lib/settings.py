from resources.lib.tools import STRING, INT, BOOL

addon_settings = dict({'pvr_delay': INT, 'margin_start': INT, 'margin_stop': INT, 'server_mode': BOOL,
                       'notification_time': INT, 'shutdown_method': INT, 'sudo': BOOL,
                       'shutdown_mode': INT, 'show_next_sched': BOOL, 'check_network': BOOL,
                       'monitored_ports': STRING, 'check_postprocesses': BOOL, 'monitored_processes': STRING,
                       'epgtimer_interval': INT, 'epgtimer_time': INT, 'epgtimer_duration': INT,
                       'epg_mode': INT, 'epg_script': STRING, 'epg_file': STRING, 'epg_socket': STRING})
