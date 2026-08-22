from tpb.indicators import flag_limit_breaks

DATES = ["2026-08-17", "2026-08-18", "2026-08-19", "2026-08-20"]


def test_flags_move_beyond_hose_band():
    # 10000 -> 9000 là -10%, bất khả thi trong một phiên HOSE bình thường
    flags = flag_limit_breaks(DATES, [10000, 9000, 9000, 9000])
    assert len(flags) == 1
    assert flags[0]["date"] == "2026-08-18"
    assert flags[0]["change_pct"] == -10.0


def test_ignores_move_inside_the_band():
    # -6.9% là biến động thị trường hợp lệ, không được gắn cờ
    flags = flag_limit_breaks(DATES, [10000, 9310, 9310, 9310])
    assert flags == []


def test_flags_upside_break_too():
    flags = flag_limit_breaks(DATES, [10000, 10800, 10800, 10800])
    assert len(flags) == 1
    assert flags[0]["change_pct"] == 8.0


def test_empty_series_is_safe():
    assert flag_limit_breaks([], []) == []


def test_zero_previous_close_does_not_divide_by_zero():
    assert flag_limit_breaks(DATES, [0, 9000, 9000, 9000]) == []
