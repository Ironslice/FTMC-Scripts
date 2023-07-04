import os
import sys
from sys import exit
import time
from ctypes import *
import pandas as pd
import numpy as np
import matplotlib as plt
import time
import os
import serial




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

 # All windows in attenuator wheels are marked:
 #     Wheel_1              Wheel_2
 #      "1": 0               "1": 0
 #      "0": 1               "0": 1
 #    "0.9": 2             "0.8": 2
 #    "0.5": 3             "0.3": 3
 #    "0.1": 4            "0.03": 4
 #   "0.01": 5           "0.003": 5
 #  "0.001": 6          "0.0003": 6
 # "0.0001": 7         "0.00003": 7

""" standart ".cfg" file, which can be downloaded to device using XILab,
    overloads command_homezero command, suitable for us """

""" Complicated variant with transition to user units """
def set_pos_calb(device_id, pos_wheel1, pos_wheel2):
    # att_id = 1
    calb = calibration_t()
    calb.A = c_double(0.04)             # 1 переход = 25 шагов
    
    calb.MicrostepMode = 1                 # режим без разделения на микрошаги
    lib.command_homezero(device_id)
    lib.command_wait_for_stop(device_id, 10)  # задержка, чтобы команды не перекрывались
    lib.command_move_calb(device_id, c_float(pos_wheel2), byref(calb))
    lib.command_wait_for_stop(device_id, 10)
    if pos_wheel1 > pos_wheel2:            # иначе колесо-1 будет цеплять колесо-2
        pos_wheel1 = pos_wheel1 - 8
    lib.command_move_calb(device_id, c_float(pos_wheel1), byref(calb))
    lib.command_wait_for_stop(device_id, 10)

""" or we can just multiply by 25 """
def set_pos(device_id, pos_wheel1, pos_wheel2):
    lib.command_wait_for_stop(device_id, 10)
    lib.command_move(device_id, 25*pos_wheel2, 0)
    lib.command_wait_for_stop(device_id, 10)
    if pos_wheel1 > pos_wheel2:
        pos_wheel1 = pos_wheel1 - 8
    lib.command_move(device_id, 25*pos_wheel1, 0)


# if __name__ == "__main__":
def init():    
    att_id = lib.open_device(b'xi-com:\\\\.\\'+(bytes('COM3', 'utf8')))
    lib.command_homezero(att_id)
    lib.command_wait_for_stop(att_id, 10)
    # global att_id
    # return att_id
    return att_id
    
def waitstop(device_id):
    lib.command_wait_for_stop(device_id)

# df = pd.read_csv('StandaWheelCal.csv')
# init()
#%%
# filter1 = 3
# filter2 = 4
# set_pos_calb(1, filter1, filter2)
#%%
#34 measureable points, starting from 0 to 33. 0 is full transmitance, 33 is no transmitance (0).
# start_point = 0
# end_point = 33
# timer = 20


# for i in range(start_point, end_point+1):
#     filter1 = df.iloc[i, 0]
#     filter2 = df.iloc[i, 1]
#     filter1val = df.iloc[i, 2]
#     filter2val = df.iloc[i, 3]
    
#     set_pos_calb(1, filter1, filter2)
#     print(filter1, filter2, filter1val, filter2val, filter1val*filter2val)
#     write_read('Trigger')
    # for i in range(timer):
    #     time.sleep(1)
    #     print('Time left for filter movement: ' + str(timer - i) + 's')
    
