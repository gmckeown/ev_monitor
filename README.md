# ev_monitor
Simple Python 3 script to ping-monitor a device, sending alerts to Telegram when it changes state online/offline.

Initial intention was to monitor an EV charger to ensure it was online, but can be applied to any device where an ICMP echo is a usable monitoring mechanism

## Configuration
Copy the `ev_monitor.template.ini` file to `ev_monitor.ini` and change the values to suit your environment.
Copy `ev_monitor.service` to `/etc/systemd/system` and run the following:

```bash
sudo systemctl enable ev_monitor.service
sudo systemctl start ev_monitor.service
```

Thanks to "301_Moved_Permanently" on Stack Exchange Code Review for [refactoring suggestions](https://codereview.stackexchange.com/questions/273845/online-check-with-retry-logic-and-anti-flapping) incorporated in this script
