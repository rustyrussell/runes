import base64
import copy
import hashlib
import runes
import pytest
import sha256  # type: ignore
import string
from typing import Sequence

# We save these in a file for other implementations to test against!
# e.g. PYTHONPATH=`pwd`/runes python3 ./tests/test_vectors.py > tests/test_vectors.csv
def gen_vectors():
    # Rune with 16x0 secret.
    secret = bytes(16)
    mr = runes.MasterRune(secret)

    # Simplest case
    print("VALID,empty rune (secret = [0]*16),{},{}".format(mr.to_str(), mr.to_base64()))
    print("PASS")
    print("PASS,f1=1")
    print("PASS,f1=var")
    print("PASS,f1=\\|\\&\\\\")

    # Rune with unique id.
    rune = runes.Rune(mr.authcode(), unique_id=1)
    print("VALID,unique id 1,{},{},1".format(rune.to_str(), rune.to_base64()))

    # Rune with unique id and version.
    rune = runes.Rune(mr.authcode(), unique_id=2, version=1)
    print("VALID,unique id 2 version 1,{},{},2,1".format(rune.to_str(), rune.to_base64()))

    # Single ops.
    rune = runes.Rune(mr.authcode())
    rune.add_restriction(runes.Restriction.from_str('f1!'))
    print("VALID,f1 is missing,{},{}".format(rune.to_str(), rune.to_base64()))
    print("PASS")
    print("PASS,f2=f1")
    print("FAIL,f1=1")
    print("FAIL,f1=var")

    rune = runes.Rune(mr.authcode())
    rune.add_restriction(runes.Restriction.from_str('f1=v1'))
    print("VALID,f1 equals v1,{},{}".format(rune.to_str(), rune.to_base64()))
    print("PASS,f1=v1")
    print("FAIL,f1=v")
    print("FAIL,f1=v1a")
    print("FAIL")
    print("FAIL,f2=f1")

    # / ^ $ ^ < > { }
    rune = runes.Rune(mr.authcode())
    rune.add_restriction(runes.Restriction.from_str('f1/v1'))
    print("VALID,f1 not equal v1,{},{}".format(rune.to_str(), rune.to_base64()))
    print("PASS,f1=v2")
    print("PASS,f1=v")
    print("PASS,f1=v1a")
    print("FAIL")
    print("FAIL,f2=v1")

    rune = runes.Rune(mr.authcode())
    rune.add_restriction(runes.Restriction.from_str('f1$v1'))
    print("VALID,f1 ends with v1,{},{}".format(rune.to_str(), rune.to_base64()))
    print("PASS,f1=v1")
    print("PASS,f1=2v1")
    print("FAIL,f1=v1a")
    print("FAIL")

    rune = runes.Rune(mr.authcode())
    rune.add_restriction(runes.Restriction.from_str('f1^v1'))
    print("VALID,f1 starts with v1,{},{}".format(rune.to_str(), rune.to_base64()))
    print("PASS,f1=v1")
    print("PASS,f1=v1a")
    print("FAIL,f1=2v1")
    print("FAIL")

    rune = runes.Rune(mr.authcode())
    rune.add_restriction(runes.Restriction.from_str('f1~v1'))
    print("VALID,f1 contains v1,{},{}".format(rune.to_str(), rune.to_base64()))
    print("PASS,f1=v1")
    print("PASS,f1=v1a")
    print("PASS,f1=2v1")
    print("PASS,f1=2v12")
    print("FAIL,f1=1v2")
    print("FAIL")

    # Invalid to compare against a non-int
    rune = runes.Rune(mr.authcode())
    rune.add_restriction(runes.Restriction.from_str('f1<v1'))
    print("VALID,f1 less than v1,{},{}".format(rune.to_str(), rune.to_base64()))
    print("FAIL,f1=1")
    print("FAIL,f1=2")
    print("FAIL,f1=v1")
    print("FAIL")

    rune = runes.Rune(mr.authcode())
    rune.add_restriction(runes.Restriction.from_str('f1<1'))
    print("VALID,f1 less than 1,{},{}".format(rune.to_str(), rune.to_base64()))
    print("PASS,f1=0")
    print("PASS,f1=-10000")
    print("FAIL,f1=1")
    print("FAIL,f1=10000")
    print("FAIL,f1=v1")
    print("FAIL")

    # Invalid to compare against a non-int
    rune = runes.Rune(mr.authcode())
    rune.add_restriction(runes.Restriction.from_str('f1>v1'))
    print("VALID,f1 greater than v1,{},{}".format(rune.to_str(), rune.to_base64()))
    print("FAIL,f1=1")
    print("FAIL,f1=2")
    print("FAIL,f1=v1")
    print("FAIL")

    rune = runes.Rune(mr.authcode())
    rune.add_restriction(runes.Restriction.from_str('f1>1'))
    print("VALID,f1 greater than 1,{},{}".format(rune.to_str(), rune.to_base64()))
    print("PASS,f1=2")
    print("PASS,f1=10000")
    print("FAIL,f1=1")
    print("FAIL,f1=-10000")
    print("FAIL,f1=0")
    print("FAIL,f1=v1")
    print("FAIL")

    rune = runes.Rune(mr.authcode())
    rune.add_restriction(runes.Restriction.from_str('f1{11'))
    print("VALID,f1 sorts before 11,{},{}".format(rune.to_str(), rune.to_base64()))
    print("PASS,f1=0")
    print("PASS,f1=1")
    print("PASS,f1=\t")
    print("PASS,f1=/")
    print("FAIL,f1=11")
    print("FAIL,f1=111")
    print("FAIL,f1=v1")
    print("FAIL,f1=:")
    print("FAIL")

    rune = runes.Rune(mr.authcode())
    rune.add_restriction(runes.Restriction.from_str('f1}11'))
    print("VALID,f1 sorts after 11,{},{}".format(rune.to_str(), rune.to_base64()))
    print("PASS,f1=111")
    print("PASS,f1=v1")
    print("PASS,f1=:")
    print("FAIL,f1=0")
    print("FAIL,f1=1")
    print("FAIL,f1=\t")
    print("FAIL,f1=/")
    print("FAIL,f1=11")
    print("FAIL")

    rune = runes.Rune(mr.authcode())
    rune.add_restriction(runes.Restriction.from_str('f1#11'))
    print("VALID,f1 sorts after 11,{},{}".format(rune.to_str(), rune.to_base64()))
    print("PASS,f1=111")
    print("PASS,f1=v1")
    print("PASS,f1=:")
    print("PASS,f1=0")
    print("PASS,f1=1")
    print("PASS,f1=\t")
    print("PASS,f1=/")
    print("PASS,f1=11")
    print("PASS")

    # Alternatives: any one can match.
    rune = runes.Rune(mr.authcode())
    rune.add_restriction(runes.Restriction.from_str('f1=1|f2=3'))
    print("VALID,f1=1 or f2=3,{},{}".format(rune.to_str(), rune.to_base64()))
    print("PASS,f1=1")
    print("PASS,f1=1,f2=2")
    print("PASS,f2=3")
    print("PASS,f1=var,f2=3")
    print("PASS,f1=1,f2=3")
    print("FAIL")
    print("FAIL,f1=2")
    print("FAIL,f1=f1")
    print("FAIL,f2=1")
    print("FAIL,f2=f1")

    # Multiple conditions: all must match!
    rune = runes.Rune(mr.authcode())
    rune.add_restriction(runes.Restriction.from_str('f1=1|f2=3'))
    rune.add_restriction(runes.Restriction.from_str('f3~v1'))
    print("VALID,f1=1 or f2=3 AND f3 contains v1,{},{}".format(rune.to_str(), rune.to_base64()))
    print("PASS,f1=1,f3=v1")
    print("PASS,f2=3,f3=v1x")
    print("FAIL")
    print("FAIL,f1=1")
    print("FAIL,f2=3")
    print("FAIL,f1=1,f2=3")
    print("FAIL,f1=2,f3=v1")
    print("FAIL,f2=2,f3=v1")
    print("FAIL,f3=v1")

    # unique-id has to be of form =<str>[-<str>]
    for cond in '!/^$~<>}{':
        rune = runes.Rune(mr.authcode(), unique_id=1)
        rune.restrictions[0].alternatives[0].cond = cond
        print("MALFORMED,unique id must use = not {},{},{}".format(cond, rune.to_str(), rune.to_base64()))

    # You cannot override unique id or version by specifying later!
    rune = runes.Rune(mr.authcode(), unique_id=1, version=2)
    rune.add_restriction(runes.Restriction.decode('=3', allow_idfield=True)[0])
    print("MALFORMED,unique id cannot be overridden,{},{}".format(rune.to_str(), rune.to_base64()))

    rune = runes.Rune(mr.authcode(), unique_id=1, version=2)
    rune.add_restriction(runes.Restriction.decode('=1-3', allow_idfield=True)[0])
    print("MALFORMED,version cannot be overridden,{},{}".format(rune.to_str(), rune.to_base64()))

    # These conditions are reserved for future
    rune = runes.Rune(mr.authcode())
    rune.add_restriction(runes.Restriction.from_str('f1#11'))
    for cond in '"&\'()*+-.:;?[\\]_`|':
        rune.restrictions[0].alternatives[0].cond = cond
        print("MALFORMED,Bad condition {},{},{}"
              .format(cond, rune.to_str(), rune.to_base64()))

    # Bad hash value (flip one bit!)
    rune = runes.Rune(mr.authcode())
    rune.add_restriction(runes.Restriction.from_str('f1#11'))
    oldbytes = rune.shaobj.state[0]
    rune.shaobj.state = (oldbytes[:-1] + bytes([int(oldbytes[-1]) ^ 1]),
                         rune.shaobj.state[1])
    print("BAD DERIVATION,Incremented sha,{},{}"
              .format(rune.to_str(), rune.to_base64()))
    rune.shaobj.state = (oldbytes, rune.shaobj.state[1])

    # Add condition, don't update authcode
    oldauth = rune.shaobj.state
    rune.add_restriction(runes.Restriction([runes.Restriction.from_str('a=1')]))
    rune.shaobj.state = oldauth
    print("BAD DERIVATION,Unchanged sha,{},{}"
              .format(rune.to_str(), rune.to_base64()))


def test_vectors():
    with open("tests/test_vectors.csv", "r") as f:
        vecs = [line.rstrip('\n').split(',') for line in f.readlines()]

    mr = runes.MasterRune(bytes(16))
    for v in vecs:
        if v[0] == 'VALID':
            print(v[1])
            rune1 = runes.Rune.from_str(v[2])
            rune2 = runes.Rune.from_base64(v[3])
            assert rune1 == rune2
            assert mr.is_rune_authorized(rune1)
            assert mr.is_rune_authorized(rune2)
            if len(v) == 6:
                assert rune1.restrictions[0].alternatives[0].encode() == '={}-{}'.format(v[4], v[5])
            elif len(v) == 5:
                assert rune1.restrictions[0].alternatives[0].encode() == '={}'.format(v[4])
            else:
                # Must not have ID field
                assert len(v) == 4
                assert len(rune1.restrictions) == 0 or not rune1.restrictions[0].alternatives[0].encode().startswith('=')
        elif v[0] == 'MALFORMED':
            print(v[1])
            # Try to ensure we complain about right problem
            errmsg = 'cond not valid'
            if "unique id" in v[1] or "version" in v[1]:
                errmsg = 'unique_id'
            with pytest.raises(ValueError, match=errmsg):
                rune1 = runes.Rune.from_str(v[2])
            with pytest.raises(ValueError, match=errmsg):
                rune2 = runes.Rune.from_base64(v[3])
        elif v[0] == 'BAD DERIVATION':
            print(v[1])
            rune1 = runes.Rune.from_str(v[2])
            rune2 = runes.Rune.from_base64(v[3])
            assert rune1 == rune2
            assert not mr.is_rune_authorized(rune1)
            assert not mr.is_rune_authorized(rune2)
        else:
            assert v[0] == 'PASS' or v[0] == 'FAIL'
            variables = {}
            for var in v[1:]:
                parts = var.partition('=')
                variables[parts[0]] = parts[2]
            assert rune1.are_restrictions_met(variables)[0] == (v[0] == 'PASS')
            assert rune2.are_restrictions_met(variables)[0] == (v[0] == 'PASS')


if __name__ == "__main__":
    gen_vectors()
