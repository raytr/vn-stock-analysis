from tpb.units import entrade_to_vnd, yahoo_to_vnd, HOSE_LIMIT_PCT


def test_entrade_thousands_to_vnd():
    assert entrade_to_vnd(14.5) == 14500
    assert entrade_to_vnd(6.9) == 6900


def test_yahoo_already_vnd():
    assert yahoo_to_vnd(14500.0) == 14500


def test_two_sources_agree_after_normalisation():
    # đây chính là lỗi đã giết script cũ: 14.5 và 14500 là cùng một giá
    assert entrade_to_vnd(14.5) == yahoo_to_vnd(14500.0)


def test_always_int_never_float():
    assert isinstance(entrade_to_vnd(14.5), int)
    assert isinstance(yahoo_to_vnd(14500.0), int)


def test_none_passes_through():
    assert entrade_to_vnd(None) is None
    assert yahoo_to_vnd(None) is None


def test_hose_limit_is_seven_percent():
    assert HOSE_LIMIT_PCT == 7.0
