import copy
import hashlib
import runes
import sha256  # type: ignore
from typing import Sequence


# This is a simplified version of end_shastream
def end_shastream_simple(length: int) -> bytes:
    stream = bytes([0x80])
    while ((length + len(stream) + 8) % 64) != 0:
        stream += bytes(1)
    stream += int.to_bytes(length * 8, 8, 'big')
    return stream


def check_auth_sha(secret: bytes, restrictions: Sequence[runes.Restriction]):
    stream = secret

    for r in restrictions:
        stream += end_shastream_simple(len(stream))
        stream += bytes(r.encode(), encoding='utf8')

    return hashlib.sha256(stream).digest()


def test_end_shastream():
    # Make sure it gives same as our naive approach
    for length in range(0, 100):
        assert runes.end_shastream(length) == end_shastream_simple(length)

    # Make sure it agrees with actual SHA terminal.
    for length in range(0, 100):
        correct = hashlib.sha256(bytes(length)).digest()
        manual = sha256.sha256()
        manual.update(bytes(length))
        manual.update(runes.end_shastream(length))
        assert manual.state[0] == correct


def test_rune_auth():
    # Rune with 16x0 secret.
    secret = bytes(16)
    mr = runes.MasterRune(secret)

    assert check_auth_sha(secret, []) == mr.authcode()
    assert mr.is_rune_authorized(runes.Rune(mr.authcode(), []))

    restriction = runes.Restriction([runes.Alternative('f1', '=', 'v1')])
    mr.add_restriction(restriction)

    assert check_auth_sha(secret, [restriction]) == mr.authcode()
    assert not mr.is_rune_authorized(runes.Rune(mr.authcode(), []))
    assert mr.is_rune_authorized(runes.Rune(mr.authcode(), [restriction]))

    long_restriction = runes.Restriction([runes.Alternative('f' * 32, '=', 'v1' * 64)])
    mr.add_restriction(long_restriction)

    assert check_auth_sha(secret, [restriction, long_restriction]) == mr.authcode()
    assert not mr.is_rune_authorized(runes.Rune(mr.authcode(), [restriction]))
    assert not mr.is_rune_authorized(runes.Rune(mr.authcode(), [long_restriction]))
    assert not mr.is_rune_authorized(runes.Rune(mr.authcode(), [long_restriction, restriction]))
    assert mr.is_rune_authorized(runes.Rune(mr.authcode(), [restriction, long_restriction]))


def test_rune_alternatives():
    """Test that we interpret alternatives as expected"""
    alt = runes.Alternative('f1', '!', '')
    assert alt.test({}) is None
    assert alt.test({'f1': '1'}) == 'f1: is present'
    assert alt.test({'f2': '1'}) is None

    alt = runes.Alternative('f1', '=', '1')
    assert alt.test({}) == 'f1: is missing'
    assert alt.test({'f1': '1'}) is None
    assert alt.test({'f1': '01'}) == 'f1: != 1'
    assert alt.test({'f1': '10'}) == 'f1: != 1'
    assert alt.test({'f1': '010'}) == 'f1: != 1'
    assert alt.test({'f1': '10101'}) == 'f1: != 1'

    alt = runes.Alternative('f1', '$', '1')
    assert alt.test({}) == 'f1: is missing'
    assert alt.test({'f1': '1'}) is None
    assert alt.test({'f1': '01'}) is None
    assert alt.test({'f1': '10'}) == 'f1: does not end with 1'
    assert alt.test({'f1': '010'}) == 'f1: does not end with 1'
    assert alt.test({'f1': '10101'}) is None

    alt = runes.Alternative('f1', '^', '1')
    assert alt.test({}) == 'f1: is missing'
    assert alt.test({'f1': '1'}) is None
    assert alt.test({'f1': '01'}) == 'f1: does not start with 1'
    assert alt.test({'f1': '10'}) is None
    assert alt.test({'f1': '010'}) == 'f1: does not start with 1'
    assert alt.test({'f1': '10101'}) is None

    alt = runes.Alternative('f1', '~', '1')
    assert alt.test({}) == 'f1: is missing'
    assert alt.test({'f1': '1'}) is None
    assert alt.test({'f1': '01'}) is None
    assert alt.test({'f1': '10'}) is None
    assert alt.test({'f1': '010'}) is None
    assert alt.test({'f1': '10101'}) is None
    assert alt.test({'f1': '020'}) == 'f1: does not contain 1'

    alt = runes.Alternative('f1', '<', '1')
    assert alt.test({}) == 'f1: is missing'
    assert alt.test({'f1': '1'}) == 'f1: >= 1'
    assert alt.test({'f1': '01'}) == 'f1: >= 1'
    assert alt.test({'f1': '10'}) == 'f1: >= 1'
    assert alt.test({'f1': '010'}) == 'f1: >= 1'
    assert alt.test({'f1': '10101'}) == 'f1: >= 1'
    assert alt.test({'f1': '020'}) == 'f1: >= 1'
    assert alt.test({'f1': '0'}) is None
    assert alt.test({'f1': 'x'}) == 'f1: not an integer field'

    alt = runes.Alternative('f1', '<', 'x')
    assert alt.test({}) == 'f1: is missing'
    assert alt.test({'f1': '1'}) == 'f1: not a valid integer'

    alt = runes.Alternative('f1', '>', '1')
    assert alt.test({}) == 'f1: is missing'
    assert alt.test({'f1': '1'}) == 'f1: <= 1'
    assert alt.test({'f1': '01'}) == 'f1: <= 1'
    assert alt.test({'f1': '10'}) is None
    assert alt.test({'f1': '010'}) is None
    assert alt.test({'f1': '10101'}) is None
    assert alt.test({'f1': '020'}) is None
    assert alt.test({'f1': '0'}) == 'f1: <= 1'
    assert alt.test({'f1': 'x'}) == 'f1: not an integer field'

    alt = runes.Alternative('f1', '>', 'x')
    assert alt.test({}) == 'f1: is missing'
    assert alt.test({'f1': '1'}) == 'f1: not a valid integer'

    alt = runes.Alternative('f1', '{', '1')
    assert alt.test({}) == 'f1: is missing'
    assert alt.test({'f1': '1'}) == 'f1: is the same or ordered after 1'
    assert alt.test({'f1': '01'}) is None
    assert alt.test({'f1': '10'}) == 'f1: is the same or ordered after 1'
    assert alt.test({'f1': '010'}) is None
    assert alt.test({'f1': '10101'}) == 'f1: is the same or ordered after 1'
    assert alt.test({'f1': '020'}) is None
    assert alt.test({'f1': '0'}) is None

    alt = runes.Alternative('f1', '}', '1')
    assert alt.test({}) == 'f1: is missing'
    assert alt.test({'f1': '1'}) == 'f1: is the same or ordered before 1'
    assert alt.test({'f1': '01'}) == 'f1: is the same or ordered before 1'
    assert alt.test({'f1': '10'}) is None
    assert alt.test({'f1': '010'}) == 'f1: is the same or ordered before 1'
    assert alt.test({'f1': '10101'}) is None
    assert alt.test({'f1': '020'}) == 'f1: is the same or ordered before 1'
    assert alt.test({'f1': '0'}) == 'f1: is the same or ordered before 1'

    alt = runes.Alternative('f1', '#', '1')
    assert alt.test({}) is None
    assert alt.test({'f1': '1'}) is None
    assert alt.test({'f1': '01'}) is None
    assert alt.test({'f1': '10'}) is None
    assert alt.test({'f1': '010'}) is None
    assert alt.test({'f1': '10101'}) is None
    assert alt.test({'f1': '020'}) is None
    assert alt.test({'f1': '0'}) is None


def test_rune_restriction():
    alt1 = runes.Alternative('f1', '!', '')
    alt2 = runes.Alternative('f2', '=', '2')

    # Either can be true
    restr = runes.Restriction((alt1, alt2))
    assert restr.test({}) is None
    assert restr.test({'f1': '1', 'f2': 3}) == "f1: is present AND f2: != 2"
    assert restr.test({'f2': '1'}) is None
    assert restr.test({'f2': '2'}) is None
    assert restr.test({'f2': 2}) is None


def test_rune_restrictions():
    """Either of these passes, the restriction passes"""
    alt1 = runes.Alternative('f1', '!', '')
    alt2 = runes.Alternative('f2', '=', '2')

    rune = runes.Rune(bytes(32), [runes.Restriction((alt1, alt2))])
    assert rune.are_restrictions_met({}) == (True, '')
    assert (rune.are_restrictions_met({'f1': '1', 'f2': 3})
            == (False, 'f1: is present AND f2: != 2'))
    assert rune.are_restrictions_met({'f1': '1', 'f2': 2}) == (True, '')
    assert rune.are_restrictions_met({'f2': '1'}) == (True, '')
    assert rune.are_restrictions_met({'f2': '2'}) == (True, '')

    alt3 = runes.Alternative('f3', '>', '2')
    rune = runes.Rune(bytes(32), [runes.Restriction((alt1, alt2)),
                                  runes.Restriction((alt3,))])
    assert rune.are_restrictions_met({}) == (False, 'f3: is missing')
    assert (rune.are_restrictions_met({'f1': '1', 'f2': 3})
            == (False, 'f1: is present AND f2: != 2'))
    assert (rune.are_restrictions_met({'f1': '1', 'f2': 2})
            == (False, 'f3: is missing'))
    assert rune.are_restrictions_met({'f2': '1'}) == (False, 'f3: is missing')
    assert rune.are_restrictions_met({'f2': '2'}) == (False, 'f3: is missing')
    assert rune.are_restrictions_met({'f3': '2'}) == (False, 'f3: <= 2')
    assert rune.are_restrictions_met({'f3': '3'}) == (True, '')
    assert (rune.are_restrictions_met({'f1': '1', 'f2': 'x', 'f3': 3})
            == (False, 'f1: is present AND f2: != 2'))
    assert (rune.are_restrictions_met({'f2': '1', 'f3': 2})
            == (False, 'f3: <= 2'))
    assert (rune.are_restrictions_met({'f2': '2', 'f3': 2})
            == (False, 'f3: <= 2'))
    assert rune.are_restrictions_met({'f2': '1', 'f3': 3}) == (True, '')
    assert rune.are_restrictions_met({'f2': '2', 'f3': 4}) == (True, '')


def test_rune_fromstring_norestrictions():
    rune = runes.Rune.from_base64('-YpZTBZ4Tb5SsUz3XIukxBx'
                                  'R619iEthm9oNJnC0LxZM=')
    assert rune.restrictions == []


def test_copy():
    """Make sure copies get their own sha state, as it corresponds to the restrictions list, which *is* copied"""
    mr = runes.MasterRune(bytes(16))
    state = mr.shaobj.state

    # .copy() and copy module should work the same.
    for mrune in (mr.copy(), copy.copy(mr), copy.deepcopy(mr)):
        restriction = runes.Restriction([runes.Alternative('f1', '=', 'v1')])
        mrune.add_restriction(restriction)
        assert mrune.shaobj.state != state
        assert mr.shaobj.state == state

    # Should work on normal runes, as well.
    orig = runes.Rune.from_base64(mr.to_base64())
    state = orig.shaobj.state
    for rune in (orig.copy(), copy.copy(orig), copy.deepcopy(orig)):
        restriction = runes.Restriction([runes.Alternative('f1', '=', 'v1')])
        rune.add_restriction(restriction)
        assert rune.shaobj.state != state
        assert orig.shaobj.state == state


def test_rune_tostring():
    alt1 = runes.Alternative('f1', '!', '')
    alt2 = runes.Alternative('f2', '=', '2')
    alt3 = runes.Alternative('f3', '>', '2')

    # Either can be true
    restr1 = runes.Restriction((alt1, alt2))
    restr2 = runes.Restriction((alt3,))

    rune = runes.MasterRune(bytes([1] * 32), [restr1, restr2])
    runestr = rune.to_base64()
    rune2 = runes.Rune.from_base64(runestr)

    assert rune == rune2
