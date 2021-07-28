#! /usr/bin/python3
"""Example of the server checking the rune is valid, and its conditions pass"""
import runes
import time
import sys

secret = bytes([5] * 16)
master_rune = runes.MasterRune(secret)

# In real life, this would come from the web data.
runestring = sys.argv[1]

# You'd catch exceptions here, usually.
rune = runes.Rune.from_str(runestring)

# Make sure auth is correct, first.
if not master_rune.is_rune_authorized(rune):
    print("Rune is not authorized, go away!")
    sys.exit(1)

# Now, lets see if it meets our values.  I assume we
# have values time (UNIX, seconds since 1970), command
# and optional id.
ok, whyfail = rune.are_restrictions_met({'time': int(time.time()),
                                         'command': 'somecommand',
					 'id': 'DEADBEEF'})
if not ok:
    print("Rune restrictions failed: {}".format(whyfail))
    sys.exit(1)

print("Yes, you passed!")
