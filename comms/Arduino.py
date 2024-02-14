from serial import Serial, SerialException
from time import sleep, time
from threading import Thread


class Arduino(Thread):


    def __init__(self, port: str, baudrate: int = 115200, data_var: list = list(),thermocouple_data: list = list(), sample_rate: float = 0.1):
        super().__init__()

        self.port = port
        self.data_var = data_var
        self.thermocouple_data = thermocouple_data  # Add a new list for thermocouple data
        self.sample_rate = sample_rate
        self.baudrate = baudrate
        self.client = None

        self._running = False
        self._recording = False

    def connect(self, timeout=1, **kwargs):
        if self.client and self.client.is_open:
            print('Arduino Error: Serial connection already open.')
            return False

        try:
            self.client = Serial(self.port, timeout=timeout, baudrate=self.baudrate, **kwargs)
            sleep(3)
        except SerialException:
            print('Arduino Error: Serial connection failed to open.')
            return False

        return self.client.is_open

    def disconnect(self) -> bool:
        self.stop()

        if not self.client.is_open:
            return False

        self.client.close()
        return not self.client.is_open

    def send(self, data: str) -> str:
        """Send data to the Arduino and return the response."""
        if not self.client.is_open:
            print('Arduino Error: Serial connection not open.')
            return ''

        try:
            self.client.write(data.encode())
            response = self.client.readline().decode().strip()
            return response
        except Exception as e:
            print(f'Arduino Error: {e}')
            return ''

    def ping(self, num_attempts=5) -> bool:
        for _ in range(num_attempts):
            response = self.send('?')
            print(f'Received response from Arduino: {response}')

            # Check if the response contains the expected '?'
            if '?' in response:
                print(f'Received expected response from Arduino: {response}')
                return True
            else:
                print(f'Unexpected response from Arduino: {response}')

        # If none of the attempts received the expected response
        print('Arduino ping failed after multiple attempts')
        return False


  

   
    def read_analog_input(self) -> float:
        self.client.write(b'READ\n')
        data = self.client.readline().decode().strip()

        try:
            # Additional check before conversion
            if data and data.replace('.', '', 1).isdigit():
                analog_value = float(data)
                return analog_value
            else:
                print(f'Error: Invalid analog input data. Received: {data}')
                return 0.0
        except ValueError:
            print(f'Error: Failed to convert data to a float. Received: {data}')
            return 0.0
    
    def read_thermocouple_temperature(self) -> float:
        self.client.write(b'READ_THERMOCOUPLE\n')
        data = self.client.readline().decode().strip()

        try:
            # Attempt to convert the data to a float
            thermocouple_temperature = float(data)
            return thermocouple_temperature
        except ValueError:
            # Handle the case when conversion to float fails
            print(f'Error: Invalid thermocouple temperature data. Received: {data}')
            return 0.0  # Return a default value or handle it as needed


    def run(self):
        self._running = True
        self._recording = False

        while True:
            if not self._running:
                break

            if self._recording:
                elapsed_time = time() - self.start_time

                # Read the analog input value
                analog_value = self.read_analog_input()
                
                # Read the thermocouple temperature
                thermocouple_temperature = self.read_thermocouple_temperature()

                # Append the thermocouple data to the thermocouple_data list
                self.thermocouple_data.append([elapsed_time, thermocouple_temperature])

                # Append the analog input and thermocouple data to the data_var list
                self.data_var.append([elapsed_time, analog_value, thermocouple_temperature])

                # Sleep to avoid potential buffer overflow
                #sleep(self.sample_rate)

            sleep(self.sample_rate)

   
   

    def read_data_from_arduino(self):
        data = self.client.readline().decode().strip().split(': ')
        label = data[0]
        value = float(data[1])
        return label, value

    def stop(self):
        """Close the data collection Thread."""
        self._running = False

    def record(self, start_time=time()):
        """Start data collection while Thread is running."""
        self._recording = True
        self.start_time = start_time

    def pause(self):
        """Pause data collection while Thread is running."""
        self._recording = False
        self.start_time = 0

    def is_connected(self):
        return self.client.is_open

if __name__ == '__main__':
    import serial.tools.list_ports

    ports = [port.device for port in serial.tools.list_ports.comports()]

    for idx, port in enumerate(ports):
        print(f'{idx}: {port}')

    while True:
        sel = int(input('Port: '))

        data_arduino = list()
        arduino_reader = Arduino(ports[sel], data_var=data_arduino)

        result = arduino_reader.connect(timeout=5)

        if not result:
            continue

        print(f'Connected on {ports[sel]}')
        break

    arduino_reader.start()
    arduino_reader.record()

    try:
        while True:
            sleep(0.5)

            if len(data_arduino) == 0:
                print('No data gathered')
                continue

            print(f'Count #{len(data_arduino):5}: {data_arduino[-1]}')

    except KeyboardInterrupt:
        pass
    finally:
        arduino_reader.stop()



# # Arduino.py
# from serial import Serial, SerialException
# from time import sleep, time
# from threading import Thread


# class Arduino(Thread):
#     def __init__(self, port: str, baudrate: int = 115200, data_var: list = list(), pressure_data: list = list(), thermocouple_data: list = list(), sample_rate: float = 0.1):
#         super().__init__()

#         self.port = port
#         self.data_var = data_var
#         self.pressure_data = pressure_data  # Add a new list for pressure data
#         self.thermocouple_data = thermocouple_data  # Add a new list for thermocouple data
#         self.sample_rate = sample_rate
#         self.baudrate = baudrate
#         self.client = None

#         self._running = False
#         self._recording = False

#     def connect(self, timeout=1, **kwargs):
#         if self.client and self.client.is_open:
#             print('Arduino Error: Serial connection already open.')
#             return False

#         try:
#             self.client = Serial(self.port, timeout=timeout, baudrate=self.baudrate, **kwargs)
#             sleep(3)
#         except SerialException:
#             print('Arduino Error: Serial connection failed to open.')
#             return False

#         return self.client.is_open

#     def disconnect(self) -> bool:
#         self.stop()

#         if not self.client.is_open:
#             return False

#         self.client.close()
#         return not self.client.is_open

#     def send(self, data: str) -> str:
#         """Send data to the Arduino and return the response."""
#         if not self.client.is_open:
#             print('Arduino Error: Serial connection not open.')
#             return ''

#         try:
#             self.client.write(data.encode())
#             response = self.client.readline().decode().strip()
#             return response
#         except Exception as e:
#             print(f'Arduino Error: {e}')
#             return ''

#     def ping(self, num_attempts=5) -> bool:
#         for _ in range(num_attempts):
#             response = self.send('?')
#             print(f'Received response from Arduino: {response}')

#             # Check if the response contains the expected '?'
#             if '?' in response:
#                 print(f'Received expected response from Arduino: {response}')
#                 return True
#             else:
#                 print(f'Unexpected response from Arduino: {response}')

#         # If none of the attempts received the expected response
#         print('Arduino ping failed after multiple attempts')
#         return False

#     def read_pressure(self) -> float:
#         self.client.write(b'READ_PRESSURE\n')
#         data = self.client.readline().decode().strip()

#         try:
#             # Attempt to convert the data to a float
#             pressure_value = float(data)
#             return pressure_value
#         except ValueError:
#             # Handle the case when conversion to float fails
#             print(f'Error: Invalid pressure data. Received: {data}')
#             return 0.0  # Return a default value or handle it as needed

#     def read_thermocouple_temperature(self) -> float:
#         self.client.write(b'READ_THERMOCOUPLE\n')
#         data = self.client.readline().decode().strip()

#         try:
#             # Attempt to convert the data to a float
#             thermocouple_temperature = float(data)
#             return thermocouple_temperature
#         except ValueError:
#             # Handle the case when conversion to float fails
#             print(f'Error: Invalid thermocouple temperature data. Received: {data}')
#             return 0.0  # Return a default value or handle it as needed

#     def run(self):
#         self._running = True
#         self._recording = False

#         while True:
#             if not self._running:
#                 break

#             if self._recording:
#                 elapsed_time = time() - self.start_time

#                 # Read the pressure value
#                 pressure_value = self.read_pressure()

#                 # Read the thermocouple temperature
#                 thermocouple_temperature = self.read_thermocouple_temperature()

#                 # Append the pressure data to the pressure_data list
#                 self.pressure_data.append([elapsed_time, pressure_value])

#                 # Append the thermocouple data to the thermocouple_data list
#                 self.thermocouple_data.append([elapsed_time, thermocouple_temperature])

#                 # Sleep to avoid potential buffer overflow
#                 # sleep(self.sample_rate)

#             sleep(self.sample_rate)

#     def read_data_from_arduino(self):
#         data = self.client.readline().decode().strip().split(': ')
#         label = data[0]
#         value = float(data[1])
#         return label, value

#     def stop(self):
#         """Close the data collection Thread."""
#         self._running = False

#     def record(self, start_time=time()):
#         """Start data collection while Thread is running."""
#         self._recording = True
#         self.start_time = start_time

#     def pause(self):
#         """Pause data collection while Thread is running."""
#         self._recording = False
#         self.start_time = 0

#     def is_connected(self):
#         return self.client.is_open
# if __name__ == '__main__':
#     import serial.tools.list_ports

#     ports = [port.device for port in serial.tools.list_ports.comports()]

#     for idx, port in enumerate(ports):
#         print(f'{idx}: {port}')

#     while True:
#         sel = int(input('Port: '))

#         data_arduino = list()
#         arduino_reader = Arduino(ports[sel], data_var=data_arduino)

#         result = arduino_reader.connect(timeout=5)

#         if not result:
#             continue

#         print(f'Connected on {ports[sel]}')
#         break

#     arduino_reader.start()
#     arduino_reader.record()

#     try:
#         while True:
#             sleep(0.5)

#             if len(data_arduino) == 0:
#                 print('No data gathered')
#                 continue

#             print(f'Count #{len(data_arduino):5}: {data_arduino[-1]}')

#     except KeyboardInterrupt:
#         pass
#     finally:
#         arduino_reader.stop()


