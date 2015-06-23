#
# WearNow - a GTK+/GNOME based  program
#
# Copyright (C) pyFirmata authors under BSD license
# Copyright (C) 2015       Benny Malengier
# Copyright (C) Alan Yorinks PyMata GPL v3 or later
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, 
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#

"""
Utilities to connect to a rfid reader board
"""

#-------------------------------------------------------------------------
#
# Standard python modules
#
#-------------------------------------------------------------------------
import os

#-------------------------------------------------------------------------
#
# WearNow modules
#
#-------------------------------------------------------------------------

def get_the_board(base_dir='/dev/', identifier='tty.usbserial',):
    """
    Helper function to get the one and only board connected to the computer
    running this.
    ``base_dir`` and ``identifier`` are overridable as well. It will raise an
    IOError if it can't find a board, on a serial, or if it finds more than
    one.
    """
    boards = []
    for device in os.listdir(base_dir):
        if device.startswith(identifier):
            boards.append(device)
    if len(boards) == 0:
        raise IOError("No boards found in {0} with identifier {1}".format(base_dir, identifier))
    elif len(boards) > 1:
        raise IOError("More than one board found!")
    return boards[0]



def to_two_bytes(integer):
    """
    Breaks an integer into two 7 bit bytes.
    """
    if integer > 32767:
        raise ValueError("Can't handle values bigger than 32767 (max for 2 bits)")
    return bytearray([integer % 128, integer >> 7])


def from_two_bytes(bytes):
    """
    Return an integer from two 7 bit bytes.
    """
    lsb, msb = bytes
    try:
        # Usually bytes have been converted to integers with ord already
        return msb << 7 | lsb
    except TypeError:
        # But add this for easy testing
        # One of them can be a string, or both
        try:
            lsb = ord(lsb)
        except TypeError:
            pass
        try:
            msb = ord(msb)
        except TypeError:
            pass
        return msb << 7 | lsb


def two_byte_iter_to_str(bytes):
    """
    Return a string made from a list of two byte chars.
    """
    bytes = list(bytes)
    chars = bytearray()
    while bytes:
        lsb = bytes.pop(0)
        try:
            msb = bytes.pop(0)
        except IndexError:
            msb = 0x00
        chars.append(from_two_bytes([lsb, msb]))
    return chars.decode()


def str_to_two_byte_iter(string):
    """
    Return a iter consisting of two byte chars from a string.
    """
    bstring = string.encode()
    bytes = bytearray()
    for char in bstring:
        bytes.append(char)
        bytes.append(0)
    return bytes


def break_to_bytes(value):
    """
    Breaks a value into values of less than 255 that form value when multiplied.
    (Or almost do so with primes)
    Returns a tuple
    """
    if value < 256:
        return (value,)
    c = 256
    least = (0, 255)
    for i in range(254):
        c -= 1
        rest = value % c
        if rest == 0 and value / c < 256:
            return (c, int(value / c))
        elif rest == 0 and value / c > 255:
            parts = list(break_to_bytes(value / c))
            parts.insert(0, c)
            return tuple(parts)
        else:
            if rest < least[1]:
                least = (c, rest)
    return (c, int(value / c))


import threading
import time
import sys

import serial


class ProcessSerial(threading.Thread):
    """
     This class manages the serial port for Arduino serial communications
    """

    # class variables
    arduino = serial.Serial()

    port_id = ""
    #baud_rate = 57600
    baud_rate = 9600
    timeout = 1    # None=wait, 0= non-blocking, x>0 = timeout in sec
    def __init__(self, port_id):
        self.port_id = port_id

        threading.Thread.__init__(self)
        
        self.daemon = True
        self.arduino = serial.Serial(self.port_id, self.baud_rate,
                                     timeout=int(self.timeout), writeTimeout=0)

        self.stop_event = threading.Event()
        self.lock = threading.Lock()

        # without this, running python 3.4 is extremely sluggish -- 
        # I need it without to have threading working correct ...
#        if sys.platform == 'linux':
#            # noinspection PyUnresolvedReferences
#            self.arduino.nonblocking()
        self.starttag = False
        self.lasttag = []
        self.currentread = []

    def stop(self):
        print ("stopping thread to watch board")
        self.stop_event.set()

    def is_stopped(self):
        return self.stop_event.is_set()

    def open(self, verbose):
        """
        open the serial port using the configuration data
        returns a reference to this instance
        """
        # open a serial port
        if verbose:
            print('\nOpening Arduino Serial port %s ' % self.port_id)

        try:

            # in case the port is already open, let's close it and then
            # reopen it
            self.arduino.close()
            time.sleep(1)
            self.arduino.open()
            time.sleep(1)
            return self.arduino

        except Exception:
            # opened failed - will report back to caller
            raise

    def close(self):
        """
            Close the serial port
            return: None
        """
        try:
            self.arduino.close()
        except OSError:
            pass

    def write(self, data):
        """
            write the data to the serial port
            return: None
        """
        if sys.version_info[0] < 3:
            self.arduino.write(data)
        else:
            self.arduino.write(bytes([ord(data)]))

    # noinspection PyExceptClausesOrder
    def run(self):
        """
        This method continually runs. 
        @return: Never Returns
        """
        while not self.is_stopped():
            # we can get an OSError: [Errno9] Bad file descriptor when shutting down
            # just ignore it
            try:
                self.processserialinput()
            except OSError:
                pass
            except IOError:
                self.stop()
        self.close()

    def processserialinput(self):        
        input_string = self.arduino.readline(512)  #max lines of 512 bytes
        try:
            input_string = input_string.decode('utf-8')
        except UnicodeDecodeError as msg:
            input_string = ""
            if self.starttag:
                #undo what we have read up to now
                self.starttag = False
                self.currentread = []
            print ('ERROR reading line from tag:', msg)
                
        input_string = input_string.strip('\r\n')
        #print ('read', input_string)
        if input_string.strip() == "Begin Tag":
            #print ("START ON TRUE")
            self.starttag = True
        if self.starttag:
            self.currentread.append( input_string)
            #print ('test', read)
            if self.currentread[-1] == 'End Tag':
                self.starttag = False
                self.lock.acquire()
                try:
                    self.lasttag = self.currentread
                    #print ('last tag read')
                    self.currentread = []
                finally:
                    self.lock.release()

    def get_read_tag(self, cleanafter=True):
        self.lock.acquire()
        try:
            tag = self.lasttag
            if cleanafter:
                self.lasttag = []
        finally:
            self.lock.release()
        return tag