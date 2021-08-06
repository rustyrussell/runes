import base64
import copy
import hashlib
import re
# We can't use the hashlib one, since we need midstate access :(
import sha256  # type: ignore
import string
from typing import Dict, Sequence, Optional, Tuple, Any, Union


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
        if cond not in ('!', '=', '/', '^', '$', '~', '<', '>', '}', '{', '#'):
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
            # Default to ignoring id field as long as no version.
            if self.field == '':
                return why('-' not in self.value, 'id', 'unknown version {}'.format(self.value))
            return why(self.cond == '!', self.field, 'is missing')

        # If they supply a function, hand it to them.
        if callable(values[self.field]):
            return values[self.field](self)

        val = str(values[self.field])
        if self.cond == '!':
            return why(False, self.field, 'is present')
        elif self.cond == '=':
            return why(val == self.value,
                       self.field,
                       '!= {}'.format(self.value))
        elif self.cond == '/':
            return why(val != self.value,
                       self.field,
                       '= {}'.format(self.value))
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
        return self.field + self.cond + (self.value
                                         .replace('\\', '\\\\')
                                         .replace('|', '\\|')
                                         .replace('&', '\\&'))

    @classmethod
    def decode(cls, encstr: str) -> Tuple['Alternative', str]:
        """Pull an Alternative from encoded string, return remainder"""
        cond = None
        end_off = 0

        # Swallow field up to conditiona
        while end_off < len(encstr):
            if encstr[end_off] in string.punctuation:
                cond = encstr[end_off]
                break
            end_off += 1
        if cond is None:
            raise ValueError('{} does not contain any operator'
                             .format(encstr))
        field = encstr[:end_off]
        end_off += 1

        value = ''
        while end_off < len(encstr):
            if encstr[end_off] == '|':
                # We swallow this
                end_off += 1
                break
            if encstr[end_off] == '&':
                break
            if encstr[end_off] == '\\':
                end_off += 1
            value += encstr[end_off]
            end_off += 1

        return cls(field, cond, value), encstr[end_off:]

    @classmethod
    def from_str(cls, encstr: str) -> 'Alternative':
        """Turns this user-readable string into an Alternative (no escaping)"""
        encstr = re.sub(r'\s+', '', encstr)
        return cls(*re.split('([' + string.punctuation + '])', encstr, maxsplit=1))

    def __eq__(self, other) -> bool:
        return (self.field == other.field
                and self.value == other.value
                and self.cond == other.cond)


class Restriction(object):
    """A restriction is a set of alternatives: any of those pass, the
restriction is met"""
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
    def decode(cls, encstr: str) -> Tuple['Restriction', str]:
        """Pull a Restriction from encoded string, return remainder"""
        alts = []
        while len(encstr) != 0:
            if encstr.startswith('&'):
                encstr = encstr[1:]
                break
            alt, encstr = Alternative.decode(encstr)
            alts.append(alt)
        return cls(alts), encstr

    @classmethod
    def from_str(cls, encstr: str) -> 'Restriction':
        """Returns a Restriction from an escaped string (ignoring whitespace)"""
        encstr = re.sub(r'\s+', '', encstr)
        ret, remainder = cls.decode(encstr)
        if len(remainder) != 0:
            raise ValueError("Restriction had extrs characters at end: {}"
                             .format(remainder))
        return ret

    @classmethod
    def unique_id(cls,
                  unique_id: Union[int, str],
                  version: Optional[Union[int, str]] = None) -> 'Restriction':
        """Helper to produce an id 'restriction'"""
        idstr = str(unique_id)
        if '-' in idstr:
            raise ValueError('Hyphen not allowed in unique_id {}'.format(idstr))
        if version:
            idstr += '-{}'.format(version)
        # We use the empty field for this, since it's always present.
        return cls([Alternative('', '=', idstr)])

    def __eq__(self, other) -> bool:
        return list(self.alternatives) == list(other.alternatives)


class Rune(object):
    """A Rune, such as you might get from a server.  You can add
restrictions and it will still be valid"""
    def __init__(self,
                 authcode: bytes,
                 restrictions: Sequence[Restriction] = [],
                 unique_id: Optional[Union[int, str]] = None,
                 version: Optional[Union[int, str]] = None):
        # If they provide a unique_id, it goes first.
        if unique_id is not None:
            restrictions = ([Restriction.unique_id(unique_id, version)]
                            + list(restrictions))
        self.restrictions = list(restrictions)

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

    def to_base64(self) -> str:
        restrstr = '&'.join([r.encode() for r in self.restrictions])
        binstr = base64.urlsafe_b64encode(self.authcode()
                                          + bytes(restrstr, encoding='utf8'))
        return binstr.decode('utf8')

    @classmethod
    def from_base64(cls, b64str) -> 'Rune':
        binstr = base64.urlsafe_b64decode(b64str)
        restrictions = []
        restrictstr = binstr[32:].decode('utf8')

        while len(restrictstr) != 0:
            restr, restrictstr = Restriction.decode(restrictstr)
            restrictions.append(restr)
        return cls(binstr[:32], restrictions)

    def __eq__(self, other) -> bool:
        return (self.restrictions == other.restrictions
                and self.shaobj.state == other.shaobj.state)

    def copy(self) -> 'Rune':
        """Perform a shallow copy"""
        return self.__copy__()

    def __copy__(self) -> 'Rune':
        # You don't want to share the shaobj!
        return Rune(self.shaobj.state[0], self.restrictions)

    def __deepcopy__(self, memo=None) -> 'Rune':
        """sha256.sha256 doesn't implement pickle"""
        return Rune(self.shaobj.state[0], copy.deepcopy(self.restrictions))


class MasterRune(Rune):
    """This is where the server creates the Rune; it's recommended you
give each rune a unique id (often a persistent counter) (with an
optional version), which gets included as an empty-fieldname field.

    """
    def __init__(self,
                 seedsecret: bytes,
                 restrictions: Sequence[Restriction] = [],
                 unique_id: Optional[Union[int, str]] = None,
                 version: Optional[Union[int, str]] = None):
        # If they provide a unique_id, it goes first.
        if unique_id is not None:
            restrictions = [Restriction.unique_id(unique_id, version)] + list(restrictions)

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

    def copy(self) -> 'Rune':
        """Perform a shallow copy"""
        return self.__copy__()

    def __copy__(self) -> 'MasterRune':
        # Create dummy so we can populate it (we don't store secret)
        ret = MasterRune(bytes())
        ret.restrictions = self.restrictions.copy()
        ret.shaobj.state = self.shaobj.state
        ret.shabase = self.shabase
        ret.seclen = self.seclen
        return ret

    def __deepcopy__(self, memo=None) -> 'MasterRune':
        """sha256.sha256 doesn't implement pickle"""
        ret = MasterRune(bytes())
        ret.restrictions = copy.deepcopy(self.restrictions)
        ret.shaobj.state = self.shaobj.state
        ret.shabase = self.shabase
        ret.seclen = self.seclen
        return ret

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

    def check_with_reason(self, b64str: str, values: Dict[str, Any]) -> Tuple[bool, str]:
        """All-in-one check that a runestring is valid, derives from this
MasterRune and passes all its conditions against the given dictionary
of values or callables"""
        try:
            rune = Rune.from_base64(b64str)
        except:  # noqa: E722
            return False, "runestring invalid"
        if not self.is_rune_authorized(rune):
            return False, "rune authcode invalid"
        return rune.are_restrictions_met(values)


def check_with_reason(secret: bytes, b64str: str, values: Dict[str, Any]) -> Tuple[bool, str]:
    """Convenience function that the b64str runestring is valid, derives
from our secret, and passes against these values.  If you want to
check many runes, it's more efficient to create the MasterRune first
then check them, but this is fine if you're only checking one.

    """
    return MasterRune(secret).check_with_reason(b64str, values)


def check(secret: bytes, b64str: str, values: Dict[str, Any]) -> bool:
    """Convenience function that the b64str runestring is valid, derives
from our secret, and passes against these values.  If you want to
check many runes, it's more efficient to create the MasterRune first
then check them, but this is fine if you're only checking one.

Unlike check_with_reason(), this discards the reason and returns a
simple True or False.

    """
    return check_with_reason(secret, b64str, values)[0]
