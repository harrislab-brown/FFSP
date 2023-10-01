from threading import Thread
import serial
import serial.tools.list_ports
import struct
from queue import Queue
import copy
import time


class SerialMonitor:
    def __init__(self, serial_port=None, serial_baud=115200, num_data_bytes=2, num_channels=1):
        self.num_data_bytes = num_data_bytes  # how many bytes per data point
        self.num_channels = num_channels  # how many data points we receive at a time
        self.data = Queue()  # each element is a Python list of n channels at a given time step

        # define the serial protocol
        self.data_type = None  # TODO: error handling here
        if num_data_bytes == 2:
            self.data_type = 'h'
        elif num_data_bytes == 4:
            self.data_type = 'f'

        # store the state of the serial monitor
        self.running = True
        self.is_receiving = False
        self.thread = None

        # start the serial connection
        self.serial_connection = self.connect_serial_port(serial_port, serial_baud)

        # start the background threads that reads the serial port
        self.serial_input_background_init()

    @staticmethod
    def connect_serial_port(port, baud):
        if port is None:
            # if not predefined, allow the user to select from list
            port_list = [comport.device for comport in serial.tools.list_ports.comports()]
            print(port_list)
            port = port_list[int(input('Select from the list of connected devices:'))]
            # TODO: handle out of bounds exception

        try:
            serial_connection = serial.Serial(port, baud, timeout=4)
            print('Connected to ' + str(port) + ' at ' + str(baud) + ' BAUD.')
        except:  # TODO: proper, more specific exception handling
            print("Failed to connect with " + str(port) + ' at ' + str(baud) + ' BAUD.')
            exit()
        return serial_connection


    def serial_input_background_init(self):
        if self.thread is None:
            self.thread = Thread(target=self.background_thread)
            self.thread.start()
            while not self.is_receiving:
                time.sleep(0.1)  # wait until background thread starts receiving data


    def background_thread(self):
        time.sleep(1)
        self.serial_connection.reset_input_buffer()
        raw_data = bytearray(self.num_data_bytes * self.num_channels)
        value_array = [None] * self.num_channels

        while self.running:
            self.serial_connection.readinto(raw_data)
            self.is_receiving = True

            private_data = copy.deepcopy(raw_data[:])

            for i in range(self.num_channels):
                byte_data = private_data[(i * self.num_data_bytes):((i+1) * self.num_data_bytes)]
                value_array[i], = struct.unpack(self.data_type, byte_data)
            self.data.put(value_array[:])
    
    def serial_write(self, val):  # TODO: figure out write format
        val = int(round(val))
        val_str = bytes(str(val), 'utf-8')
        #print(val_str)
        self.serial_connection.write(val_str)

    def close(self):
        self.running = False
        self.thread.join()
        self.serial_connection.close()
        print('Serial disconnected')
