#! /usr/bin/python3
"""Example of the server issuiing a rune"""
import runes

# Secret determined by fair dice roll.
secret = bytes([5] * 16)

# Make an unrestricted rune.
rune = runes.MasterRune(secret)

# Best practice is to always include a uniqueid[-version], so we
# can blacklist, and safely upgrade in future.  A UUID is big,
# so I recommend a persistent internal counter (here, "0").
rune.add_restriction(rune.Restriction.from_str('=0'))

# We could add our own restrictions here, if we wanted.
print("Your rune is {}".format(rune.to_base64()))
