#! /usr/bin/python3
"""Example of adding restrictions to a rune, eg:

examples/restrict.py -YpZTBZ4Tb5SsUz3XIukxBxR619iEthm9oNJnC0LxZM= 'command=foobar|command=fizzbuz'
"""
import runes
import sys

rune = runes.Rune.from_str(sys.argv[1])

for arg in sys.argv[2:]:
    rune.add_restriction(runes.Restriction.decode(arg))

print("Your restricted rune is {}".format(rune.to_str()))
