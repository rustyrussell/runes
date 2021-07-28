#! /usr/bin/python3
"""Simple commandline decoder and kinda-pretty printer"""
import runes
import string
import sys
import re

# In real life, this would come from the web data.
runestring = sys.argv[1]

# You'd catch exceptions here, usually.
rune = runes.Rune.from_base64(runestring)


# Insert whitespace around operators.
def pretty(code: str):
    return re.sub('([' + string.punctuation + '])', r' \1 ', code)


print("Authcode: {}".format(rune.authcode().hex()))
print("Restrictions:")
for r in rune.restrictions:
    print('  * ', end='')
    print('\n    OR '.join([pretty(alt.encode()) for alt in r.alternatives]))
