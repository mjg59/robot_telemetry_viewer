#!/usr/bin/env python3

import pyvesc
import serial
import struct
import sys
import time

from blessed import Terminal

output = None
from_file = None
ser = None
term = Terminal()
dumpmode = None

parameters = [[{'name': "temp_fet", 'warn': 80, 'critical': 100}],
              [{'name': "temp_fet", 'warn': 80, 'critical': 100}],
              [{'name': "temp_fet", 'warn': 80, 'critical': 100},
               {'name': "v_in", 'low_warn': 20, 'low_critical': 8}],
              [{'name': "temp_fet", 'warn': 80, 'critical': 100}]]

# Find the next record separator and return.
def resync():
    data = []
    while True:
        data.append(data_read())
        if data[-4:] == [b'-', b'-', b'-', b'-']:
            return

# Read data, either from a file or from a serial port. If reading from
# serial, write out to a local file as well.
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

# Accel data is 3 signed 16-bit integers, with one unit representing 0.1g
def parse_accel(timestamp, data):
    x = struct.unpack("<h", data[0:2])[0]
    y = struct.unpack("<h", data[2:4])[0]
    z = struct.unpack("<h", data[4:6])[0]
    if dumpmode == "accel":
        output.write("%d, %f, %f, %f\n" % (timestamp, x/10, y/10, z/10))

# Parsing of VESC data is done with pyvesc. Last 4 bytes of the data are the
# separator, so ignore them.
def parse_vesc(timestamp, vesc, data):
    msg, consumed = pyvesc.decode(data[0:-4])
    # If there's any corruption, the CRC check will fail and pyvesc will return
    # None. Return and let the main loop resynchronise.
    if msg == None:
        return
    if dumpmode != None:
        try:
            value = getattr(msg, dumpmode)
            if value != None:
                output.write("%d, %d, %s, %f\n" % (timestamp, vesc, dumpmode, value))
        except AttributeError:
            pass
        return
    print(term.home, end='')
    print (term.move_y(2), end='')
    for parm in parameters[vesc]:
        print (term.move_x(term.width * vesc // 4), end='')
        if parm['name'] != "":
            value = getattr(msg, parm['name'])
            if ('critical' in parm.keys() and value > parm['critical']) or \
               ('low_critical' in parm.keys() and value < parm['low_critical']):
                print(term.red_on_black, end='')
            elif ('warn' in parm.keys() and value > parm['warn']) or \
                 ('low_warn' in parm.keys() and value < parm['low_warn']):
                print(term.orange_on_black, end='')
            else:
                print(term.green_on_black, end='')
            print(parm['name'], value, end='')
        print(term.normal)

if len(sys.argv) > 1:
    arg = sys.argv[1]
    if arg == "list":
        ser = serial.Serial("/dev/ttyUSB0", 115200, timeout=1)
        ser.write(b'\r\r\rl\r')
        data = ser.read()
        while data:
            print(data.decode("ascii"), end='')
            data = ser.read()
        exit()
    elif arg == "dump":
        if len(sys.argv) != 4:
            print("Usage: dump filenum output")
            exit()
        filenum = sys.argv[2].encode("ascii")
        output = open(sys.argv[3], "wb")
        ser = serial.Serial("/dev/ttyUSB0", 115200, timeout=1)
        ser.write(b'\r\r\rp\r' + filenum + b'\r')
        data = ser.read()
        while data:
            output.write(data)
            data = ser.read()
        output.close()
        exit()
    elif arg == "accel":
        if len(sys.argv) != 4:
            print("Usage: accel data output")
            exit()
        dumpmode = "accel"
        from_file = open(sys.argv[2], "rb")
        output = open(sys.argv[3], "w")
    elif arg == "vesc":
        if len(sys.argv) != 5:
            print("Usage: vesc parameter data output")
            exit()
        dumpmode = sys.argv[2];
        from_file = open(sys.argv[3], "rb")
        output = open(sys.argv[4], "w")
    else:
        from_file = open(sys.argv[1], "rb")
else:
    ser = serial.Serial("/dev/ttyUSB0", 115200)
    output = open("telemetry.%d" % int(time.time()), "wb")

if dumpmode == None:
    print(term.on_black + term.home + term.clear, end='')
    print(term.white_on_black + "VESC 0" + term.normal, end='')
    print(term.move_x(int(term.width * 0.25)) + term.white_on_black + "VESC 1" + term.normal, end='')
    print(term.move_x(int(term.width * 0.5)) + term.white_on_black + "VESC 2" + term.normal, end='')
    print(term.move_x(int(term.width * 0.75)) + term.white_on_black + "VESC 3" + term.normal, end='')

while True:
    datatype = data_read()
    if datatype == b'\x41':
        # Accelerometer data
        timestamp = int.from_bytes(data_read(4), "little")
        data = data_read(10)
        if data[-4:] != b'----':
            resync()
            continue
        parse_accel(timestamp, data)
    elif datatype >= b'\x00' and datatype < b'\x0a':
        vesc = int.from_bytes(datatype, "little");
        timestamp = int.from_bytes(data_read(4), "little")
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
        parse_vesc(timestamp, vesc, msg)
    else:
        resync()

            
