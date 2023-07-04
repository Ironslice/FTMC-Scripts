# -*- coding: utf-8 -*-
"""
Created on Mon Mar 20 16:18:44 2023

GUI for UC threshold measurement
@author: Manvydas Dapkevičius, Vilnius University
"""
from tkinter import filedialog
from tkinter import *
from tkinter import ttk
import tkinter as tk

import statistics
import tksheet
import matplotlib
import pandas as pd
import numpy as np
import sys
from sys import exit
import time
import datetime
import os
import serial
from pynput.keyboard import Controller, Key
keyboard = Controller()
import ctypes
import platform
import random
import traceback
import win32gui
import win32com.client
from threading import Thread
import csv
matplotlib.use('TkAgg')
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import (
    FigureCanvasTkAgg,
    NavigationToolbar2Tk
)
if sys.version_info >= (3,0):
    import urllib.parse
cur_dir = os.path.abspath(os.path.dirname(__file__)) # Specifies the current directory.
ximc_dir = os.path.join(cur_dir, "ximc") # Formation of the directory name with all dependencies. The dependencies for the examples are located in the ximc directory.
ximc_package_dir = os.path.join(ximc_dir, "crossplatform", "wrappers", "python") # Formation of the directory name with python dependencies.
sys.path.append(ximc_package_dir)  # add pyximc.py wrapper to python path
if platform.system() == "Windows":
    # Determining the directory with dependencies for windows depending on the bit depth.
    arch_dir = "win64" if "64" in platform.architecture()[0] else "win32" # 
    libdir = os.path.join(ximc_dir, arch_dir)
    if sys.version_info >= (3,8):
        os.add_dll_directory(libdir)
    else:
        os.environ["Path"] = libdir + ";" + os.environ["Path"] # add dll path into an environment variable

try: 
    from pyximc import *
except ImportError as err:
    print ("Can't import pyximc module. The most probable reason is that you changed the relative location of the test_Python.py and pyximc.py files. See developers' documentation for details.")
    exit()
except OSError as err:
    # print(err.errno, err.filename, err.strerror, err.winerror) # Allows you to display detailed information by mistake.
    if platform.system() == "Windows":
        if err.winerror == 193:   # The bit depth of one of the libraries bindy.dll, libximc.dll, xiwrapper.dll does not correspond to the operating system bit.
            print("Err: The bit depth of one of the libraries bindy.dll, libximc.dll, xiwrapper.dll does not correspond to the operating system bit.")
            # print(err)
        elif err.winerror == 126: # One of the library bindy.dll, libximc.dll, xiwrapper.dll files is missing.
            print("Err: One of the library bindy.dll, libximc.dll, xiwrapper.dll is missing.")
            print("It is also possible that one of the system libraries is missing. This problem is solved by installing the vcredist package from the ximc\\winXX folder.")
            # print(err)
        else:           # Other errors the value of which can be viewed in the code.
            print(err)
        print("Warning: If you are using the example as the basis for your module, make sure that the dependencies installed in the dependencies section of the example match your directory structure.")
        print("For correct work with the library you need: pyximc.py, bindy.dll, libximc.dll, xiwrapper.dll")
    else:
        print(err)
        print ("Can't load libximc library. Please add all shared libraries to the appropriate places. It is decribed in detail in developers' documentation. On Linux make sure you installed libximc-dev package.\nmake sure that the architecture of the system and the interpreter is the same")
    exit()
 
import simple as drv

category = {'IN': ['AUTO', '300mW', '30.0mW', '3.00mW', '300uW'],
            'OUT': ['AUTO','3.00mW','300uW', '30.0uW','3.00uW','0.30uW']}
global stoping, Measure
stoping = True
Measure = False


class Application(tk.Frame):
    
    def __init__(self, master=None):
        tk.Frame.__init__(self)
        self.frame2 = tk.Frame(root)
        master.title('UC threshold measurement')
        master.geometry("1000x600+10+10")
        
        
        self.is_on = True
        self.powervar = '0.0'
        
        self.path = ''
        self.getdata()
        self.createWidgets()
        self.createGraph()
        self.createSheet()
        self.commArduino()
        self.commOphir()
        self.commStandaFilter()
        
    
    def reconnect(self):
        self.ard.close()
        self.waithere(1000)
        self.commArduino()
        self.commOphir()
        self.commStandaFilter()
        
        
    def generatedata(self):
        x = random.randrange(3, 300000)
        y = 20052*x*(1+(1-np.sqrt(1+2*0.00201*x))/(0.00201*x))
        return x,y
        
    def generatepower(self):
        x = random.randrange(3, 300000)/100
        return x
    
    def getdata(self):    
        # data = pd.read_csv('C:\\Users\\manvy\\Desktop\\FTMC\\Duomenys\\20230313_netiesine galios priklausomybe test\\auto su internal rezimu\\data.csv', index_col=None, header=0)
        # self.powers = data.iloc[:, 0].to_numpy()
        # self.intensities = data.iloc[:, 1].to_numpy()
        self.powers = np.empty(0)
        self.intensities = np.empty(0)
    
    def getpath(self):
        root.directory = filedialog.askdirectory()
        self.txt1.configure(state='normal')
        self.txt1.insert(END, str(root.directory))
        self.txt1.configure(state='disabled')
        self.path = root.directory
        print (root.directory)
    
    def ShowXGraph(self, x, y):
        self.axes.clear()
        self.checkInput()
        if self.choices3.index(self.Plot_range) == 1:
            self.powerplot = np.asarray(self.sheet.get_column_data(0)).astype(float)
            self.axes.set_xlabel('Power, mW/cm2')
        else: 
            self.powerplot = np.asarray(self.sheet.get_column_data(0)).astype(float) / int(self.Power_multiplyer) * self.BeamArea
            x = x / int(self.Power_multiplyer) * self.BeamArea
            self.axes.set_xlabel('Power, mW')
        self.axes.scatter(self.powerplot, self.intensities)
        self.axes.scatter(x, y, marker ='x', s=30, c='red')
        self.axes.set_yscale('log')
        self.axes.set_xscale('log')
        self.axes.set_ylabel('Intensity, arb. units')
        self.axes.set_xlabel('Power, mW/cm2')
        self.axes.grid(True)
        self.figure_canvas.draw()
    
        
        
    def updateGraphR(self, arg):
        # print('updating graph')
        self.checkInput()
        self.axes.clear()
        self.powers = np.asarray(self.sheet.get_column_data(0)).astype(float)
        self.intensities = np.asarray(self.sheet.get_column_data(1)).astype(float)
        if self.choices3.index(self.Plot_range) == 1:
            self.powerplot = np.asarray(self.sheet.get_column_data(0)).astype(float)
            self.axes.set_xlabel('Power, mW/cm2')
        else: 
            self.powerplot = np.asarray(self.sheet.get_column_data(0)).astype(float) / int(self.Power_multiplyer) * self.BeamArea
            self.axes.set_xlabel('Power, mW')
        print(self.intensities)
        self.intensities = np.asarray(self.sheet.get_column_data(1)).astype(float)
        
        self.axes.scatter(self.powerplot, self.intensities)
        self.axes.set_yscale('log')
        self.axes.set_xscale('log')
        self.axes.set_ylabel('Intensity, arb. units')
        
        self.axes.grid(True)
        self.figure_canvas.draw()
        
        
    def refresh_sheet_Data_Add(self):
        # print('updating sheet')
        self.sheet.total_rows(0)
        self.sheet.set_column_data(0, values = tuple(self.powers), add_rows = True)
        self.sheet.set_column_data(1, values = tuple(self.intensities), add_rows = True, redraw = True)
        # print('updating sheet')
        arg = 1
        self.updateGraphR(arg)
        
    def createWidgets(self):
        
        self.Power_params = tk.LabelFrame(root, text="Power parameters", pady=2, bg = 'light grey', width = 30)
        self.Power_params.grid(column = 3, row = 2)
        self.Power_params.place(x=200, y=70)
        
        self.Measurement_params = tk.LabelFrame(root, text="Measurement parameters", bg = 'light grey', pady=2)
        self.Measurement_params.grid(column = 2, row = 11)
        self.Measurement_params.place(x=10, y=70)
        
        self.lb2=Label(root, text="Measurement folder:", fg='black', font=("Calibri", 12))
        self.lb2.place(x=10, y=10)
        
        self.txt1 = Text(root, state='disabled', height = 1, width = 89, bg = "light grey")
        self.txt1.place(x=10, y=45)
        
        self.btn1=Button(root, text = "Browse", command = self.getpath, width = 10)
        self.btn1.pack()
        self.btn1.place(x=160, y=10)
        
        self.btn2=Button(root, text = "Measurement START", command = self.Measure, height = 2, width = 20, bg = "green", font=("Calibri", 12))
        self.btn2.pack()
        self.btn2.place(x=630, y=80)
        
        self.btn3=Button(root, text = "Measurement STOP", command = self.StopMeasure, height = 2, width = 20, bg = "red", font=("Calibri", 12))
        self.btn3.pack()
        self.btn3.place(x=820, y=80)
        
        self.btn4=Button(root, text = "Reconnect devices", command = self.reconnect, height = 1, width = 16, bg = "light grey", font=("Calibri", 12))
        self.btn4.pack()
        self.btn4.place(x=850, y=10)
        
        self.lb3=Label(root, text="Sample Name:", fg='black', font=("Calibri", 12))
        self.lb3.place(x=300, y=10)
        self.name=Entry(root, text="Sample Name", fg='black', font=("Calibri", 12), width = 40)
        self.name.place(x=400, y=10)
        
        
                   
        # self.lbl=Label(root, text="Measurement parameters", fg='black', font=("Calibri", 12))
        # self.lbl.place(x=10, y=65)
        
        self.exp=Label(self.Measurement_params, text="Exposure, ms",  bg = 'light grey', fg='black', font=("Calibri", 10))
        self.exp.grid(column = 1, row = 1, sticky='e', ipadx=5, ipady=10)
        self.avg=Label(self.Measurement_params, text="Averaging",  bg = 'light grey', fg='black', font=("Calibri", 10))
        self.avg.grid(column = 1, row = 2, sticky='e', ipadx=5, ipady=10)
        self.exc=Label(self.Measurement_params, text="Excitation WL, nm",  bg = 'light grey', fg='black', font=("Calibri", 10))
        self.exc.grid(column = 1, row = 3, sticky='e', ipadx=5, ipady=10)
        self.pwr=Label(self.Measurement_params, text="Power multiplyer",  bg = 'light grey', fg='black', font=("Calibri", 10))
        self.pwr.grid(column = 1, row = 4, sticky='e', ipadx=5, ipady=10)
        self.comm=Label(self.Measurement_params, text="Comment",  bg = 'light grey', fg='black', font=("Calibri", 10))
        self.comm.grid(column = 1, row = 5, sticky='e', ipadx=5, ipady=10)
        self.start=Label(self.Measurement_params, text="Start point",  bg = 'light grey', fg='black', font=("Calibri", 10))
        self.start.grid(column = 1, row = 6, sticky='e', ipadx=5, ipady=10)
        self.stop=Label(self.Measurement_params, text="Stop point",  bg = 'light grey', fg='black', font=("Calibri", 10))
        self.stop.grid(column = 1, row = 7,sticky='e', ipadx=5, ipady=10)
        self.BeamSpot=Label(self.Measurement_params, text="Beam rad 1/e2, um",  bg = 'light grey', fg='black', font=("Calibri", 10))
        self.BeamSpot.grid(column = 1, row = 8, sticky='e', ipadx=5, ipady=10)
        self.BeamAng=Label(self.Measurement_params, text="Beam-Sample angle",  bg = 'light grey', fg='black', font=("Calibri", 10))
        self.BeamAng.grid(column = 1, row = 9, sticky='e', ipadx=5, ipady=10)
        self.IntF=Label(self.Measurement_params, text="Integrate from, nm",  bg = 'light grey', fg='black', font=("Calibri", 10))
        self.IntF.grid(column = 1, row = 10, sticky='e', ipadx=5, ipady=10)
        self.IntT=Label(self.Measurement_params, text="Integrate to, nm",  bg = 'light grey', fg='black', font=("Calibri", 10))
        self.IntT.grid(column = 1, row = 11, sticky='e', ipadx=5, ipady=10)
        
        
        self.exp=Entry(self.Measurement_params, text="Exposure", fg='black', font=("Calibri", 10), width = 6)
        self.exp.grid(column = 2, row = 1, ipadx=5, ipady=5)
        self.avg=Entry(self.Measurement_params, text="Averaging", fg='black', font=("Calibri", 10), width = 6)
        self.avg.insert(0, "1")
        self.avg.grid(column = 2, row = 2, ipadx=5, ipady=5)
        self.exc=Entry(self.Measurement_params, text="Excitation WL, nm", fg='black', font=("Calibri", 10), width = 6)
        self.exc.grid(column = 2, row = 3, ipadx=5, ipady=5)
        self.pwr=Entry(self.Measurement_params, text="Power multiplyer", fg='black', font=("Calibri", 10), width = 6)
        self.pwr.insert(0, "1")
        self.pwr.grid(column = 2, row = 4, ipadx=5, ipady=5)
        self.comm=Entry(self.Measurement_params, text="Comment", fg='black', font=("Calibri", 10), width = 6)
        self.comm.grid(column = 2, row = 5, ipadx=5, ipady=5)
        self.start=Entry(self.Measurement_params, text="Start point", fg='black', font=("Calibri", 10), width = 6)
        self.start.insert(0, "0")
        self.start.grid(column = 2, row = 6, ipadx=5, ipady=5)
        self.stop=Entry(self.Measurement_params, text="Stop point", fg='black', font=("Calibri", 10), width = 6)
        self.stop.insert(0, "33")
        self.stop.grid(column = 2, row = 7, ipadx=5, ipady=5)
        self.Beamspt=Entry(self.Measurement_params, text="um", fg='black', font=("Calibri", 10), width = 6)
        self.Beamspt.grid(column = 2, row = 8, ipadx=5, ipady=5)
        self.BeamAng=Entry(self.Measurement_params, text="deg", fg='black', font=("Calibri", 10), width = 6)
        self.BeamAng.insert(0, "90")
        self.BeamAng.grid(column = 2, row = 9, ipadx=5, ipady=5)
        self.IntF=Entry(self.Measurement_params, text="nm", fg='black', font=("Calibri", 10), width = 6)
        self.IntF.grid(column = 2, row = 10, ipadx=5, ipady=5)
        self.IntT=Entry(self.Measurement_params, text="nm2", fg='black', font=("Calibri", 10), width = 6)
        self.IntT.grid(column = 2, row = 11, ipadx=5, ipady=5)
        
        
        
        self.powervar = tk.StringVar()
        self.PowerValues=Label(root, bg = 'white', textvariable = self.powervar,  width = 14, height = 2, font=("Calibri", 14), borderwidth=2, relief="groove")
        self.PowerValues.place(x=470, y=70)
        
        
        
        self.on_buttonpwr1 = Button(self.Power_params, text="ON", command = self.powerON,  width = 6)
        self.on_buttonpwr1.grid(column = 1, row = 1, ipadx=5)
        # self.on_buttonpwr1.place(side = BOTTOM)
        
        self.on_buttonpwr2 = Button(self.Power_params, text="OFF", command = self.powerOFF,  width = 6)
        # self.on_buttonpwr2.place(x=360, y=90)
        self.on_buttonpwr2.grid(column = 1, row = 2, ipadx=5)
        
        self.RangeInfo=Label(self.Power_params, text="Power meter range:", fg='black', font=("Calibri", 10))
        self.RangeInfo.grid(column = 2, row = 1, ipadx=5)
        self.FillterInfo=Label(self.Power_params, text="Power meter filter:", fg='black', font=("Calibri", 10))
        self.FillterInfo.grid(column = 2, row = 2, ipadx=5)
        
        
        
        self.choiceVar = tk.StringVar()
        self.choices = ['AUTO', '300mW', '30.0mW', '3.00mW', '300uW']
        self.choiceVar.set(self.choices[0])
        self.cb = ttk.Combobox(self.Power_params, state="readonly", textvariable = self.choiceVar, values = self.choices, font=("Calibri", 10), width = 5)
        self.cb.bind('<<ComboboxSelected>>', self.getUpdateData)
        self.cb.grid(column = 3, row = 1, ipadx=5)
        
        self.choiceVar2 = tk.StringVar()
        self.choices2 = ['IN', 'OUT']
        self.choiceVar2.set(self.choices2[0])
        self.cb2 = ttk.Combobox(self.Power_params, state="readonly", textvariable = self.choiceVar2, values = list(category.keys()), font=("Calibri", 10), width = 5)
        self.cb2.bind('<<ComboboxSelected>>', self.UpdateFilter)
        self.cb2.grid(column = 3, row = 2, ipadx=5)
        
        self.choiceVar3 = tk.StringVar()
        self.choices3 = ['mW', 'mw/cm2']
        self.choiceVar3.set(self.choices3[0])
        self.cb3 = ttk.Combobox(root, state="readonly", textvariable = self.choiceVar3, values = self.choices3, font=("Calibri", 10), width = 5)
        self.cb3.bind('<<ComboboxSelected>>', self.updateGraphR)
        self.cb3.place(x=100, y=560)
        self.Xaxis=Label(root, text="X-axis units:", fg='black', font=("Calibri", 10))
        self.Xaxis.place(x=20, y=560)
        
        
        self.on_buttonsave = Button(root, text="SAVE DATA", command = self.SaveFile,  width = 12)
        self.on_buttonsave.place(x=300, y=560)
        
        self.on_buttonimport = Button(root, text="IMPORT DATA", command = self.ImportFile,  width = 12)
        self.on_buttonimport.place(x=200, y=560)
        
        self.my_canvas = tk.Canvas(root, width=50, height=50)  # Create 200x200 Canvas widget
        self.my_canvas.place(x=900, y=540)
        self.indicator = self.my_canvas.create_oval(20, 20, 50, 50)  # Create a circle on the Canvas
        self.my_canvas.itemconfig(self.indicator, fill="green")  # Fill the circle with GREED
        self.statusvar = tk.StringVar()
        self.StatusValues=Label(root, textvariable = self.statusvar,  width = 6, height = 2, font=("Calibri", 14), borderwidth=2)
        self.StatusValues.place(x=840, y=550)
        self.statusvar.set('Ready..')
    
    def UpdateFilter(self, event):
        self.cb['values'] = category[self.cb2.get()]
        self.choiceVar.set(self.choices[0])
        self.getUpdateData(event = None)
        
    def getUpdateData(self,  event):
        
        self.Power_range=self.choiceVar.get()
        self.Filter_present=self.choiceVar2.get()
        print(category[self.cb2.get()].index(self.Power_range), list(category.keys()).index(self.Filter_present))
        global stoping
        if stoping == False:
            stoping = True
            self.waithere(500)
            # self.OphirCOM.StopAllStreams() 
            # self.OphirCOM.SetRange(self.DeviceHandle, 0, category[self.cb2.get()].index(self.Power_range))
            # self.OphirCOM.SetFilter(self.DeviceHandle, 0, self.list(category.keys()).index(self.Filter_present))
            # self.OphirCOM.StartStream(self.DeviceHandle, 0)
            stoping = False
            self.powerUpdate()
        else:
            x=1
            # self.OphirCOM.SetRange(self.DeviceHandle, 0, category[self.cb2.get()].index(self.Power_range))
            # self.OphirCOM.SetFilter(self.DeviceHandle, 0, self.list(category.keys()).index(self.Filter_present))
        
        
    
    def createGraph(self):
                                            # GRAPHICAL SECTION
        # create a figure
        figure = Figure(figsize=(6, 4), dpi=100)
        
        # create axes
        self.axes = figure.add_subplot()
        # self.ax2 = self.axes.twiny()
        
        # create FigureCanvasTkAgg object
        self.figure_canvas = FigureCanvasTkAgg(figure, master=root)
        
        self.figure_canvas.get_tk_widget().place(x=400, y=150) 
        # create the toolbar
        # NavigationToolbar2Tk(self.figure_canvas, root)
        self.toolbar = NavigationToolbar2Tk(self.figure_canvas, self.frame2)
        self.frame2.place(x=400, y=550)
        
        # NavigationToolbar2Tk.get_tk_widget().place(x=400, y=750) 
        
        # create the barchart
        self.axes.scatter(self.powers, self.intensities)
        # self.ax2.set_xlim(self.axes.get_xlim())
        # self.axes.set_yscale('log')
        # self.axes.set_xscale('log')
        self.axes.grid(True)
        # axes.set_title('UC threshold')
        self.axes.set_ylabel('Intensity, arb. units')

        self.axes.set_xlabel('Power, mW')
        
        self.figure_canvas.draw()
        # figure_canvas.get_tk_widget().pack(side=tk.RIGHT, fill=tk.NONE, expand=1)
       
        # return figure_canvas, axes

        
        
    def createSheet(self):
                                                                # TABLE SECTION                                                  
        self.sheet = tksheet.Sheet(root, total_columns = 2, headers = ["Powers", "Intensities"], column_width = 65, show_x_scrollbar = False)
        self.sheet.set_column_data(0, values = tuple(self.powers), add_rows = True)
        self.sheet.set_column_data(1, values = tuple(self.intensities), add_rows = True)
        self.sheet.height_and_width(height = 400, width = 190)
        self.sheet.place(x=200, y=150)
        self.sheet.enable_bindings(("single_select",
        
                                "row_select",
        
                                "column_width_resize",
        
                                "arrowkeys",
        
                                "right_click_popup_menu",
        
                                "rc_select",
        
                                "rc_insert_row",
                                
                                "column_select",
                                
                                "drag_select",
                                
                                "select_all",
                                
                                "rc_delete_row",
        
                                "copy",
        
                                "cut",
        
                                "paste",
        
                                "delete",
        
                                "undo",
        
                                "edit_cell"))
        
        self.sheet.extra_bindings([("all_select_events", self.sheet_select_event)])
        self.sheet.extra_bindings([("rc_delete_row", self.updateGraphR)])
        
    def sheet_select_event(self, event = None):
        try:
                len(event)
        except:
                return
        try:
                if event[0] == "select_cell":
                    rowstart = f"{event[1]}"
                    rowend = f"{event[1]+1}"
                    
                    x = self.powers[int(rowstart):int(rowend)]
                    y = self.intensities[int(rowstart):int(rowend)]
                    # print("powers ", x)
                    # print("intensities ", y)
                    self.ShowXGraph(x, y)
                elif event[0] == "select_row":
                    rowstart = f"{event[1]}"
                    rowend = f"{event[1]+1}"
                    x = self.powers[int(rowstart):int(rowend)]
                    y = self.intensities[int(rowstart):int(rowend)]
                    # print("powers ", x)
                    # print("intensities ", y)
                    self.ShowXGraph(x, y)
                    
                elif "rows" in event[0]:
                    rowstart = f"{event[1][0]}"
                    rowend = f"{event[1][-1]+1}"
                    x = self.powers[int(rowstart):int(rowend)]
                    y = self.intensities[int(rowstart):int(rowend)]
                    # print("powers ", x)
                    # print("intensities ", y)
                    self.ShowXGraph(x, y)
                else:
                    print('wrong selection')
        except:
            print('')
    
    
    def commOphir(self):
        try:
          self.OphirCOM = win32com.client.Dispatch("OphirLMMeasurement.CoLMMeasurement")
          # Stop & Close all devices
          self.OphirCOM.StopAllStreams() 
          self.OphirCOM.CloseAll()
          # Scan for connected Devices
          DeviceList = self.OphirCOM.ScanUSB()
          # print(DeviceList)
          for Device in DeviceList:   	# if any device is connected
              self.DeviceHandle = self.OphirCOM.OpenUSBDevice(Device)	# open first device
              exists = self.OphirCOM.IsSensorExists(self.DeviceHandle, 0)
              if exists:
                  print('\n----------Connection with Starlabs S/N {0} sensor established---------------'.format(Device))
              else:
                  print('\nNo Starlabs power sensor attached to {0} !!!'.format(Device))
        except OSError as err:
            print('Ophir power meter failed to connect1')
            print("OS error: {0}".format(err))
        except:
            print('Ophir power meter failed to connect2')
            traceback.print_exc()
            
          
    def OphirWavelength(self, Excitation_wavelength):
        self.OphirCOM.ModifyWavelength(self.DeviceHandle, 0, 0, int(Excitation_wavelength))
        self.OphirCOM.SetWavelength(self.DeviceHandle, 0, 0)
        
        
    def commArduino(self):
        try:
            self.ard = serial.Serial(port='COM5', baudrate=9600, timeout = 2, write_timeout = 2, rtscts=False, dsrdtr=False)
            data = self.ArduinoWrite_Read('Handshake')
            self.waithere(500)
            data = self.ArduinoWrite_Read('Handshake2')
            self.waithere(500)
        except:
            print("Arduino failed to connect")
        else:
            print("Arduino OK")
            
            
    def ArduinoWrite_Read(self, x):
        self.ard.write(bytes(x, 'utf-8'))
        time.sleep(0.05)
        data = self.ard.readline()
        data = data.decode('utf-8').rstrip()
        return data
    
    
    def commStandaFilter(self):
        self.cal = pd.read_csv('StandaWheelCal.csv')
        ID = drv.init()
        if ID == -1:
            print('Standa filter failed to connect')
        if ID == 1:
            print('Standa filter OK')
            
            
    def readInput(self):
        self.Sample_name=self.name.get()
        self.Exposure=self.exp.get()
        self.Averaging=self.avg.get()
        self.Excitation_wavelength=self.exc.get()
        self.Power_multiplyer=self.pwr.get()
        self.Comment=self.comm.get()
        self.Start_point=self.start.get()
        self.End_point=self.stop.get()
        self.BeamRadius=self.Beamspt.get()
        self.Beam_angle=self.BeamAng.get()
        self.Integrate_from=self.IntF.get()
        self.Integrate_to=self.IntT.get()
        self.Power_range=self.choiceVar.get()
        self.Plot_range=self.choiceVar3.get()
        self.Filter_present=self.choiceVar2.get()
        
        
    def checkInput(self):
        
        self.readInput()
        
        cond = False
        if not self.Sample_name:
            print("Please Enter Sample Name")
            cond = True
        if not self.Exposure:
            print("Please Enter Exposure")
            cond = True
        if not self.Averaging:
            print("Please Enter Averaging")
            cond = True
        if not self.Power_multiplyer:
            print("Please Enter Power Multiplyer")
            cond = True
        if not self.Start_point:
            print("Please Enter Starting Point")
            cond = True
        if not self.End_point:
            print("Please Enter Ending Point")
            cond = True
        if not self.BeamRadius:
            print("Please Enter Beam Radius")
            cond = True
        if not self.Beam_angle:
            print("Please Enter Beam Angle")
            cond = True
        if not self.Integrate_from:
            print("Please Enter Integration Range")
            cond = True
        if not self.Integrate_to:
            print("Please Enter Integration Range")
            cond = True
        if not self.path:
            print("Please Enter Filepath")
            cond = True
        return cond
            

            
    def calculateBeamArea(self):
        self.BeamArea = ((int(self.BeamRadius)/10000) / (np.sin((int(self.Beam_angle))*np.pi/180))) * (int(self.BeamRadius)/10000) * np.pi
        # *(int(self.BeamRadius)/10000)**2*np.pi
        # print('Area in cm2 is: ', self.BeamArea)
        
        
    def powerUpdate(self):

        # BeamArea = self.calculateBeamArea()
        if stoping == False:
            # power = 0
            # power = self.OphirCOM.GetData(self.DeviceHandle, 0)
            # if len(power[0]) > 0:
            #     poweru = (power[0][0])*1000
            #     powerustr = '{:0.2e}'.format(poweru)
            #     self.powervar.set(powerustr + ' mW')
                
            x= self.generatepower()
            self.powervar.set(str(x) + ' mW/cm2')
            root.after(1000, self.powerUpdate)
            
            
    def powerOFF(self):
        # self.OphirCOM.StopAllStreams() 

        self.waithere(1000)
        self.ard.write(b"\no")
        print('first')
        self.waithere(10000)
        self.ard.write(b"\nb") 
        print('first')
        
        global stoping
        stoping = True


    def powerON(self):
        global stoping
        if stoping == False:
            print('Power Measurement already running')
        else:
            self.readInput()
            self.waithere(1000)
            self.ard.write(b"\nm") 
            filter1 = self.cal.iloc[int(self.Start_point), 0]
            filter2 = self.cal.iloc[int(self.Start_point), 1]
            drv.set_pos_calb(1, filter1, filter2)
            self.ard.flushInput()
            self.ard.flushOutput()
            self.waithere(1000)
            self.ard.write(b"\nt") 
            # self.OphirWavelength(self.Excitation_wavelength)
            # self.OphirCOM.SetRange(self.DeviceHandle, 0, self.choices.index(self.Power_range))
            # self.OphirCOM.SetFilter(self.DeviceHandle, 0, self.choices2.index(self.Filter_present))
            # self.OphirCOM.StartStream(self.DeviceHandle, 0)
            stoping = False
            self.powerUpdate()


    def calculatePowerDensity(self, poweravg):
        PowerDensity = ((poweravg*1000)/self.BeamArea) * int(self.Power_multiplyer)
        return PowerDensity
    
        
    def SaveFile(self):
        self.powers = np.asarray(self.sheet.get_column_data(0)).astype(float)
        self.intensities = np.asarray(self.sheet.get_column_data(1)).astype(float)
        df = pd.DataFrame(np.hstack((self.powers[:,None], self.intensities[:,None])), columns=['powers, mW/cm2', 'intensities, arb. units'])
        data = [("csv file(*.csv)","*.csv"),('All tyes(*.*)', '*.*')]
        file = filedialog.asksaveasfilename(filetypes = data, defaultextension = data)
        df.to_csv(file, sep=';', index = False)
        
        
    def ImportFile(self):
        cond = self.checkInput()
        if cond == True:
            print('Please Enter missing values')
        else:
            data = [("csv file(*.csv)","*.csv"),('All tyes(*.*)', '*.*')]
            file = filedialog.askopenfilename(filetypes = data, defaultextension = data)
            data = pd.read_csv(file, sep = ';', index_col=None, header=0)
            self.powers = data.iloc[:, 0].to_numpy()
            self.intensities = data.iloc[:, 1].to_numpy()
            self.refresh_sheet_Data_Add()
    
    
    def StopMeasure(self):
        global Measure
        Measure = False
        
        
    def waithere(self, time):
        var = IntVar()
        root.after(time, var.set, 1)
        root.wait_variable(var)
        
        
    def GetMeasurementData(self, start):
        global Measure
        if int(start)-1 < int(self.End_point) and Measure == True:
            start = int(start) + 1
            self.ard.flushInput()
            self.ard.flushOutput()
            self.statusvar.set('Running')
            self.my_canvas.itemconfig(self.indicator, fill="red")
            powerlist = []
            filter1 = self.cal.iloc[int(start)-1, 0]
            filter2 = self.cal.iloc[int(start)-1, 1]
            filter1val = self.cal.iloc[int(start)-1, 2]
            filter2val = self.cal.iloc[int(start)-1, 3]
            print('moving filter to position: ', filter1val*filter2val)
            self.ard.write(b"\nm") 
            drv.set_pos_calb(1, filter1, filter2)
            self.waithere(1000)
            self.ard.flushInput()
            self.ard.flushOutput()
            
            ######################### POWER MEASUREMENT
            power_measurement_time = 8
            exec_end_time = datetime.datetime.now() + datetime.timedelta(seconds = power_measurement_time)
            self.ard.write(b"\nt") 
            self.OphirCOM.StartStream(self.DeviceHandle, 0)
            self.waithere(1000) #Time for mechanical trigger
            while True:
                    power = self.OphirCOM.GetData(self.DeviceHandle, 0)
                    # print(OphirCOM.GetData(DeviceHandle, 0))
                    if len(power[0]) > 0:
                        powerlist.append(power[0][0]*int(self.Power_multiplyer))
                        # print(power[0][0])
                        if power[0][0] == 0.0:
                            print('Power meter saturated, use a neutral filter!')
                    self.waithere(200)
                    if datetime.datetime.now() >= exec_end_time:
                        break
            poweravg = statistics.median(powerlist)
            ######################### SAMPLE MEASUREMENT
            self.ard.write(b"\nb")
            self.waithere(6000)
            with keyboard.pressed(Key.ctrl):
                keyboard.press('a')
                keyboard.release('a')
            measurement_time = int(self.Exposure) * int(self.Averaging) * 2
            self.waithere(measurement_time)
            self.OphirCOM.StopAllStreams() 
            self.waithere(1000)
            self.ard.flushInput()
            self.ard.flushOutput()
            self.ard.write(b"\no")
            poweravgstr = '{:0.3e}'.format(poweravg)
            print('Measured power: ', poweravgstr, 'W')      
            # print('Measurement at ', filter1val*filter2val, ' transmission finished')
            self.waithere(6000)
            ######################## MEASUREMENT END
            
            ######################## HAMMAMATSU FILE RENAMING
            names = os.listdir(self.path)
            paths = [os.path.join(self.path, basename) for basename in names]
            latest_file = max(paths, key=os.path.getctime)
            new_name = root.directory + '\\' + self.Sample_name + '_exp_' + self.Exposure + 'ms_avg' + self.Averaging + 'x_Power_'+ poweravgstr + "W" + '_@' + self.Excitation_wavelength + 'nm_Ophir_filter_' + self.Filter_present + '_' + self.Comment + '.txp'
            os.rename(latest_file, new_name)
            data_to_save = [int(start)-1, filter1val*filter2val, self.Sample_name, self.Exposure, self.Averaging, poweravgstr, self.Filter_present, self.Power_range]
            with open(self.path + '\\' + 'ALL_DATA.csv' ,'a') as PowerLog: 
                writer = csv.writer(PowerLog)
                writer.writerow(data_to_save)
                
                
            ######################## GRAPHING AND CALCULATION
            self.calculateBeamArea()
            powerdensity = self.calculatePowerDensity(poweravg)
            
            
            df = pd.read_csv(new_name, sep='\t')
            df.columns = ['WL', 'SAMPLE']
            df = df[df['WL'] < int(self.Integrate_to)]
            df = df[df['WL'] > int(self.Integrate_from)]
            df['SAMPLE'] = df['SAMPLE']/(int(self.Exposure)/1000)
            Intensity = float(np.trapz([df['SAMPLE']]))
            self.powers = np.append(self.powers, powerdensity)
            self.intensities = np.append(self.intensities, Intensity)   
            self.refresh_sheet_Data_Add()
            
            # x, y = self.generatedata()
            # self.powers = np.append(self.powers, float(x))
            # self.intensities = np.append(self.intensities, float(y))
            # self.refresh_sheet_Data_Add()
            self.waithere(4000)
            root.after(1000, self.GetMeasurementData(start))
        else:    
            Measure = False
            self.OphirCOM.StopAllStreams() 
            drv.set_pos_calb(1, 1, 1) 
            self.statusvar.set('Ready..')  
            self.my_canvas.itemconfig(self.indicator, fill="green")
            
        
        
    def Measure(self):
        global Measure, stoping
        if Measure == True:
            print('Measurement already running')
        else:
            cond = self.checkInput()
            if cond == True:
                print('Please Enter missing values')
            else:
                Measure = True
                stoping = True
                self.waithere(500)
                self.BeamArea = self.calculateBeamArea()
                self.OphirWavelength(self.Excitation_wavelength)
                self.OphirCOM.SetRange(self.DeviceHandle, 0, self.choices.index(self.Power_range))
                self.OphirCOM.SetFilter(self.DeviceHandle, 0, self.choices2.index(self.Filter_present))
                
                self.GetMeasurementData(self.Start_point)
 
        

root=tk.Tk()
app=Application(master=root)
root.mainloop()

