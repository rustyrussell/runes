#! /usr/bin/python3
"""Simple commandline decoder and kinda-pretty printer

Try:
./examples/decode.py VJOGnQcJfi3GHgfgSxCd3cLv97zvdTLAkE4hXLdKwCdjb21tYW5kPWZvb2Jhcnxjb21tYW5kPWZpenpidXomdGltZTwxNjI3NDQ5NTgwJnN1YmNvbW1hbmReZnxzdWJjb21tYW5kJHJ8c3ViY29tbWFuZH5oZWxwJng-MTAwMCZzb21lZmllbGR7ZXhpdHxzb21lZmllbGR9a2l0ZSZXb3JzdGNvb2tpZWV2ZXIjUmVhbGx5

This gives:
    Authcode: 5493869d07097e2dc61e07e04b109dddc2eff7bcef7532c0904e215cb74ac027
    Restrictions:
      * command equals 'foobar'
        OR command equals 'fizzbuz'
      * time (integer) less than 1627449580
      * subcommand starts with 'f'
        OR subcommand ends with 'r'
        OR subcommand contains 'help'
      * x (integer) greater than 1000
      * somefield ordered before 'exit'
        OR somefield ordered after 'kite'
      * Comment: WorstcookieeverReally
"""
import runes
import string
import sys
import re

# In real life, this would come from the web data.
runestring = sys.argv[1]

# You'd catch exceptions here, usually.
rune = runes.Rune.from_base64(runestring)


# Turn operators into english
def pretty(code: str):
    parts = re.split('([' + string.punctuation + '])', code, maxsplit=1)
    formatters = {'!': "{field} is missing",
                  '=': "{field} equals '{value}'",
                  '^': "{field} starts with '{value}'",
                  '$': "{field} ends with '{value}'",
                  '~': "{field} contains '{value}'",
                  '<': "{field} (integer) less than {value}",
                  '>': "{field} (integer) greater than {value}",
                  '{': "{field} ordered before '{value}'",
                  '}': "{field} ordered after '{value}'",
                  '#': "Comment: {field}{value}"}

    formatter = formatters.get(parts[1], "UNKNOWN {op} on {field} and '{value}'")
    return formatter.format(field=parts[0], op=parts[1], value=parts[2])


print("Authcode: {}".format(rune.authcode().hex()))
print("Restrictions:")
for r in rune.restrictions:
    print('  * ', end='')
    print('\n    OR '.join([pretty(alt.encode()) for alt in r.alternatives]))
