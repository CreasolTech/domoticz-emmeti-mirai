#!/usr/bin/env python
"""
domoticz-emmeti-mirai Heat Pump plugin for Domoticz.
Original Author: Patrick Hamers https://github.com/Sateetje (SPRSUN-Modbus plugin for Domoticz)
Author: Paolo Subiaco https://github.com/CreasolTech
Tested with Emmeti Mirai EH1018DC heat pump (Modbus, 9600bps, slave addr=1)

THIS SOFTWARE COMES WITH ABSOLUTE NO WARRANTY. 

** CHECK THE MANUAL OF YOUR EMMETI HEAT PUMP: DIFFERENT MODEL/VERSION HAVE DIFFERENT PARAMETER ADDRESS!!! **

Requirements:
    1.python module minimalmodbus -> http://minimalmodbus.readthedocs.io/en/master/
        (pi@raspberrypi:~$ sudo pip3 install minimalmodbus)
    2.Communication module Modbus USB to RS485 converter module
"""
"""
<plugin key="EmmetiMirai" name="Emmeti-Mirai heat pump" version="1.0" author="CreasolTech">
    <params>
        <param field="SerialPort" label="Modbus Port" width="200px" required="true" default="/dev/ttyUSB0" />
        <param field="Mode1" label="Baud rate" width="40px" required="true" default="9600"  />
        <param field="Mode2" label="Device ID" width="40px" required="true" default="1" />
        <param field="Mode6" label="Debug" width="75px">
            <options>
                <option label="True" value="Debug"/>
                <option label="False" value="Normal"  default="true" />
            </options>
        </param>
    </params>
</plugin>

"""

import minimalmodbus    #v2.1.1
import Domoticz         #tested on Python 3.9.2 in Domoticz 2021.1 and 2023.1



LANGS=[ "en", "it" ] # list of supported languages, in DEVS dict below
DEVADDR=0   #field corresponding to Modbus address in the DEVS dict
DEVUNIT=1
DEVTYPE=2
DEVSUBTYPE=3
DEVSWITCHTYPE=4
DEVOPTIONS=5
DEVIMAGE=6
DEVLANG=7  # item in the DEVS list where the first language starts 

DEVS={ #topic:                Modbus, Unit,Type,Sub,swtype, Options, Image,  "en name", "it name"  ...other languages should follow  ],
    "COMPRESSOR_MAX":       [ 16387,    1,244,73,7,    None,       None,   "Compressor max",   "Compressore max"   ],
    "COMPRESSOR_NOW":       [ 8996,     2,243,6,0,    None,       None,   "Compressor now",   "Compressore ora"   ],
    "SP_HOTWATER":          [ 16398,    3,242,1,0,  {'ValueStep':'1', ' ValueMin':'10', 'ValueMax':'60', 'ValueUnit':'°C'}, None,  "SetPoint Hot Water", "Termostato ACS"    ],
    "SP_HOTWATER_OUTLET":   [ 16400,    4,242,1,0,  {'ValueStep':'1', ' ValueMin':'10', 'ValueMax':'60', 'ValueUnit':'°C'}, None,  "SetPoint Hot Water outlet", "Termostato uscita per ACS" ],
    "SP_WINTER_MIN":        [ 16420,    5,242,1,0,  {'ValueStep':'1', ' ValueMin':'10', 'ValueMax':'60', 'ValueUnit':'°C'}, None,  "Temp min outlet Winter", "Temp. min uscita inverno"  ],
    "SP_WINTER_MAX":        [ 16421,    6,242,1,0,  {'ValueStep':'1', ' ValueMin':'20', 'ValueMax':'60', 'ValueUnit':'°C'}, None,  "Temp max outlet Winter", "Temp. max uscita inverno"  ],
    "SP_SUMMER_MIN":        [ 16427,    7,242,1,0,  {'ValueStep':'0.5', ' ValueMin':'6.5', 'ValueMax':'25', 'ValueUnit':'°C'}, None,  "Temp min outlet Summer", "Temp. min uscita estate"  ],
    "SP_SUMMER_MAX":        [ 16428,    8,242,1,0,  {'ValueStep':'0.5', ' ValueMin':'6.5', 'ValueMax':'25', 'ValueUnit':'°C'}, None,  "Temp max outlet Summer", "Temp. max uscita estate"  ],
    "TEMP_EXTERNAL":        [ 8973,     9, 80,5,0,  None,          None,   "Temp. ambient",    "Temp. esterna"     ],
    "TEMP_OUTLET":          [ 8974,     10,80,5,0,  None,          None,   "Temp. outlet",     "Temp. uscita"      ],
}

class BasePlugin:
    def __init__(self):
        self.rs485 = ""
        return

    def onStart(self):
        devicecreated = []
        Domoticz.Log("Starting Emmeti-Mirai plugin")
        Domoticz.Heartbeat(30)
        self.runInterval = 1
        self._lang=Settings["Language"]
        # check if language set in domoticz exists
        if self._lang in LANGS:
            self.lang=DEVLANG+LANGS.index(self._lang)
        else:
            Domoticz.Log(f"Language {self._lang} does not exist in dict DEVS, inside the domoticz-emmeti-mirai plugin, but you can contribute adding it ;-) Thanks!")
            self._lang="en"
            self.lang=DEVLANG # default: english text

        # Check that all devices exist, or create them
        for i in DEVS:
            if DEVS[i][DEVUNIT] not in Devices:
                Options=DEVS[i][DEVOPTIONS] if DEVS[i][DEVOPTIONS] else {}
                Image=DEVS[i][DEVIMAGE] if DEVS[i][DEVIMAGE] else 0
                Domoticz.Log(f"Creating device {i}, Name={DEVS[i][self.lang]}, Unit={DEVS[i][DEVUNIT]}, Type={DEVS[i][DEVTYPE]}, Subtype={DEVS[i][DEVSUBTYPE]}, Switchtype={DEVS[i][DEVSWITCHTYPE]} Options={Options}, Image={Image}")
                Domoticz.Device(Name=DEVS[i][self.lang], Unit=DEVS[i][DEVUNIT], Type=DEVS[i][DEVTYPE], Subtype=DEVS[i][DEVSUBTYPE], Switchtype=DEVS[i][DEVSWITCHTYPE], Options=Options, Image=Image, Used=1).Create()

        self.rs485 = minimalmodbus.Instrument(Parameters["SerialPort"], int(Parameters["Mode2"]))
        self.rs485.serial.baudrate = Parameters["Mode1"]
        self.rs485.serial.bytesize = 8
        self.rs485.serial.parity = minimalmodbus.serial.PARITY_EVEN
        self.rs485.serial.stopbits = 1
        self.rs485.serial.timeout = 1
        self.rs485.serial.exclusive = True # Fix From Forum Member 'lost'
        self.rs485.debug = True
        self.rs485.mode = minimalmodbus.MODE_RTU
        self.rs485.close_port_after_each_call = True

    def onStop(self):
        Domoticz.Log("Stopping Emmeti-Mirai plugin")

    def onHeartbeat(self):

        value=self.rs485.read_register(16387, 0, 3, False)
        for i in DEVS:
            try:
                value=self.rs485.read_register(DEVS[i][DEVADDR], 0, 3, False)
            except:
                Domoticz.Log(f"Error connecting to heat pump by Modbus, reading register {DEVS[i][DEVADDR]}");
            else:
                if i=="COMPRESSOR_MAX":
                    nValue=1 if value>0 else 0  # dimmer: nValue=1 (On) or 0 (Off)
                else:
                    nValue=int(value/10)
                sValue=str(value/10)
                Devices[DEVS[i][DEVUNIT]].Update(nValue=nValue, sValue=sValue)
                if Parameters["Mode6"] == 'Debug':
                    Domoticz.Log(f"{i}, Addr={DEVS[i][DEVADDR]}, nValue={nValue}, sValue={sValue}")

        self.rs485.serial.close()  #  Close that door !

    def onCommand(self, Unit, Command, Level, Hue):
        Domoticz.Log(f"Command for {Devices[Unit].Name}: Unit={Unit}, Command={Command}, Level={Level}")

        sValue=str(Level)
        nValue=int(Level)
        
        if Unit==DEVS["COMPRESSOR_MAX"][DEVUNIT]:   #dimmer
            if Level>100:
                Level=100
            nValue=1 if Level>0 else 0
                
            self.WriteRS485(DEVS["COMPRESSOR_MAX"][DEVADDR], Level*10)
        else:
            for i in DEVS:  # Find the index of DEVS
                if DEVS[i][DEVUNIT]==Unit:
                    self.WriteRS485(DEVS[i][DEVADDR], int(Level*10))
                    break


        Devices[Unit].Update(nValue=nValue, sValue=sValue)
#        Devices[Unit].Refresh()

    def WriteRS485(self, Register, Value):
            try:
                 self.rs485.write_register(Register, Value, 0, 6, False)

                 self.rs485.serial.close()
            except:
                Domoticz.Log("Error writing to heat pump Modbus");

global _plugin
_plugin = BasePlugin()

def onStart():
    global _plugin
    _plugin.onStart()

def onStop():
    global _plugin
    _plugin.onStop()

def onHeartbeat():
    global _plugin
    _plugin.onHeartbeat()

def onCommand(Unit, Command, Level, Hue):
    global _plugin
    _plugin.onCommand(Unit, Command, Level, Hue)

# Generic helper functions
def DumpConfigToLog():
    for x in Parameters:
        if Parameters[x] != "":
            Domoticz.Debug("'" + x + "':'" + str(Parameters[x]) + "'")
            Domoticz.Debug("Device count: " + str(len(Devices)))
    for x in Devices:
        Domoticz.Debug("Device:           " + str(x) + " - " + str(Devices[x]))
        Domoticz.Debug("Device ID:       '" + str(Devices[x].ID) + "'")
        Domoticz.Debug("Device Name:     '" + Devices[x].Name + "'")
        Domoticz.Debug("Device nValue:    " + str(Devices[x].nValue))
        Domoticz.Debug("Device sValue:   '" + Devices[x].sValue + "'")
        Domoticz.Debug("Device LastLevel: " + str(Devices[x].LastLevel))
    return


