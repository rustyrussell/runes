#! /usr/bin/python3
"""Example of the server checking the rune is valid, and its conditions pass"""
import runes
import time
import sys

secret = bytes([5] * 16)

# In real life, this would come from the web data.
runestring = sys.argv[1]

# This checks the format is correct, it's authorized, an that it meets
# our values.  I assume we have values time (UNIX, seconds since
# 1970), command and optional id.
ok, whyfail = rune.check_with_reason(secret, runestring,
                                     {'time': int(time.time()),
                                      'command': 'somecommand',
                                      'id': 'DEADBEEF'})
if not ok:
    print("Rune restrictions failed: {}".format(whyfail))
    sys.exit(1)

print("Yes, you passed!")
