# .\VENV\Scripts\activate
import json
import numpy as np
import os
import serial.tools.list_ports

from comms.vfd import ModbusThread
from comms.Arduino import Arduino

from datetime import datetime
from tkinter import *
from time import time
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from threading import Thread
from math import floor  # Import floor function for rounding down
from datetime import timedelta
from time import sleep
from tkinter import Entry, Button, Frame, Label, LEFT, RIGHT, NORMAL, DISABLED

# vfd = None
# - - Global Variables - -
data_arduino = []
thermocouple_data = []
recorded_values = []
gui_update_rate = 500  # ms

vfd = None
def scan_serial_ports():
    return [port.device for port in serial.tools.list_ports.comports()]

def save_data():
    date = datetime.now().strftime('%Y-%m-%d - %H-%M')
    if not os.path.exists('data'):
        os.makedirs('data')
    np.savetxt(
        'data/' + date + ' - Arduino.csv',
        np.asarray(data_arduino),
        delimiter=','
    )
    np.savetxt(
        'data/' + date + ' - VFD.csv',
        np.asarray(recorded_values),
        delimiter=','
    )

class CommsPanel(Frame):
    defaults_filename = 'defaults.json'

    def __init__(self, parent,  graph_panel, frame_vfd_controls, **kwargs):
        super().__init__(parent,
                         padx=40, pady=10,
                         borderwidth=1, relief=GROOVE,
                         **kwargs)

        self.options_serial = ['empty']
        self.graph_panel = graph_panel  # Reference to GraphPanel
        self.frame_vfd_controls = frame_vfd_controls  # Store the frame_vfd_controls instance

        self._build_gui()

        self.search_serial()

        self.load_defaults()

    def _build_gui(self):
        frame_sub = Frame(self)
        frame_sub.pack()

        label_arduino = Label(frame_sub, text='Arduino')
        label_vfd = Label(frame_sub, text = 'VFD')

        button_search_serial = Button(frame_sub, text='Search',
                                      command=self.search_serial)
        self.comm_arduino = StringVar()
        self.menu_arduino = OptionMenu(frame_sub, self.comm_arduino,
                                       *self.options_serial)
        self.comm_vfd = StringVar()
        self.menu_vfd = OptionMenu(frame_sub, self.comm_vfd,
                                      *self.options_serial)
        self.button_arduino = Button(
            frame_sub,
            text='Connect',
            width=10,
            command=self.connect_arduino
        )
        self.button_vfd = Button(
            frame_sub,
            text='Connect',
            width=10,
            command=self.connect_vfd
        )
        Label(frame_sub, text='Peripheral Setup', font='Helvetica 14 bold') \
            .grid(row=0, column=0, columnspan=3)

        label_arduino.grid(row=1, column=0, sticky=E)
        label_vfd.grid(row=2, column=0, sticky=E)

        button_search_serial.grid(row=2, column=1, rowspan=2, sticky=N + S)

        self.menu_arduino.grid(row=1, column=2, sticky=E + W)
        self.button_arduino.grid(row=1, column=3)
        self.menu_vfd.grid(row=2, column=2, sticky=E + W)
        self.button_vfd.grid(row=2, column=3)

        
    def save_defaults(self):
        if os.path.exists(self.defaults_filename):
            os.remove(self.defaults_filename)
        with open(self.defaults_filename, 'w+') as output_file:
            defaults = {
                'comm_arduino': self.comm_arduino.get(),'comm_vfd': self.comm_vfd.get()
            }
            json.dump(defaults, output_file)

    def load_defaults(self):
        if not os.path.exists(self.defaults_filename):
            return
        with open(self.defaults_filename, 'r+') as input_file:
            defaults = json.load(input_file)
            if defaults['comm_arduino'] in self.options_serial:
                self.comm_arduino.set(defaults['comm_arduino'])
            if defaults['comm_vfd'] in self.options_serial:
                self.comm_vfd.set(defaults['comm_vfd'])

    def search_serial(self):
        menu_arduino = self.menu_arduino['menu']
        menu_arduino.delete(0, 'end')

        menu_vfd = self.menu_vfd['menu']
        menu_vfd.delete(0, 'end')
        self.options_serial = scan_serial_ports()
        self.comm_arduino.set('')
        for port in self.options_serial:
            menu_arduino.add_command(
                label=port,
                command=lambda x=port: self.comm_arduino.set(x)
            )
            menu_vfd.add_command(
                label=port,
                command=lambda x=port: self.comm_vfd.set(x)
            )
    def connect_arduino(self):
        global arduino
        print('- - Connecting to the Arduino - -')

        arduino = Arduino(
            self.comm_arduino.get(),
            data_var=data_arduino,thermocouple_data=thermocouple_data
        )

        arduino.connect()

        if arduino.ping():
            print('Arduino ping successful')
            arduino.start()
            self.button_arduino.config(text='Disconnect', bg='red',
                                       command=self.disconnect_arduino)
        else:
            print('Arduino ping failed')
            self.button_arduino.config(bg='light yellow')

        self.save_defaults()
        print('- - Connected to Arduino - -')
    
    

    def connect_vfd(self):
        global vfd
        print('- - Connecting to the VFD - -')
        
        rs485_port = self.comm_vfd.get()
        slave_address = 1  # Assuming 1 is the correct slave address for your VFD.
        write_value = 0  # Initialize with a default write value or obtain it from the GUI as needed.

        # Initialize the ModbusThread with the selected serial port and parameters.
        vfd = ModbusThread(rs485_port, slave_address, write_value, data_var=recorded_values)

        # Attempt to connect to the VFD.
        if vfd.connect():
            print(f"Connected to {rs485_port} with slave address {slave_address}")
            
            # Check if the connection is successfully established using is_connected().
            if vfd.is_connected():
                vfd.start()  # Start the thread if connected.
                self.button_vfd.config(text='Disconnect', bg='red', command=self.disconnect_vfd)
                self.frame_vfd_controls.enable()  # Enable VFD controls on successful connection.
                print('- - Connected to VFD - -')
            else:
                print('Failed to establish a connection with the VFD.')
                self.button_vfd.config(bg='light yellow')
        else:
            print('Failed to connect to the VFD.')
            self.button_vfd.config(bg='light yellow')

        self.save_defaults()

    # def connect_vfd(self):
    #     global vfd
    #     global recorded_values
    #     print('- - Connecting to the VFD - -')
        
    #     rs485_port = self.comm_vfd.get()
    #     slave_address = 1  # Set the appropriate slave address
    #     write_value = 0  # Set the appropriate default write value

    #     vfd = ModbusThread(rs485_port, slave_address, write_value, data_var=recorded_values)

    #     vfd.connect()

        
    #     if vfd.is_connected:
    #         vfd.start()

    #         self.button_vfd.config(text='Disconnect', bg='red',
    #                                   command=self.disconnect_vfd)
    #         # Enable the button_set_write_v
    #         self.frame_vfd_controls.enable()
    #     else:
    #         self.button_vfd.config(bg='light yellow')

    #     self.save_defaults()

    #     print('- - Connected to VFD - -')

    

    def disconnect_vfd(self):
        global vfd

        print('- - Disconnecting from VFD - -')

        # Check if there is an existing vfd instance and stop it
        if vfd and isinstance(vfd, ModbusThread):
            vfd.disconnect()

        self.button_vfd.config(text='Connect', bg='green', command=self.connect_vfd)
        frame_vfd_controls.disable()

        print('- - Disconnected from VFD - -')

    
   


    def disconnect_arduino(self):
        print('- - Disconnecting from Arduino - -')
        arduino.stop()
        arduino.disconnect()

        self.button_arduino.config(text='Connect', bg='SystemButtonFace',
                                  command=self.connect_arduino)





class VFD_Controls(Frame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent,
                         padx=40, pady=10,
                         borderwidth=1, relief="groove",
                         **kwargs)

        
        self._build_gui()

    def _build_gui(self):
        frame_sub = Frame(self)
        frame_sub.pack()

        frame_frequency = Frame(frame_sub)

        self.frequency = Entry(frame_frequency, width=20)
        Label(frame_frequency, text='Pressure [torr]:').pack(side=LEFT)
        Label(frame_frequency, text=' ').pack(side=LEFT)
        self.frequency.pack(side=RIGHT)

        
        self.button_set_write_v = Button(frame_sub, text='write_frequency', command=self.set_write_v, state=DISABLED)
        # self.button_stop = Button(frame_sub, text='Stop', width=10,
        #                      command=self.stop_running, state=DISABLED)
        # self.button_start = Button(frame_sub, text='Start',
        #                           width=10, command=self.start_vfd)
        # self.button_save = Button(frame_sub, text='Save', width=10,
        #                      command=self.save_data, state=DISABLED)
       

        Label(frame_sub, text='VFD Controls', font='Helvetica 14 bold').grid(row=0, column=0, columnspan=2)

        Label(frame_sub, text='').grid(row=3, column=0, columnspan=2)
        frame_frequency.grid(row=4, column=0, columnspan=2)
        Label(frame_sub, text='').grid(row=5, column=0, columnspan=2)
        

        self.button_set_write_v.grid(row=6, column=0, columnspan=2, sticky='ew', pady=10)
        # self.button_stop.grid(row=7, column=0, columnspan=2, sticky='ew', pady=10)
        # self.button_start.grid(row=8, column=0, columnspan=2, sticky='ew', pady=10)
        # self.button_save.grid(row=9, column=0, columnspan=2, sticky='ew', pady=10)
        
        



    def enable(self):
        self.button_set_write_v['state'] = NORMAL

    def disable(self):
        self.button_set_write_v['state'] = DISABLED

    # def start_vfd(self):
    #     print('- - Starting VFD - -')

    #     if vfd is not None and vfd.is_connected():
    #         vfd.record(start_time=time())
    #         vfd.start_vfd()

        

    #     self.button_start['state'] = DISABLED
    #     self.button_stop['state'] = NORMAL
    # def stop_running(self):
    #     print('- - Stop Plotting - -')

    #     if vfd is not None and vfd.is_connected():
    #         vfd.stop()

        
    #     self.button_set_write_v['state'] = NORMAL
    #     self.button_stop['state'] = DISABLED
    #     self.button_start['state'] = NORMAL
    #     self.button_save['state'] = NORMAL

    # def save_data(self):
    #     print('- - Save Data - -')

    #     save_data()

    #     print('- - Save Complete - -')

    def set_write_v(self):
        try:
            user_input = float(self.frequency.get())
            write_value = float((user_input /50.0)* 10000.0)
            print(f'Set write_value: {write_value} based on user input: {user_input}')
        except ValueError:
            print('Input Error: Frequency must be an integer value')
            return
        vfd.set_write_value(write_value)

    

    

class GraphPanel(Frame):

    def __init__(self, parent, **kwargs):
        super().__init__(parent,
                         borderwidth=1, relief=GROOVE,
                         **kwargs)
        self._build_gui()

    def _build_gui(self):
        frame_graph = Frame(self, background='white')
        frame_graph.pack(side=TOP, fill=BOTH, expand=True)

        frame_graph.columnconfigure(0, weight=1)
        frame_graph.columnconfigure(1, weight=1)

        Label(frame_graph, background='white',
              text='Pressure', font='Helvetica 14 bold') \
            .grid(row=0, column=0, sticky=E + W)

        

        figure_arduino = Figure(figsize=(5, 4), dpi=100)
        self.axes_arduino = figure_arduino.add_subplot(111)
        self.axes_arduino.set_xlabel('Time [s]')
        self.axes_arduino.set_ylabel('Pressure [torr]')
        self.axes_arduino.grid(1)
        self.axes_arduino.set_xlim([0, 1])
        self.axes_arduino.set_ylim([0, 250])

        self.line_arduino, = self.axes_arduino.plot(
            [0], [0],
            label='Arduino',
            color='red'
        )

        lines = [self.line_arduino]
        self.axes_arduino.legend(
            lines,
            [line.get_label() for line in lines]
        )

        self.canvas_arduino = FigureCanvasTkAgg(figure_arduino,
                                                master=frame_graph)

        self.canvas_arduino.draw()
        self.canvas_arduino.get_tk_widget() \
            .grid(row=1, column=0, sticky=N + S + E + W)



        figure_thermocouple = Figure(figsize=(5, 4), dpi=100)
        self.axes_thermocouple = figure_thermocouple.add_subplot(111)
        self.axes_thermocouple.set_xlabel('Time [s]')
        self.axes_thermocouple.set_ylabel('Temperature [°C]')
        self.axes_thermocouple.grid(1)
        self.axes_thermocouple.set_xlim([0, 1])
        self.axes_thermocouple.set_ylim([0, 100])  # Set the appropriate temperature range

        self.line_thermocouple, = self.axes_thermocouple.plot(
            [0], [0],
            label='Thermocouple',
            color='blue'
        )

        lines = [self.line_thermocouple]
        self.axes_thermocouple.legend(
            lines,
            [line.get_label() for line in lines]
        )

        self.canvas_thermocouple = FigureCanvasTkAgg(figure_thermocouple, master=frame_graph)

        self.canvas_thermocouple.draw()
        self.canvas_thermocouple.get_tk_widget() \
            .grid(row=1, column=1, sticky=N + S + E + W)  # Adjust the column to position the thermocouple graph


        # - - Controls for Plots  - -
        frame_controls = Frame(self)
        frame_controls.pack(side=BOTTOM, fill='x')

        frame_controls.columnconfigure(0, weight=1)
        frame_controls.columnconfigure(1, weight=1)

        frame_controls_graph = Frame(frame_controls)
        frame_controls_graph.grid(row=0, column=0)

        self.button_start = Button(frame_controls_graph, text='Start',
                                   width=10, command=self.start_plots)
        self.button_stop = Button(frame_controls_graph, text='Stop', width=10,
                                  command=self.stop_plots, state=DISABLED)
        button_clear = Button(frame_controls_graph, text='Clear', width=10,
                              command=self.clear_plots)
        self.button_save = Button(frame_controls_graph, text='Save', width=10,
                                  command=self.save_data, state=DISABLED)

        self.button_start.pack(side=LEFT)
        Label(frame_controls_graph, text=' ').pack(side=LEFT)
        self.button_stop.pack(side=LEFT)
        Label(frame_controls_graph, text=' ').pack(side=LEFT)
        button_clear.pack(side=LEFT)
        Label(frame_controls_graph, text=' ').pack(side=LEFT)
        self.button_save.pack(side=LEFT)

        # - - Most Recent Data - -
        frame_current_data = Frame(self)
        frame_current_data.pack(side=BOTTOM, fill='x')

        frame_current_data.columnconfigure(0, weight=1)
        frame_current_data.columnconfigure(1, weight=1)

        self.current_arduino = Label(
            frame_current_data,
            background='white',
            text='Pressure - [torr] @ - [s]'
        )

        self.current_arduino.grid(row=0, column=0, sticky=E + W)

    
    def start_plots(self):
        print('- - Start Plotting - -')

        if arduino is not None and arduino.is_connected():
            arduino.record(start_time=time())

        if vfd is not None and vfd.is_connected():
            vfd.record(start_time=time())
            vfd.start_vfd()

        self.button_start['state'] = DISABLED
        self.button_stop['state'] = NORMAL

    def stop_plots(self):
        print('- - Stop Plotting - -')

        if arduino is not None and arduino.is_connected():
            arduino.pause()
            
        if vfd is not None and vfd.is_connected():
            vfd.stop()

        self.button_stop['state'] = DISABLED
        self.button_save['state'] = NORMAL

    def clear_plots(self):
        print('- - Clear Plots - -')

        data_arduino.clear()
        thermocouple_data.clear()

        if self.button_stop['state'] == DISABLED:
            self.button_start['state'] = NORMAL
            self.button_stop['state'] = DISABLED
            self.button_save['state'] = DISABLED

    def save_data(self):
        print('- - Save Data - -')

        save_data()

        print('- - Save Complete - -')


window = Tk()
window.title('Lathe Control System')
window.geometry('1200x675')

window.columnconfigure(0, weight=1)
window.columnconfigure(1, weight=1)

window.rowconfigure(0, weight=1)
window.rowconfigure(1, weight=99)


frame_graph = GraphPanel(window)
frame_graph.grid(row=1, column=0, columnspan=2, sticky=N + S + E + W)

# Create an instance of VFD_Controls in your main GUI setup
# frame_vfd_controls = VFD_Controls(window)



# frame_vfd_controls = VFD_Controls(window)

frame_vfd_controls = VFD_Controls(window)
frame_comms = CommsPanel(window, graph_panel=frame_graph, frame_vfd_controls=frame_vfd_controls)
frame_vfd_controls.grid(row=0, column=1, sticky=N + S + E + W)
# frame_comms = CommsPanel(window, graph_panel=frame_graph)
frame_comms.grid(row=0, column=0, sticky=N + S + E + W)


def update_gui():
    np_arduino = np.asarray(data_arduino) if len(data_arduino) else np.zeros((1, 2))
    np_thermocouple = np.asarray(thermocouple_data) if len(thermocouple_data) else np.zeros((1, 2))

    # Update Arduino
    frame_graph.line_arduino.set_xdata(np_arduino[:, 0])
    frame_graph.line_arduino.set_ydata(np_arduino[:, 1])

    # Update Thermocouple
    frame_graph.line_thermocouple.set_xdata(np_thermocouple[:, 0])
    frame_graph.line_thermocouple.set_ydata(np_thermocouple[:, 1])

    # Adjust the x-axis limits for both plots
    min_x = min(np_arduino[:, 0])
    max_x = max(np_arduino[:, 0])
    max_x = max_x if not min_x == max_x else min_x + 1

    frame_graph.axes_arduino.set_xlim([min_x, max_x])
    frame_graph.axes_thermocouple.set_xlim([min_x, max_x])

    # Adjust the y-axis limits for both plots
    frame_graph.axes_arduino.set_ylim([
        min(np_arduino[:, 1]) - 1,
        max(np_arduino[:, 1]) + 1
    ])

    frame_graph.axes_thermocouple.set_ylim([
        min(np_thermocouple[:, 1]) - 1,
        max(np_thermocouple[:, 1]) + 1
    ])

    # Redraw Plots
    frame_graph.canvas_arduino.draw()
    frame_graph.canvas_thermocouple.draw()

    # Update Current Data Text
    frame_graph.current_arduino.config(
        text=f'Pressure {np_arduino[-1, 1]} [torr] @ {np_arduino[-1, 0]} [s]'
    )

    # Reschedule Update
    window.after(gui_update_rate, update_gui)

# After the GUI is created, add the following line to enable blit
frame_graph.canvas_arduino.get_tk_widget().after(100, lambda: frame_graph.canvas_arduino.draw_idle())
frame_graph.canvas_thermocouple.get_tk_widget().after(100, lambda: frame_graph.canvas_thermocouple.draw_idle())


# Start the GUI update loop
window.after(gui_update_rate, update_gui)
window.mainloop()

# No need to handle window close event after window.mainloop()


# def on_window_close():
#     if arduino and arduino.is_connected():
#         arduino.stop()
#         arduino.disconnect()
#         sleep(1)
#     window.destroy()

# window.protocol('WM_DELETE_WINDOW', on_window_close)
# window.after(gui_update_rate, update_gui)
# window.mainloop()  # Remove this line as well

# # Start the GUI update loop
# window.after(gui_update_rate, update_gui)
# window.mainloop()






# def on_window_close():
    
#     if arduino and arduino.is_connected():
#         arduino.stop()
#         arduino.disconnect()
#         sleep(1)

#     window.destroy()


# window.protocol('WM_DELETE_WINDOW', on_window_close)
# window.after(gui_update_rate, update_gui)
# window.mainloop()