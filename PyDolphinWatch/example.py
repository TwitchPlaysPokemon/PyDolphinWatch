'''
Very small example of how one could use PyDolphinWatch.
This example just permanently reconnects to localhost:6000
and wants to always know the value of memory address 0x00478498,
printing that to stdout

@author: Felk
'''

from __future__ import print_function, division

from dolphinWatch import DolphinWatch
import gevent
        
def reconnect(watcher, reason):
    print("DolphinWatch reconnection attempt in 3 seconds...")
    gevent.sleep(3)
    watcher.connect()
        
def _initDolphinWatch(watcher):
    print("Initializing!")
    watcher._subscribe(0x00478498, print)

def main():
    watcher = DolphinWatch("localhost", 6000)
    watcher.onDisconnect(reconnect)
    watcher.onConnect(_initDolphinWatch)
    watcher.connect()
    
    gevent.sleep(1000)

if __name__ == "__main__":
    main()
