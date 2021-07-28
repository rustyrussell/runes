#! /usr/bin/python3
import runes
import time
import sys

# In real life, this would come from the web data.
runestring = sys.argv[1]

# You'd catch exceptions here, usually.
rune = runes.Rune.from_base64(runestring)

# You can construct a Restriction class from a sequence of Alternative
# but it's easier to use from_str()
rune.add_restriction(runes.Restriction.from_str("time < {}"
                                                .format(int(time.time())
                                                        + 60)))

print("Your restricted rune is {}".format(rune.to_base64()))
