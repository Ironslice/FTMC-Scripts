# By M. Dapkevičius
# Vilnius University
import pandas as pd
import numpy as np
import matplotlib as plt
import sys
from sys import exit
import time
import datetime
import os
import serial
import pyautogui
import win32com.client
import traceback
import csv
ard = serial.Serial(port='COM6', baudrate=9600, timeout=2)


def write_read(x):
    ard.write(bytes(x, 'utf-8'))
    time.sleep(0.05)
    data = ard.readline()
    data = data.decode('utf-8').rstrip()
    return data
data = write_read('Handshake')
time.sleep(1)
data = write_read('Handshake2')
time.sleep(1)

if sys.version_info >= (3,0):
    import urllib.parse

cur_dir = os.path.abspath(os.path.dirname(__file__))
ximc_dir = os.path.join(cur_dir, "ximc")
ximc_package_dir = os.path.join(ximc_dir, "crossplatform", "wrappers", "python")
sys.path.append(ximc_package_dir)

if sys.platform in ("win32", "win64"):
    libdir = os.path.join(ximc_dir, sys.platform)
    os.environ["Path"] = libdir + ";" + os.environ["Path"]

try: 
    from pyximc import *
    from pyximc import MicrostepMode
except ImportError as err:
    print ('Can not import pyximc module.')
    exit()
except OSError as err:
    print ('Can not load libximc library.')
    exit()
import simple as drv
df = pd.read_csv('StandaWheelCal.csv')

ID = drv.init()
if ID == -1:
    print('Standa filter controller initialization failed')
if ID == 1:
    print('Standa filter controller initialization completed')
try:
 OphirCOM = win32com.client.Dispatch("OphirLMMeasurement.CoLMMeasurement")
 # Stop & Close all devices
 OphirCOM.StopAllStreams() 
 OphirCOM.CloseAll()
 # Scan for connected Devices
 DeviceList = OphirCOM.ScanUSB()
 for Device in DeviceList:   	# if any device is connected
  DeviceHandle = OphirCOM.OpenUSBDevice(Device)	# open first device
  exists = OphirCOM.IsSensorExists(DeviceHandle, 0)
  if exists:
   print('\n----------Connection with Starlabs S/N {0} sensor established---------------'.format(Device))
  else:
   print('\nNo Starlabs power sensor attached to {0} !!!'.format(Device))
except OSError as err:
 print("OS error: {0}".format(err))
except:
 traceback.print_exc()
 
print('Initialization completed, proceed to the next step')
#%%
#Measurement settings I
#34 measureable points, starting from 0 to 33. 0 is full transmitance, 33 is no transmitance (0).
# USER SECTION
start_point = 13 #min 0 
end_point = 28#max 33
# Use this section to move filter to starting position. This allows to set up exposure time.
filter1 = df.iloc[start_point, 0]
filter2 = df.iloc[start_point, 1]
drv.set_pos_calb(1, filter1, filter2)
ard.write(bytes("Trigger", 'utf-8')) 
print('Arrived at starting position:', start_point)

#%%
#Measurement settings II
exposure_time = 0.02 #seconds, same as Hamamatsu!!
averaging = 4 #same as Hamamatsu!!
series_name = 'DABNA0.5slenkstis'
excitation_wavelength = 3 #index: 0 - '640nm', 1 - '220nm', 2 - '830nm', 3 - '532nm', 4 - '370nm', 5 - '730nm'
ophir_range = 0 #index: 0 - 'AUTO', 1 - '300mW', 2 - '30.0mW', 3 - '3.00mW', 4 - '300uW'
ophir_filter = 0 #index: 0 - 'no filter present', 1 - 'filter installed'
filter_power_multiplier = 1 #multiply measured power by this value
neutral_filter = '' #tag to be present in names
destination_folder = r'C:\Users\Domantas-FNI\Desktop\Hamamatsu data\2023\20230313_netiesine galios priklausomybe test' #has to be the same as in Hamamatsu software!!
#%%
# Run this block to start the measurement
if excitation_wavelength == 0:
    ex = 640
elif excitation_wavelength == 1:
    ex = 220
elif excitation_wavelength == 2:
    ex = 830
elif excitation_wavelength == 3:
    ex = 532
elif excitation_wavelength == 4:
    ex = 370
elif excitation_wavelength == 5:
    ex = 730

ard.write(bytes("Off", 'utf-8'))
OphirCOM.SetWavelength(DeviceHandle, 0, excitation_wavelength)
OphirCOM.SetRange(DeviceHandle, 0, ophir_range)
OphirCOM.SetFilter(DeviceHandle, 0, ophir_filter)
print('Starting measurement')


for i in range(start_point, end_point+1):
    filter1 = df.iloc[i, 0]
    filter2 = df.iloc[i, 1]
    filter1val = df.iloc[i, 2]
    filter2val = df.iloc[i, 3]
    print('moving filter to position: ', filter1val*filter2val)
    drv.set_pos_calb(1, filter1, filter2)
    ard.flushInput()
    ard.flushOutput()
    # OphirCOM.StartStream(DeviceHandle, 0)
    powerlist = []
    print('sending trigger')
    measurement_time = exposure_time * averaging * 2
    if measurement_time < 8:
        measurement_time = 8
    exec_end_time = datetime.datetime.now() + datetime.timedelta(seconds = measurement_time)
    ard.write(bytes("Trigger", 'utf-8')) 
    OphirCOM.StartStream(DeviceHandle, 0)
    time.sleep(1)
    pyautogui.hotkey('ctrl', 'a')
    while True:
            power = OphirCOM.GetData(DeviceHandle, 0)
            # print(OphirCOM.GetData(DeviceHandle, 0))
            if len(power[0]) > 0:
                powerlist.append(power[0][0]*filter_power_multiplier)
                print(power[0][0])
                if power[0][0] == 0.0:
                    print('Power meter saturated, use a neutral filter!')
            time.sleep(.2)
            if datetime.datetime.now() >= exec_end_time:
                break
    poweravg = sum(powerlist)/len(powerlist)
    OphirCOM.StopAllStreams() 
    poweravgstr = '{:0.4e}'.format(poweravg)
    # OphirCOM.StopAllStreams() 
    print('Measured power: ', poweravg, 'W')    
    ard.write(bytes("Off", 'utf-8'))
    print('Measurement at ', filter1val*filter2val, ' transmission finished')
    time.sleep(2)
    
    names = os.listdir(destination_folder)
    paths = [os.path.join(destination_folder, basename) for basename in names]
    latest_file = max(paths, key=os.path.getctime)
    
    new_name = destination_folder + '\\' + series_name + '_exp_' + str(exposure_time*1000) + 'ms_avg' + str(averaging) + 'x_Power_'+ poweravgstr + "W" + '_@' + str(ex) + 'nm' + neutral_filter + '.txp'
    os.rename(latest_file, new_name)
    data_to_save = [i, new_name, poweravgstr, filter1val*filter2val, ]
    with open(destination_folder + '\\' + 'powerlog.csv' ,'a') as PowerLog: 
        writer = csv.writer(PowerLog)
        writer.writerow(data_to_save)
drv.set_pos_calb(1, 1, 1)        
print('all measurements finished')    

#%%
ophir_filter = 0
OphirCOM.SetWavelength(DeviceHandle, 0, excitation_wavelength)
OphirCOM.SetRange(DeviceHandle, 0, ophir_range)
OphirCOM.SetFilter(DeviceHandle, 0, ophir_filter)
OphirCOM.StartStream(DeviceHandle, 0)
powerlist = []
for i in range (0, 20):
    power = OphirCOM.GetData(DeviceHandle, 0)
    
    if len(power[0]) > 0:
        print(power[0][0])
        if power[0][0] == 0.0:
            print('Power meter saturated, use a neutral filter!')
        powerlist.append(power[0][0]*filter_power_multiplier)
    time.sleep(.2)
OphirCOM.StopAllStreams()

