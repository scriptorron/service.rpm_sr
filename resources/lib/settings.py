from resources.lib.tools import STRING, INT, BOOL

setting_definitions = dict({'pwr_requested': BOOL, 'pwr_notified': BOOL, 'pvr_delay': INT, 'margin_start': INT,
                            'margin_stop': INT, 'notification_time': INT, 'shutdown_method': INT, 'sudo': BOOL,
                            'shutdown_mode': INT, 'show_next_sched': BOOL, 'check_network': BOOL,
                            'monitored_ports': STRING, 'check_postprocesses': BOOL, 'monitored_processes': STRING,
                            'epgtimer_interval': INT, 'epgtimer_time': INT, 'epgtimer_duration': INT,
                            'epg_grab_ext': BOOL, 'epg_socket': STRING, 'store_epg': BOOL, 'epg_path': STRING})
