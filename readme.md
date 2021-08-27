Telemetry visualisation tool
============================

This tool allows for real-time visualisation of telemetry data, along with
later data extraction.

Usage
=====

Live usage
----------

Run the tool with no arguments to read data from /dev/ttyUSB0 and display
it.  Parameters can be configured by editing the parameters list near the
top of the code. Each list entry corresponds to a single vesc. Each list
entry contains a further list of dicts. Each dict should contain a name,
indicating which vesc parameter should be extracted. See
https://github.com/LiamBindle/PyVESC/blob/master/pyvesc/VESC/messages/getters.py#L46
for the set of available values. By default the value will be displayed in
green. If it is greater than the value in "warn", or smaller than the value
in "low_warn", it will be orange. If it is greater than the value in
"critical", or smaller than the value in "low_critical", it will be red.

Data extraction
---------------

To list the files available on a remote device, use the "list" argument. To
dump a file from a remote device, use the "dump" argument and provide an
additional argument for the filename to be written to.

To extract data from a local file, use either the "accel" or "vesc"
commands. The "accel" command should be followed by the input filename and
an output filename. It will write a CSV to the output containing each
accelerometer packet, in the format:

timestamp,x,y,z

where timestamp is milliseconds since startup, x, y, and z are measurements
in G.

The "vesc" command should be followed by a parameter name, an input filename
and an output filename. It will write a CSV to the output containing the
relevant parameter from each VESC packet, in the format:

timestamp,vesc,parameter,value

If the parameter is "all", all data will be dumped.