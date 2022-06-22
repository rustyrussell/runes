# Runes - Simple Cookies You Can Extend (similar to Macaroons)

https://research.google/pubs/pub41892/ is a paper called "Macaroons:
Cookies with Contextual Caveats for Decentralized Authorization in the
Cloud".  It has one good idea, some extended ideas nobody implements,
and lots and lots of words.

The idea: a server issues a cookie to Alice.  She can derive cookies
with extra restrictions and hand them to Bob and Carol to send back to
the server, and they can't remove the restrictions.

But they did it using a Message Authetication Code (MAC, get it?),
which is actually counter-productive, since it's simpler and better to
use Length Extension to achieve the same results.  I call that a Rune;
this version really only handles strings, but you can use hex or another
encoding.

## Rune Language

A *rune* is a series of restrictions; you have to pass all of them (so
appending a new one always makes the rune less powerful).  Each
restriction is one or more alternatives ("cmd=foo OR cmd=bar"), any
one of which can pass.

The form of each alternative is a simple string:

    ALTERNATIVE := FIELDNAME CONDITION VALUE

`FIELDNAME` contains only UTF-8 characters, exclusive of
! " # $ % & ' ( ) * +, - . / : ;  ? @ [ \ ] ^ _ \` { | } ~ (C's ispunct()).
These can appear inside a `VALUE`, but `&`, `|` and `\\` must be escaped with `\` (escaping is legal for any character, but unnecessary).


`CONDITION` is one of the following values:
* `!`: Pass if field is missing (value ignored)
* `=`: Pass if exists and exactly equals
* `/`: Pass if exists and is not exactly equal
* `^`: Pass if exists and begins with
* `$`: Pass if exists and ends with
* `~`: Pass if exists and contains
* `<`: Pass if exists, is a valid integer (may be signed), and numerically less than
* `>`: Pass if exists, is a valid integer (may be signed), and numerically greater than
* `}`: Pass if exists and lexicograpically greater than (or longer)
* `{`: Pass if exists and lexicograpically less than (or shorter)
* `#`: Always pass: no condition, this is a comment.

Grouping using `(` and `)` may be added in future.

A restriction is a group of alternatives separated by `|`; restrictions
are separated by `&`.
e.g.

    cmd=foo | cmd=bar
	& subcmd! | subcmd{get

The first requires `cmd` be present, and to be `foo` or `bar`.  The second
requires that `subcmd` is not present, or is lexicographically less than `get`.
Both must be true for authorization to succeed.


## Rune Authorization

A run also comes with a SHA-256 authentication code.  This is
generated as SHA-256 of the following bytestream:

1. The secret (less than 56 bytes, known only to the server which issued it).
2. For every restriction:
   1. Pad the stream as per SHA-256 (i.e. append 0x80, then zeroes, then
      the big-endian 64-bit bitcount so far, such that it's a multiple of 64
      bytes).
   2. Append the restriction.

By using the same padding scheme as SHA-256 usually uses to end the
data, we have the property that we can initialize the SHA-256 function
with the result from any prior restriction, and continue.

The server can validate the rune authorization by repeating this
procedure and checking the result.


## Rune Encoding

Runes are encoded as base64, starting with the 256-bit SHA256
authentication code, the followed by one or more restrictions
separated by `&`.

Not because base64 is good, but because it's familiar to Web people;
we use RFC3548 with `+` and `/` replaced by `-` and `_` to make
it URL safe.

(There's also a string encoding which is easier to read and debug).

## Best Practices

It's usually worth including an id in each rune you hand out so that
you can blacklist particular runes in future (your other option is to
change your master secret, but that revokes all runes).  Because this
appears in all runes, using the empty fieldname (''), and a simple
counter reduces overall size, but you could use a UUID.

This is made trivial by the `unique_id` parameter to Rune() and
MasterRune(): it adds such an empty field with the unique id (which
the default evaluator will ignore unless you handle it explicitly).

You may also include version number, to allow future runes to have
different interpretations: this appends '-[version]' in the '' field:
the default handler will fail any cookie that has a version field
(for safe forward compatibility).

The rune unmarshalling code ensures that if an empty parameter exists,
it's the first one, and it's of a valid form.

See [examples/blacklist.py](examples/blacklist.py).


## API Example

Here's the server, making you a rune! (spoiler: it's
"-YpZTBZ4Tb5SsUz3XIukxBxR619iEthm9oNJnC0LxZM=")

```
import runes
import secrets

# Secret determined by fair dice roll.
secret = bytes([5] * 16)

# Make an unrestricted rune.
rune = runes.MasterRune(secret)

# We could add our own restrictions here, if we wanted.
print("Your rune is {}".format(rune.to_base64()))
```

Here's the server, checking a rune.  You will need to define what
conditions you provide for the rune to test; one of the most useful
ones is time, but other common things are the resource being accessed,
(e.g. URL, or command and parameters), or who is accessing it (assuming
you have authenticated them already in some way).

```
import runes
import time
import sys

secret = bytes([5] * 16)

# In real life, this would come from the web data.
runestring = sys.argv[1]

# This checks the format is correct, it's authorized, an that it meets
# our values.  I assume we have values time (UNIX, seconds since
# 1970), command and optional id.
# (You can also use rune.check() if you don't care *why* it failed)
ok, whyfail = rune.check_with_reason(secret, runestring,
                                     {'time': int(time.time()),
                                      'command': 'somecommand',
                                      'id': 'DEADBEEF'})
if not ok:
    print("Rune restrictions failed: {}".format(whyfail))
    sys.exit(1)

print("Yes, you passed!")
```


Here's the client Alice.  She gets the rune and gives Bob a variant
that can only be used for 1 minute:

```
import runes
import time

# In real life, this would come from the web data.
runestring = sys.argv[1]

# You'd catch exceptions here, usually.
rune = runes.from_base64(runestring)

# You can construct a Restriction class from a sequence of Alternative
# but it's easier to use decode() to translate a string
rune.add_restriction(rune.Restriction.decode("time < {}".format((int)time.time() + 60))

print("Your restricted rune is {}".format(rune.to_base64()))
```

You can find more examples in the examples/ subdirectory.


## Advanced Techniques

If you place a callable in the dictionary to check(), that will be
called if referred to by a restriction, so you can perform your own
processing.

This is useful in implementing ratelimiting, for example: you can have
a last-used time for each id, and thus fail if it is too soon.

See [examples/ratelimit.py](examples/ratelimit.py).


## Author

Rusty Russell wrote it; but I blame @roasbeef for raving about them
long enough at LnConf that I actually read the paper.  It only took me
18 months to find a day to implement them.
