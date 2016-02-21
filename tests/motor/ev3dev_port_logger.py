#!/usr/bin/env python

import json
import argparse
import time
import threading

import ev3dev.ev3 as ev3

parser = argparse.ArgumentParser()
parser.add_argument("infile", help="the name of the input specification")
args = parser.parse_args()

# Log device readings at requested intervals
class LogThread(threading.Thread):
    def __init__(self, interval, device, attributes):
        super(LogThread, self).__init__()

        self.interval   = interval
        self.device     = device
        self.attributes = attributes
        self.done       = threading.Event()

    def run(self):
        tic = time.time()
        toc = tic
        self.results = []

        while not self.done.isSet():
            now = time.time()
            s = ()
            for a in self.attributes:
                s += ( getattr( self.device, a ), )
            self.results.append((now-tic, s))

            while .005 > toc - time.time():
                toc += self.interval
            time.sleep(toc - time.time())

    def join(self, timeout=None):
        self.done.set()
        super(LogThread, self).join(timeout)


test = json.loads( open( args.infile ).read() )

def execute_actions(actions):
    for p,c in actions['ports'].items():
        for b in c:
            for k,v in b.items():
                setattr( device[p], k, v )
 
device = {}
logs = {}

for p,v in test['meta']['ports'].items():
    device[p] = getattr( ev3, v['device_class'] )( p )

if test['actions'][0]['time'] < 0:
    execute_actions(test['actions'][0])

for p,v in test['meta']['ports'].items():
    device[p] = getattr( ev3, v['device_class'] )( p )

    logs[p] = LogThread(test['meta']['interval'] * 1e-3,
                        device[p],
                        v['log_attributes'] )
    logs[p].start()

start = time.time()
end   = start + test['meta']['max_time'] * 1e-3

for a in test['actions']:
    if a['time'] >= 0:
        then = start + a['time'] * 1e-3
        while time.time() < then: pass
        execute_actions(a)

while time.time() < end:
    pass

test['data'] = {}

for p,v in test['meta']['ports'].items():
     logs[p].join()
     test['data'][p] = logs[p].results

# Add a nice JSON formatter here - maybe?
print json.dumps( test, indent = 4 )
