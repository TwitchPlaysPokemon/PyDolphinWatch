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
from util import enum

DisconnectReason = enum(
    CONNECTION_CLOSED_BY_PEER = 1,
    CONNECTION_CLOSED_BY_HOST = 2,
    CONNECTION_LOST           = 3,
    CONNECTION_FAILED         = 4,
)

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
        self._leFunc = None
        self._callbacks = {}
        self._buf = ""
        self._sep = "\n"
        
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
            self._disconnect(DisconnectReason.CONNECTION_FAILED)
        
    def disconnect(self):
        '''
        Disconnects the socket from the server.
        The onDisconnect callback will be called with CONNECTION_CLOSED_BY_HOST
        '''
        self._disconnect(DisconnectReason.CONNECTION_CLOSED_BY_HOST)
        
    def _disconnect(self, reason):
        if not self._connected:
            return
        self._connected = False
        try:
            self._sock.close()
        except:
            pass
        if self._dcFunc:
            self._dcFunc(self, reason)
            
    def onConnect(self, func):
        '''
        Sets the callback that will be called after a connection
        has been successfully established.
        Callback is initially None, and can again be assigned to None.
        '''
        if not hasattr(func, '__call__'):
            raise ArgumentError("onDisconnect callback must be callable.")
        self._cFunc = func
        
    def onDisconnect(self, func):
        '''
        Sets the callback that will be called after a connection attempt fails,
        an active connection gets closed or the connection gets lost.
        A DisconnectReason enum will be the parameter.
        Callback is initially None, and can again be assigned to None.
        '''
        if not hasattr(func, '__call__'):
            raise ArgumentError("onDisconnect callback must be callable.")
        self._dcFunc = func
        
    def onLoadError(self, func):
        '''
        Sets the callback that will be called when a savestate loading error occured.
        The filename will be the parameter.
        Callback is initially None, and can again be assigned to None.
        '''
        if not hasattr(func, '__call__'):
            raise ArgumentError("onError callback must be callable.")
        self._leFunc = func
        
    def startBatch(self):
        '''
        Call this function to send following commands in a batch.
        All following commands are guaranteed to be executed at once in Dolphin.
        Is done by buffering and not executing anything until endBatch() is called.
        '''
        self._sep = ";"
        
    def endBatch(self):
        '''
        Ends the batch started with startBatch().
        All buffered commands gets executed now and no more buffering is done.
        '''
        self._sep = "\n"
        self._cmd("")
        
    def volume(self, v):
        self._cmd("VOLUME %d" % v)

    def write(self, mode, addr, val):
        '''
        Sends a command to write <mode> bytes of data to the given address.
        <mode> must be 8, 16 or 32.
        '''
        self._cmd("WRITE %d %d %d" % (mode, addr, val))
        
    def read(self, mode, addr, callback):
        '''
        Sends a command to send back <mode> bytes of data at the given address.
        The given callback function gets called with the returned value as parameter.
        <mode> must be 8, 16 or 32.
        '''
        self._reg_callback(addr, callback, False)
        self._cmd("READ %d %d" % (mode, addr))
        
    def _subscribe(self, mode, addr, callback):
        '''
        Sends a command to send back <mode> bytes of data at the given address,
        repeating each time the value changes.
        The given callback function gets called with the returned value as parameter.
        <mode> must be 8, 16 or 32.
        '''
        self._reg_callback(addr, callback, True)
        self._cmd("SUBSCRIBE %d %d" % (mode, addr))
        
    def _subscribeMulti(self, size, addr, callback):
        '''
        Sends a command to send back <size> bytes of data starting at the given address,
        repeating each time the value changes. Useful for strings and arrays.
        The given callback function gets called with the returned values in a list as parameter.
        '''
        self._reg_callback(addr, callback, True)
        self._cmd("SUBSCRIBE_MULTI %d %d" % (size, addr))
        
    def write8(self, addr, val):
        '''
        Sends a command to write 8 bytes of data to the given address.
        '''
        self.write(8, addr, val)
    
    def write16(self, addr, val):
        '''
        Sends a command to write 16 bytes of data to the given address.
        '''
        self.write(16, addr, val)
    
    def write32(self, addr, val):
        '''
        Sends a command to write 32 bytes of data to the given address.
        '''
        self.write(32, addr, val)
        
    def read8(self, addr, callback):
        '''
        Sends a command to send back 8 bytes of data at the given address.
        The given callback function gets called with the returned value as parameter. 
        '''
        self.read(8, addr, callback)
        
    def read16(self, addr, callback):
        '''
        Sends a command to send back 16 bytes of data at the given address.
        The given callback function gets called with the returned value as parameter. 
        '''
        self.read(16, addr, callback)
        
    def read32(self, addr, callback):
        '''
        Sends a command to send back 32 bytes of data at the given address.
        The given callback function gets called with the returned value as parameter. 
        '''
        if addr%4 != 0:
            raise ArgumentError("Read32 address must be whole word; multiple of 4")
        self.read(32, addr, callback)
    
    def subscribe8(self, addr, callback):
        '''
        Sends a command to send back 8 bytes of data at the given address,
        repeating each time the value changes.
        The given callback function gets called with the returned value as parameter.
        '''
        self._subscribe(8, addr, callback)
        
    def subscribe16(self, addr, callback):
        '''
        Sends a command to send back 16 bytes of data at the given address,
        repeating each time the value changes.
        The given callback function gets called with the returned value as parameter.
        '''
        self._subscribe(16, addr, callback)
        
    def subscribe32(self, addr, callback):
        '''
        Sends a command to send back 32 bytes of data at the given address,
        repeating each time the value changes.
        The given callback function gets called with the returned value as parameter.
        '''
        if addr%4 != 0:
            raise ArgumentError("Read address must be whole word; multiple of 4")
        self._subscribe(32, addr, callback)
        
    def subscribeMulti(self, size, addr, callback):
        '''
        Sends a command to send back <size> bytes of data starting at the given address,
        repeating each time any value changes. Useful for strings or arrays.
        The given callback function gets called with the returned values in a list as parameter.
        '''
        self._subscribeMulti(size, addr, callback)
        
    def wiiButton(self, wiimoteIndex, buttonstates):
        '''
        Sends 16 bit of data representing some buttonstates of the Wiimote.
        see http://wiibrew.org/wiki/Wiimote#Buttons for more info
        '''
        self._cmd("BUTTONSTATES %d %d" % (wiimoteIndex, buttonstates))
        
    def pause(self):
        '''
        Tells Dolphin to pause the current emulation.
        Resume with resume()
        '''
        self._cmd("PAUSE")
        
    def resume(self):
        '''
        Tells Dolphin to resume the current emulation.
        '''
        self._cmd("RESUME")
        
    def save(self, filename):
        '''
        Tells Dolphin to make a savestate and save it to <filename>.
        '''
        if ":?\"<> | " in filename:
            raise ArgumentError("filename must not contain any of the following: :?\"<> | ")
        self._cmd("SAVE %s" % filename)
        
    def load(self, filename):
        '''
        Tells Dolphin to load the savestate located at <filename>.
        '''
        if ":?\"<> | " in filename:
            raise ArgumentError("filename must not contain any of the following: :?\"<> | ")
        self._cmd("LOAD %s" % filename)
        
    ################### private stuff ###################
    
    def _cmd(self, cmd):
        if not self._connected:
            raise socket.error("DolphinWatch is not _connected and therefore cannot perform actions!")
        self._sock.send(bytes(cmd + self._sep))
    
    def _reg_callback(self, addr, func, _subscribe=False):
        self._callbacks[addr] = (func, _subscribe)
        
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
        elif parts[0] == "MEM_MULTI":
            addr = int(parts[1])
            data = [int(v) for v in parts[2:]]
            callback = self._callbacks.get(addr)
            if callback:
                if not callback[1]:
                    self._dereg_callback(addr)
                callback[0](data)
            else:
                print("No recipient for address 0x%x, data %s" % (addr, data))
        elif parts[0] == "FAILLOAD":
            filename = " ".join(parts[1:])
            if self._leFunc:
                self._leFunc(filename)
        else:
            print("Unknown DolphinWatch Command: "+line)
    
    def _recv(self):
        while self._connected:
            try:
                data = self._sock.recv(1024)
                if not data:
                    print("DolphinWatch connection closed")
                    self._disconnect(DisconnectReason.CONNECTION_CLOSED_BY_PEER)
                    return
                self._buf += data
            except socket.error:
                print("DolphinWatch connection lost")
                self._disconnect(DisconnectReason.CONNECTION_LOST)
                return
            buf = StringIO(self._buf)
            end = 0
            for line in buf:
                if not line.endswith("\n"):
                    break
                self._process(line.strip())
                end = buf.tell()
            self._buf = self._buf[end:]
        

