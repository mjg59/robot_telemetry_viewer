#!/usr/bin/env python3

import pyvesc
import serial
import struct
import sys
import time

output = None
from_file = None
ser = None

def resync():
    data = []
    while True:
        data.append(data_read())
        if data[-4:] == [b'-', b'-', b'-', b'-']:
            return

def data_read(length=None):
    if from_file == None:
        if length == None:
            data = ser.read()
            output.write(data)
            return data
        data = ser.read(length)
        output.write(data)
        return data
    else:
        if length == None:
            return from_file.read(1)
        return from_file.read(length)

def parse_accel(data):
    x = struct.unpack("<h", data[0:2])
    y = struct.unpack("<h", data[2:4])
    z = struct.unpack("<h", data[4:6])
    print("Accel", x, y, z)

def parse_vesc(vesc, data):
    msg, consumed = pyvesc.decode(data[0:-4])
    print(msg.temp_fet)

if len(sys.argv) > 1:
    from_file = open(sys.argv[1], "rb")
else:
    output = open("telemetry.%d" % int(time.time()), "wb")
    ser = serial.Serial("/dev/ttyUSB0", 115200)

while True:
    datatype = data_read()
    if datatype == b'\x41':
        # Accelerometer data
        timestamp = data_read(4)        
        data = data_read(10)
        if data[-4:] != b'----':
            resync()
            continue
        parse_accel(data)
    elif datatype >= b'\x00' and datatype < b'\x0a':
        vesc = datatype;
        timestamp = data_read(4)
        packettype = data_read()
        if packettype != b'\x02':
            resync()
            continue
        length = ord(data_read())
        # 3 bytes of trailing message data, 4 bytes of trailer
        data = data_read(length + 7)
        if data[-4:] != b'----':
            resync()
            continue
        # Reconstruct the original message so pyvesc can parse it
        msg = b'\x02' + length.to_bytes(1, "little") + data
        parse_vesc(vesc, msg)
    else:
        resync()

            
