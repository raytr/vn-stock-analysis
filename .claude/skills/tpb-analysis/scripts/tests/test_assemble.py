from tpb.assemble import cross_check, rel_strength


def test_cross_check_passes_when_sources_agree():
    out = cross_check(14500, 14500)
    assert out["ok"] is True and out["diff_pct"] == 0.0


def test_cross_check_fails_beyond_two_percent():
    out = cross_check(14500, 13000)   # lệch ~11,5%
    assert out["ok"] is False
    assert out["diff_pct"] > 2.0


def test_cross_check_tolerates_small_gap():
    assert cross_check(14500, 14400)["ok"] is True   # 0,69%


def test_cross_check_missing_source_is_not_a_failure():
    out = cross_check(14500, None)
    assert out["ok"] is True and out["diff_pct"] is None


def test_rel_strength_zero_when_stock_matches_market():
    stock = [100, 110]
    index = [1000, 1100]        # cả hai +10%
    assert round(rel_strength(stock, index, window=1), 6) == 0.0


def test_rel_strength_negative_when_stock_lags():
    stock = [100, 105]
    index = [1000, 1100]        # +5% so với +10%
    assert round(rel_strength(stock, index, window=1), 2) == -5.0


def test_rel_strength_none_when_history_too_short():
    assert rel_strength([100], [1000], window=20) is None
