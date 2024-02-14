import minimalmodbus
import time
from threading import Thread
from serial import Serial
from serial.serialutil import SerialException

class ModbusThread(Thread):
    def __init__(self, port, slave_address, write_value, data_var=None, sample_rate=0.1):
        super().__init__()
        self.port = port
        self.slave_address = slave_address
        self.write_value = write_value
        self.instrument = None
        self.ping_register_address = 0x7003
        self.read_register_address = 0x7000
        self.write_register_address = 0x1000
        self.expected_value = 0x0000
        self.sample_rate = sample_rate
        self._running = False
        self._recording = False
        self.data_var = data_var if data_var is not None else []

    def connect(self, timeout=1, **kwargs):
        try:
            self.instrument = minimalmodbus.Instrument(self.port, self.slave_address)
            self.instrument.serial.timeout = timeout
            print(f"Connected to {self.port} with slave address {self.slave_address}")
            return True
        except SerialException as e:
            print(f"Serial connection error on {self.port}: {e}")
        except Exception as e:
            print(f"Unexpected error connecting to {self.port}: {e}")
        return False

    def disconnect(self):
        if self.instrument:
            self.instrument.serial.close()
            print(f"Disconnected from {self.port}")

    def ping(self):
        try:
            actual_value = self.instrument.read_register(self.ping_register_address, functioncode=3)
            return actual_value == self.expected_value
        except Exception as e:
            print(f"Ping error: {e}")
            return False
    def is_connected(self):
        try:
            # Attempt to read a register to check if the connection is open
            self.instrument.read_register(self.ping_register_address, functioncode=3)
            return True
        except Exception as e:
            return False
    def read_register(self, register_address):
        try:
            return self.instrument.read_register(register_address, functioncode=3)
        except Exception as e:
            print(f"Error reading register {hex(register_address)}: {e}")
            return None

    def write_register(self, register_address, value):
        try:
            self.instrument.write_register(register_address, value, functioncode=6)
        except minimalmodbus.ModbusException as e:
            print(f"Modbus error writing to register {hex(register_address)}: {e}")
        except SerialException as e:
            print(f"Serial error writing to register {hex(register_address)}: {e}")
        except Exception as e:
            print(f"Unexpected error writing to register {hex(register_address)}: {e}")

    def run(self):
        self._running = True
        self.connect()
        while self._running:
            if self._recording:
                elapsed_time = time.time() - self.start_time
                data_point = self.read_register(self.read_register_address)
                if data_point is not None:
                    self.data_var.append([elapsed_time, data_point])
            time.sleep(self.sample_rate)

    def stop(self):
        self._running = False
        self.disconnect()

    def record(self, start_time=time.time()):
        self._recording = True
        self.start_time = start_time

    def pause(self):
        self._recording = False



# import minimalmodbus
# import time
# from threading import Thread
# from time import sleep, time
# from serial import Serial
# from serial.serialutil import SerialException



# class ModbusThread(Thread):
#     def __init__(self, port, slave_address, write_value, data_var: list = list(), sample_rate: float = 0.1):
#         super().__init__()  # Corrected the super() call
#         self.port = port
#         self.slave_address = slave_address
#         self.write_value = write_value
       

#         self.port = port
#         self.slave_address = slave_address
#         self.write_value = write_value
#         self.instrument = None
#         self.ping_register_address = 0x7003
#         self.read_register_address = 0x7000
#         self.write_register_address = 0x1000
#         self.expected_value = 0x0000
#         self.sample_rate = sample_rate
#         self._running = False
#         self._recording = False

#         # Use the provided data_var or create an empty list
#         self.data_var = data_var

    

#     def connect(self, timeout=1, **kwargs):
#         try:
#             self.instrument = minimalmodbus.Instrument(self.port, self.slave_address)
#             print(f"Connected to {self.port} with slave address {self.slave_address}")
#         except Exception as e:
#             print(f"Error connecting to {self.port}: {e}")


#     def disconnect(self):
#         if self.instrument:
#             self.instrument.serial.close()
#             print(f"Disconnected from {self.port}")
#         else:
#             print("Not connected.")

#     def ping(self):
#         try:
#             actual_value = self.instrument.read_register(self.ping_register_address, functioncode=3)
#             if actual_value == self.expected_value:
#                 print(f"Ping successful. Value read: {actual_value}")
#                 return True
#             else:
#                 print(f"Ping failed. Unexpected value read: {actual_value}")
#                 return False
#         except Exception as e:
#             print(f"Error during ping: {e}")
#             return False
    
#     def is_connected(self):
#         try:
#             # Attempt to read a register to check if the connection is open
#             self.instrument.read_register(self.ping_register_address, functioncode=3)
#             return True
#         except Exception as e:
#             return False

#     def read_register(self, register_address):
#         try:
#             value = self.instrument.read_register(register_address, functioncode=3)
#             return value
#         except Exception as e:
#             print(f"Error reading register {hex(register_address)}: {e}")
#             return None

#     def set_write_value(self, write_value):
#             self.write_register(self.write_register_address, write_value)

#     # def write_register(self, register_address, value):
#     #     try:
#     #         self.instrument.write_register(register_address, value, functioncode=6)
#     #     except Exception as e:
#     #         print(f"Error writing to register {hex(register_address)}: {e}")
#     # Modify the write_register method in ModbusThread class
#     def write_register(self, register_address, value, timeout=2):
#         try:
#             self.instrument.write_register(register_address, value, functioncode=6)
#         except minimalmodbus.ModbusException as e:
#             print(f"Error writing to register {hex(register_address)}: {e}")
#         except SerialException as se:
#             print(f"Serial communication error: {se}")
#         except Exception as e:
#             print(f"Unexpected error writing to register {hex(register_address)}: {e}")
#         finally:
#             self.stop()


  

#     def perform_modbus_operations(self):
#         # Read and print data from a Modbus register
#         read_value = self.read_register(self.read_register_address)
#         print(f"Read from register {hex(self.read_register_address)}: {read_value}")

#         # Write data to a Modbus register
#         self.write_register(self.write_register_address)
#         print(f"Wrote {hex(self.write_value)} to register {hex(self.write_register_address)}")

#         # Allow time for the changes to take effect (optional)
#         time.sleep(1)

#         # Read and print data again to confirm the write operation
#         read_value_after_write = self.read_register(self.read_register_address)
#         print(f"Read from register {hex(self.read_register_address)} after write: {read_value_after_write}")

     
#     def run(self):
#         self._running = True
#         self._recording = False
#         self.connect()

#         while True:
#             # Check if the thread is still running
#             if not self._running:
#                 break

#             # Check if currently recording data
#             if self._recording:
#                 elapsed_time = time() - self.start_time

#                 # Read data from Modbus register
#                 data_point = self.read_register(self.read_register_address)

#                 # Append the timestamp and data to the data_var list
#                 self.data_var.append([elapsed_time, data_point])

#             # Delay until the next sample to be taken
#             sleep(self.sample_rate)
   


    

#     # def stop(self) -> None: 
#     #     """Close the data collection Thread and write to register 0x2000."""
#     #     self._running = False
        
#     #     # Additional code to write to register 0x2000 with value 0x0006
#     #     try:
#     #         self.write_register(0x2000, 0x0006)
#     #         print(f"Write to register 0x2000 successful.")
#     #     except Exception as e:
#     #         print(f"Error writing to register 0x2000: {e}")
#     # Modify the stop method in ModbusThread class
#     def stop(self) -> None: 
#         """Close the data collection Thread and write to register 0x2000."""
#         self._running = False
#         self._recording = False

#         # Additional code to write to register 0x2000 with value 0x0006
#         try:
#             self.write_register(0x2000, 0x0006)
#             print(f"Write to register 0x2000 successful.")
#         except minimalmodbus.ModbusException as e:
#             print(f"Error writing to register 0x2000: {e}")
#         except SerialException as se:
#             print(f"Serial communication error: {se}")
#         except Exception as e:
#             print(f"Unexpected error writing to register 0x2000: {e}")


    
#     def record(self, start_time=time()):
#         """Start data collection while Thread is running."""
#         self._recording = True
#         self.start_time = start_time
    

#     def start_vfd(self) -> None:
#         """Write to register 0x2000 with value 0x0001."""
#         try:
#             self.write_register(0x2000, 0x0001)
#             print(f"Write to register 0x2000 successful.")
#         except Exception as e:
#             print(f"Error writing to register 0x2000: {e}")
#     def pause(self):
#         """Pause data collection while Thread is running."""
#         self._recording = False
#         self.start_time = 0

if __name__ == '__main__':
    import serial.tools.list_ports

    ports = [port.device for port in serial.tools.list_ports.comports()]
    if not ports:
        print("No serial ports found. Exiting.")
        exit()

    print("Available serial ports:")
    for idx, port in enumerate(ports):
        print(f"{idx}: {port}")

    sel = int(input("Select a port by entering the corresponding number: "))
    if 0 <= sel < len(ports):
        selected_port = ports[sel]
        print(f"Selected port: {selected_port}")
        
        vfd = ModbusThread(selected_port, slave_address=1, write_value=0x0FA7)
        
        if vfd.connect() and vfd.ping():
            print("Successfully connected to the VFD and pinged successfully.")
            
            # Example usage to demonstrate functionality
            vfd.start()
            vfd.record()
            print("Recording data for 10 seconds...")
            time.sleep(10)  # Record for a short duration
            vfd.pause()
            
            vfd.stop()
            print("Stopped recording and disconnected from the VFD.")
        else:
            print("Failed to connect or ping the VFD.")
    else:
        print("Invalid selection. Exiting.")

# if __name__ == '__main__':
#     import serial.tools.list_ports

#     ports = [port.device for port in serial.tools.list_ports.comports()]

#     for idx, port in enumerate(ports):
#         print(f'{idx}: {port}')

#     # vfd = None
#     recorded_values = list()

#     while True:
#         sel = int(input('Select a port (enter the corresponding number): '))
#         recorded_values = list()
#         # Create an instance of ModbusThread with the selected port
#         vfd = ModbusThread(ports[sel], slave_address=1, write_value=0x0FA7, data_var=recorded_values)
        
#         vfd.connect()
#         ping_successful = vfd.ping()

#         if not ping_successful:
#             continue

#         print(f'Connected on {ports[sel]}')
#         break

#     # Command Testing
#     print('Frequency Test')
    
#     # Specify the register address for the frequency test
#     register_address = vfd.read_register_address
#     for x in range(5):
#         frequency = vfd.read_register(register_address)
#         print(f"Frequency: {frequency}")
#         time.sleep(0.25)

#     vfd.start()
#     vfd.record()

#     swap_count = 20
#     itr = 1
#     sampling = False

#     try:
#         while True:
#             time.sleep(0.5)

#             if len(recorded_values) == 0:
#                 print('No data gathered')
#                 continue

#             print(f'Count #{len(recorded_values):5}: {recorded_values[-1]}')

#             if itr % swap_count == 0:
#                 if sampling:
#                     vfd.record()
#                 else:
#                     vfd.pause()

#                 sampling = not sampling

#             itr = itr + 1

#     except KeyboardInterrupt:
#         pass
#     finally:
#         vfd.stop()





