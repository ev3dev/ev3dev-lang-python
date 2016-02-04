#! /usr/bin/python2.7

import json
import time
import ev3dev.ev3 as ev3

def next_commands():
        for d in test['data']:
                for c in d['commands']:
                        yield c

test = json.loads( open( './run-direct.json' ).read() )

print test['data'][0]['port']
m = ev3.Motor( test['data'][0]['port'] )

name     = test['meta']['name']
interval = test['meta']['interval']
max_time = test['meta']['max_time']

start = time.clock()
end   = start + max_time/1000

intervals = [x/1000.0 for x in range( 0, max_time, interval )]

now = time.clock()

commands = next_commands()

c = commands.next()

next_interval = c['time']/1000.0
results = []

for i in intervals:
        i = i + start
        while now < i:
                now = time.clock()
        if now >= start + next_interval:
                print i, next_interval, now
                for a in c['attributes']:
                        for k in a.keys():
                                print "    ", k, " = ", a[k]
                                setattr(m,k,a[k])
                try:
                        c = commands.next()
                        next_interval = c['time']/1000.0
                except StopIteration:
                        next_interval = max_time/1000.0
        results.append( (now-start, (m.speed, m.position, m.duty_cycle)) )


print 'data = ['

first = True
for r in results:
        if first:
                print( '      ({0}, ({1}, {2}, {3}))'.format(r[0], r[1][0], r[1][1], r[1][2]))
                first = False
        else:
                print( '    , ({0}, ({1}, {2}, {3}))'.format(r[0], r[1][0], r[1][1], r[1][2]))

print ']'


