#! /usr/bin/python3
"""Example of the server issuiing a rune"""
import runes
import secrets

# Secret determined by fair dice roll.
secret = bytes([5] * 16)

# Make an unrestricted rune.
rune = runes.MasterRune(secret)

# We could add our own restrictions here, if we wanted.
print("Your rune is {}".format(rune.to_base64()))
