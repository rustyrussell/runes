import base64
import hashlib
import re
# We can't use the hashlib one, since we need midstate access :(
import sha256
import string
from typing import Dict, Sequence, Optional, Tuple, Any


def padlen_64(x: int):
    """Amount which will increase x until it's divisible evenly by 64"""
    return (64 - (x % 64)) % 64


def end_shastream(length: int):
    """Simulate an SHA-256 ending pad (1 bit, zero bad, 64-bit length)"""
    padlen = padlen_64(length + 1 + 8)
    return bytes([0x80]) + bytes(padlen) + int.to_bytes(length * 8, 8, 'big')


class Alternative(object):
    """One of possibly several conditions which could be met"""
    def __init__(self, field: str, cond: str, value: str):
        if any([c in string.punctuation for c in field]):
            raise ValueError("field not valid")
        if any([c in string.punctuation for c in value]):
            raise ValueError("value not valid")
        if cond not in ('!', '=', '^', '$', '~', '<', '>', '}', '{', '#'):
            raise ValueError("cond not valid")
        self.field = field
        self.value = value
        self.cond = cond

    def test(self, values: Dict[str, Any]) -> Optional[str]:
        """Returns None on success, otherwise an explanation string"""
        # This is always True
        if self.cond == '#':
            return None 

        def why(cond, field, explanation) -> Optional[str]:
            if cond:
                return None
            return '{}: {}'.format(field, explanation)

        # If it's missing, it's only True if it's a missing test.
        if self.field not in values:
            return why(self.cond == '!', self.field, 'is missing')

        val = str(values[self.field])
        if self.cond == '!':
            return why(False, self.field, 'is present')
        elif self.cond == '=':
            return why(val == self.value,
                       self.field,
                       '!= {}'.format(self.value))
        elif self.cond == '^':
            return why(val.startswith(self.value),
                       self.field,
                       'does not start with {}'.format(self.value))
        elif self.cond == '$':
            return why(val.endswith(self.value),
                       self.field,
                       'does not end with {}'.format(self.value))
        elif self.cond == '~':
            return why(self.value in val,
                       self.field,
                       'does not contain {}'.format(self.value))
        elif self.cond == '<':
            try:
                actual_int = int(val)
            except ValueError:
                return why(False, self.field, "not an integer field")
            try:
                restriction_val = int(self.value)
            except ValueError:
                return why(False, self.field, "not a valid integer")
            return why(actual_int < restriction_val,
                       self.field,
                       ">= {}".format(restriction_val))
        elif self.cond == '>':
            try:
                actual_int = int(val)
            except ValueError:
                return why(False, self.field, "not an integer field")
            try:
                restriction_val = int(self.value)
            except ValueError:
                return why(False, self.field, "not a valid integer")
            return why(actual_int > restriction_val,
                       self.field,
                       "<= {}".format(restriction_val))
        elif self.cond == '{':
            return why(val < self.value,
                       self.field,
                       'is the same or ordered after {}'.format(self.value))
        elif self.cond == '}':
            return why(val > self.value,
                       self.field,
                       'is the same or ordered before {}'.format(self.value))
        else:
            # We checked this in init!
            assert False

    def encode(self) -> str:
        return self.field + self.cond + self.value

    @classmethod
    def decode(cls, encstr: str, ignore_ws=True) -> 'Alternative':
        if ignore_ws:
            encstr = re.sub(r'\s+', '', encstr)
        return cls(*re.split('([' + string.punctuation + '])', encstr))

    def __eq__(self, other) -> bool:
        return (self.field == other.field
                and self.value == other.value
                and self.cond == other.cond)


class Restriction(object):
    """A restriction is a set of alternatives: any of those pass, the restriction is met"""
    def __init__(self, alternatives: Sequence[Alternative]):
        self.alternatives = alternatives

    def test(self, values: Dict[str, Any]) -> Optional[str]:
        """Returns None on success, otherwise a string of all the failures"""
        reasons = []
        for alt in self.alternatives:
            reason = alt.test(values)
            if reason is None:
                return None
            reasons.append(reason)

        return " AND ".join(reasons)

    def encode(self) -> str:
        return '|'.join([alt.encode() for alt in self.alternatives])

    @classmethod
    def decode(cls, encstr: str, ignore_ws=True) -> 'Restriction':
        alts = []
        for altstr in encstr.split('|'):
            alts.append(Alternative.decode(altstr, ignore_ws))
        return cls(alts)

    def __eq__(self, other) -> bool:
        return list(self.alternatives) == list(other.alternatives)
    

class Rune(object):
    """A Rune, such as you might get from a server.  You can add
restrictions and it will still be valid"""
    def __init__(self,
                 authcode: bytes,
                 restrictions: Sequence[Restriction] = []):
        self.restrictions = restrictions

        # How many bytes encoded so far? (seed block is 64 bytes)
        runelength = 64
        for r in restrictions:
            runelength += len(r.encode())
            runelength += padlen_64(runelength)

        # Replace with real shastate (aka authcode)
        self.shaobj = sha256.sha256()
        self.shaobj.state = (authcode, runelength)

    def add_restriction(self, restriction: Restriction) -> None:
        self.restrictions.append(restriction)
        self.shaobj.update(bytes(restriction.encode(), encoding='utf8'))
        self.shaobj.update(end_shastream(self.shaobj.state[1]))

    def are_restrictions_met(self, values: Dict[str, Any]) -> Tuple[bool, str]:
        """Tests the restrictions against the values dict given.  Normally
        values are treated strings, but < and > conditions only work
        if they're actually integers.

        Returns (True, '') if everything is good.  Otherwise, returns
        (False, reasonstring)

        """,
        for r in self.restrictions:
            reasons = r.test(values)
            if reasons is not None:
                return False, reasons
        return True, ''

    def authcode(self) -> bytes:
        return self.shaobj.state[0]

    def to_str(self) -> str:
        restrstr = '&'.join([r.encode() for r in self.restrictions])
        return base64.urlsafe_b64encode(self.authcode()
                                        + bytes(restrstr, encoding='utf8')).decode('utf8')

    @classmethod
    def from_str(cls, b64str) -> 'Rune':
        binstr = base64.urlsafe_b64decode(b64str)
        restrictions = []
        # Python empty string split with delimiter *SUCKS*
        parts = binstr[32:].decode('utf8').split('&')
        if parts == ['']:
            parts = []
        for restrstr in parts:
            restrictions.append(Restriction.decode(restrstr, ignore_ws=False))
        return cls(binstr[:32], restrictions)

    def __eq__(self, other) -> bool:
        return (self.restrictions == other.restrictions
                and self.shaobj.state == other.shaobj.state)


class MasterRune(Rune):
    """This is where the server creates the Rune"""
    def __init__(self, seedsecret: bytes, restrictions: Sequence[Restriction]=[]):
        self.restrictions = []
        # Everyone assumes that seed secret takes 1 block only
        assert len(seedsecret) + 1 + 8 <= 64
        self.shaobj = sha256.sha256()
        self.shaobj.update(seedsecret + end_shastream(len(seedsecret)))
        for r in restrictions:
            self.add_restriction(r)

        # For fast calc using hashlib
        self.shabase = hashlib.sha256()
        self.shabase.update(seedsecret)
        self.seclen = len(seedsecret)

    def is_rune_authorized(self, other: Rune) -> bool:
        """This is faster than adding the restrictions one-by-one and checking
        the final authcode (but equivalent)"""
        # Make copy, as we're going to update state.
        sha = self.shabase.copy()
        totlen = self.seclen
        for r in other.restrictions:
            pad = end_shastream(totlen)
            sha.update(pad)
            totlen += len(pad)
            enc = bytes(r.encode(), encoding='utf8')
            sha.update(enc)
            totlen += len(enc)

        return other.authcode() == sha.digest()
