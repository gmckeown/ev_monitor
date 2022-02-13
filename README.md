# ev_monitor
Simple Python 3 script to ping-monitor a device, sending alerts to Telegram when it changes state online/offline.

Initial intention was to monitor an EV charger to ensure it was online, but can be applied to any device where an ICMP echo is a usable monitoring mechanism

Thanks to "301_Moved_Permanently" on Stack Exchange Code Review for [refactoring suggestions](https://codereview.stackexchange.com/questions/273845/online-check-with-retry-logic-and-anti-flapping) incorporated in this script
