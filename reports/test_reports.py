from . import tests as legacy_tests


class TestReports(legacy_tests.ReportsSmokeTests):
    """Pytest collects only test_*.py (see pytest.ini).

    Shim that exposes legacy `reports/tests.py` tests without double-collecting.
    """

    pass
