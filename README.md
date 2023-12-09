# domoticz-emmeti-mirai 
Domoticz Emmeti Mirai heat pump python plugin for Domoticz

Forked from simat-git/SDM120-Modbus 
Forked from Sateetje/SPRSUN-Modbus

This version allows multiple instances to work on Domoticz 2023.2 which uses multithreaded loading of the Plugins.
Exclusive access on the serial port is now enforced to ensure only one instance at a time can access that port.


# Installation
cd ~/domoticz/plugins<br>
git clone https://github.com/CreasolTech/domoticz-emmeti-mirai

Used python modules: <br>
minimalmodbus -> http://minimalmodbus.readthedocs.io<br>

Tested on domoticz 2023.2, Python 3.11.2.  MinimalModbus included is 2.1.1

