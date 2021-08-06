#! /usr/bin/python3
"""Example of ratelimited rune: Usage id mintime [lastcalled]"""
import runes
import time
import sys
from typing import Optional

runeid = sys.argv[1]
mintime = sys.argv[2]

# Normally you'd keep lasttimes persistent across calls.
lasttimes = {}
if len(sys.argv) == 4:
    lasttimes[runeid] = float(sys.argv[3])


# Make up a rune, with mintime
rune = runes.MasterRune(bytes(16), unique_id=runeid)
rune.add_restriction(runes.Restriction.from_str('mintime={}'.format(mintime)))


def check_rune(rune, now):
    def check_id(alt) -> Optional[str]:
        if alt.cond != '=':
            return "id only supports ="
        # Future versions will append "-[version]": fail them for now.
        dash = alt.value.find('-')
        if dash != -1:
            return "unknown version {}".format(alt.value[dash+1:])
        # Don't let them set two ids.
        if 'id' in state:
            return "two id fields not supported"
        state['id'] = str(alt.value)
        return None

    def check_mintime(alt) -> Optional[str]:
        if alt.cond != '=':
            return "mintime only supports ="
        if 'id' not in state:
            # Our server would always do this!
            return "mintime must be preceeded by id"
        try:
            mintime = float(alt.value)
        except ValueError:
            return "mintime is not a valid float"
        if state['id'] in lasttimes:
            if state['time'] < lasttimes[state['id']] + mintime:
                return "mintime: too early"
        return None

    state = {}
    state['time'] = now
    ok, whyfail = rune.are_restrictions_met({'': check_id, 'mintime': check_mintime})
    # We choose to only update lasttimes when it succeeds.
    if ok:
        lasttimes[state['id']] = now
    return ok, whyfail


now = time.time()
ok, whyfail = check_rune(rune, now)

# We print args for next time.
print("{} {}".format(runeid, mintime), end='')
if runeid in lasttimes:
    print(" {}".format(lasttimes[runeid]))
else:
    print('')

if not ok:
    print("Rune failed: {}".format(whyfail))
    sys.exit(1)

print("Rune OK!")
