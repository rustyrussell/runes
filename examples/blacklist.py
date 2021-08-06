#! /usr/bin/python3
"""Example of runes with ids (from cmdline), and a blacklist which fails id=1"""
import runes
import time
import sys
from typing import Optional

# In real life, this would come from a persistent counter.
this_id = int(sys.argv[1])
rune = runes.MasterRune(bytes(16))
rune.add_restriction(runes.Restriction.from_str('id={}'.format(this_id)))
print("Rune is {}".format(rune.to_base64()))


# We will fail all runes with id 1
blacklist = {'1': "I don't like you"}

def check_id(alt) -> Optional[str]:
    if alt.cond != '=':
        return "id only supports ="
    return blacklist.get(alt.value)

ok, whyfail = rune.are_restrictions_met({'id': check_id})
if not ok:
    print("Rune failed: {}".format(whyfail))
    sys.exit(1)

print("Rune OK!")
