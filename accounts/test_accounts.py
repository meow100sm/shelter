from . import tests as legacy_tests


class TestAccounts(legacy_tests.AccountsSmokeTests):
    """Pytest collects only test_*.py (see pytest.ini).

    Shim that exposes legacy `accounts/tests.py` tests without double-collecting.
    """

    pass
