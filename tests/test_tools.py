import json
from tools import lookup, calculate

def test_lookup():
    assert "error" not in json.loads(lookup("Brightwater"))
    assert "error" in json.loads(lookup("NonexistentXYZ"))

def test_calculate():
    assert json.loads(calculate("48317 * 1.0947"))
    assert "error" in json.loads(calculate("10 / 0"))
    assert "error" in json.loads(calculate("__import__('os')"))
    assert "error" in json.loads(calculate("(1).__class__"))