"""Pytest collects only test_*.py (see pytest.ini).

Shim that exposes legacy `animals/tests.py` tests.
"""

from . import tests as legacy_tests


class TestAnimals(legacy_tests.AnimalsSmokeTests):
    pass
