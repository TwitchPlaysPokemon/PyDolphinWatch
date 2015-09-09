'''
Implementation of the own DolphinWatch Protocol
(see https://github.com/ProjectRevoTPP/dolphin).

Is based on virtual coroutines using gevent.

@author: Felk
'''

from __future__ import print_function, division
from gevent import monkey; monkey.patch_socket()

import gevent, socket
from _ctypes import ArgumentError
from StringIO import StringIO

class DolphinWatch(object):
    def __init__(self, host="localhost", port=6000):
        '''
        Creating a new DolphinWatch instance,
        pointing to the DolphinWatch Server specified by host and port.
        The connection must be established explicitly with connect().
        
        host and port can be overwritten, followed by another connect() call to reconnect.
        '''
        self.host = host
        self.port = port
        self._connected = False
        self._sock = None
        self._cFunc = None
        self._dcFunc = None
        self._callbacks = {}
        self._buf = ""
        
    def isConnected(self):
        '''
        Returns whether the DolphinWatch instance is connected to the
        corresponding server defined by host and port.
        '''
        return self._connected
        
    def connect(self):
        '''
        Tries to establish a connection to the server.
        If it succeeds, the onConnect callback will be called.
        If it fails, the onDisconnect callback will be called.
        '''
        self.disconnect()
        self._connected = True
        try:
            self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._sock.connect((self.host, self.port))
            print("DolphinWatch connection to %s:%d established! Ready for work!" % (self.host, self.port))
            if self._cFunc: self._cFunc(self)
            gevent.spawn(self._recv)
        except socket.error:
            print("DolphinWatch connection to %s:%d failed." % (self.host, self.port))
            self.disconnect()
        
    def disconnect(self):
        '''
        Disconnects the socket from the server.
        The onDisconnect callback will be called.
        '''
        if not self._connected:
            return
        self._connected = False
        try:
            self._sock.close()
        except:
            pass
        if self._dcFunc:
            self._dcFunc(self)
            
    def onConnect(self, func):
        '''
        Sets the callback that will be called after a connection
        has been successfully established.
        The current DolphinWatch instance will be submitted as parameter.
        Is initially None, and can again be assigned to None.
        '''
        if not hasattr(func, '__call__'):
            raise ArgumentError("onDisconnect lambda must be callable.")
        self._cFunc = func
        
    def onDisconnect(self, func):
        '''
        Sets the callback that will be called after a connection attempt fails,
        an active connection gets closed or the connection gets lost.
        The current DolphinWatch instance will be submitted as parameter.
        Is initially None, and can again be assigned to None.
        '''
        if not hasattr(func, '__call__'):
            raise ArgumentError("onDisconnect lambda must be callable.")
        self._dcFunc = func
        
    def write8(self, addr, val):
        '''
        Sends a command to write 8 bytes of data to the given address.
        '''
        self._write(8, addr, val)
    
    def write16(self, addr, val):
        '''
        Sends a command to write 16 bytes of data to the given address.
        '''
        self._write(16, addr, val)
    
    def write32(self, addr, val):
        '''
        Sends a command to write 32 bytes of data to the given address.
        '''
        self._write(32, addr, val)
        
    def read(self, addr, callback):
        '''
        Sends a command to send back 32 bytes of data at the given address.
        The given callback function gets called with the returned value as parameter. 
        '''
        if addr%4 != 0:
            raise ArgumentError("Read address must be whole word; multiple of 4")
        self._reg_callback(addr, callback, False)
        self._cmd("MEMGET %d" % addr)
    
    def subscribe(self, addr, callback):
        '''
        Sends a command to send back 32 bytes of data at the given address,
        repeating each time the value changes.
        The given callback function gets called with the returned value as parameter.
        '''
        if addr%4 != 0:
            raise ArgumentError("Read address must be whole word; multiple of 4")
        self._reg_callback(addr, callback, True)
        self._cmd("SUBSCRIBE %d" % addr)
        
    def wiiButton(self, wiimoteIndex, buttonstates):
        '''
        Sends 16 bit of data representing some buttonstates of the Wiimote.
        see http://wiibrew.org/wiki/Wiimote#Buttons for more info
        '''
        self._cmd("BUTTONSTATES %d %d" % (wiimoteIndex, buttonstates))
        
    ################### private stuff ###################
    
    def _cmd(self, cmd):
        if not self._connected:
            raise socket.error("DolphinWatch is not _connected and therefore cannot perform actions!")
        self._sock.send(bytes(cmd + "\n"))
    
    def _reg_callback(self, addr, func, subscribe=False):
        self._callbacks[addr] = (func, subscribe)
        
    def _dereg_callback(self, addr):
        self._callbacks.pop(addr)
        
    def _process(self, line):
        parts = line.split(" ")
        if parts[0] == "MEM":
            addr = int(parts[1])
            val = int(parts[2])
            callback = self._callbacks.get(addr)
            if callback:
                if not callback[1]:
                    self._dereg_callback(addr)
                callback[0](val)
            else:
                print("No recipient for address 0x%x, value 0x%x" % (addr, val))
        else:
            print("Unknown DolphinMem Command: "+line)
    
    def _recv(self):
        while (self._connected):
            try:
                data = self._sock.recv(1024)
                if not data:
                    print("DolphinWatch connection closed")
                    self.disconnect()
                    return
                self._buf += data
            except socket.error:
                print("DolphinWatch connection lost")
                self.disconnect()
                return
            buf = StringIO(self._buf)
            for line in buf:
                if not line.endswith("\n"):
                    break;
                self._process(line.strip())
            self._buf = self._buf[buf.tell():]
    
    def _write(self, mode, addr, val):
        self._cmd("MEMSET %d %d %d" % (mode, addr, val))
        

