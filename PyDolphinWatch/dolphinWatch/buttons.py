'''
Created on 10.11.2015

@author: Felk
'''

from enum import Enum

class WiimoteButtons(Enum):
    NONE  = 0x0000
    LEFT  = 0x0001
    RIGHT = 0x0002
    DOWN  = 0x0004
    UP    = 0x0008
    PLUS  = 0x0010
    
    TWO   = 0x0100
    ONE   = 0x0200
    B     = 0x0400
    A     = 0x0800
    MINUS = 0x1000
    HOME  = 0x8000

class GCPadButtons(Enum):
    NONE  = 0x0000
    LEFT  = 0x0001
    RIGHT = 0x0002
    DOWN  = 0x0004
    UP    = 0x0008
    Z     = 0x0010
    R     = 0x0020
    L     = 0x0040
    A     = 0x0100
    B     = 0x0200
    X     = 0x0400
    Y     = 0x0800
    START = 0x1000

class GCPadSticks(Enum):
    NONE  = ( 0,  0, 0, 0)
    UP    = ( 0,  1, 0, 0)
    DOWN  = ( 0, -1, 0, 0)
    LEFT  = (-1,  0, 0, 0)
    RIGHT = ( 1,  0, 0, 0)
