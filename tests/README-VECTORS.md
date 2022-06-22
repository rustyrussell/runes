# Runes - Test Vectors

The test vectors are a simple CSV file, with several different lines.
They are all derived from the initial master rune, created with a
secret which is simply 16 bytes of zero.

* `VALID`,description,str,base64str
    - This is a valid rune, encoded as a string and as base64.
	- It should be a valid derivation of the master rune.
* `PASS`[,variables...]
    - Interpreting any variables of form "var=str" as a set of values, this
	  should pass the rune conditions of the previous VALID rune.
* `FAIL`[,variables...]
    - Interpreting any variables of form "var=str" as a set of values, this
	  should fail the rune conditions of the previous VALID rune.
* `MALFORMED`,description,str,base64str
    - This rune is malformed and should not parse.
* `BAD DERIVATION`,description,str,base64str
    - This rune does not correctly derive from the master rune.

You can regenerate the test vectors by running:

    PYTHONPATH=`pwd`/runes python3 ./tests/test_vectors.py

Cheers!
Rusty.
