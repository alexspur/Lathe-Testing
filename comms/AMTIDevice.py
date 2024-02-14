from threading import Thread
import time

class AMTIDevice(Thread):
    def __init__(self, sdk_path, device_index=0, data_var=None, sample_rate=0.1):
        super().__init__()
        self.sdk_path = sdk_path
        self.device_index = device_index
        self.data_var = data_var if data_var is not None else []
        self.sample_rate = sample_rate
        self._running = False
        self._recording = False
        self.amti_lib = None
        self.start_time = 0

    def load_sdk(self):
        # Assuming the SDK is loaded here, pseudo-code
        try:
            import ctypes
            self.amti_lib = ctypes.cdll.LoadLibrary(self.sdk_path)
            return True
        except Exception as e:
            print(f"Error loading AMTI SDK: {e}")
            return False

    def connect(self):
        if not self.load_sdk():
            return False
        # Initialize device based on AMTI SDK documentation
        try:
            init_result = self.amti_lib.initialize_device(self.device_index)
            if init_result == 1:  # Assuming 1 signifies success
                print("Connected to AMTI device")
                return True
            else:
                print("Failed to initialize AMTI device")
                return False
        except Exception as e:
            print(f"Error initializing AMTI device: {e}")
            return False

    def disconnect(self):
        if self.amti_lib:
            # Close the device connection
            self.stop()
            try:
                self.amti_lib.close_device()
                print("Disconnected from AMTI device")
                return True
            except Exception as e:
                print(f"Error disconnecting AMTI device: {e}")
                return False
        else:
            print("AMTI device was not connected")
            return False

    def run(self):
        self._running = True
        while self._running:
            if self._recording:
                # Simulate data reading
                elapsed_time = time.time() - self.start_time
                data_point = self.read_data()
                if data_point is not None:
                    self.data_var.append([elapsed_time, data_point])
            time.sleep(self.sample_rate)

    def read_data(self):
        # Implement data reading from AMTI device
        # This is pseudo-code, replace with actual SDK call
        try:
            data = self.amti_lib.read_data()
            return data
        except Exception as e:
            print(f"Error reading data from AMTI device: {e}")
            return None

    def record(self, start_time=time.time()):
        self._recording = True
        self.start_time = start_time

    def stop(self):
        self._running = False
        self._recording = False

    def pause(self):
        self._recording = False

    def is_connected(self):
        # Implement check based on AMTI SDK
        # This is pseudo-code, replace with actual SDK call
        try:
            status = self.amti_lib.check_connection_status()
            return status == 1  # Assuming 1 signifies a live connection
        except Exception:
            return False
