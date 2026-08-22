from push_to_sheet import build_row

FULL = dict(date="2026-08-21", close=14500, volume="6,285,000 (81% TB20)",
            signal="GIỮ", confidence="TB",
            reason="P/B 0,88 vs trung vị ngành 1,10",
            levels="HT 14.300 / KC 15.294 / CL 13.700",
            next_step="nếu đóng cửa trên 15.294 thì xem xét gia tăng",
            review="Đúng — nhận định 5 phiên trước về vùng hỗ trợ đã đúng")


def test_row_has_exactly_the_writable_columns():
    row = build_row(**FULL)
    assert list(row.keys()) == ["date", "close", "volume", "signal",
                                "confidence", "reason", "levels",
                                "next_step", "review"]


def test_row_never_contains_holding_or_pl_columns():
    # cột L, M là của người dùng; cột J là công thức — skill không được đụng
    row = build_row(**FULL)
    for forbidden in ("holding_avg", "holding_volume", "pl"):
        assert forbidden not in row


def test_non_trading_day_uses_dash_and_blanks():
    row = build_row(date="2026-08-22", close=None, volume=None, signal=None,
                    confidence=None, reason=None, levels=None,
                    next_step=None, review=None)
    assert row["close"] == "—"
    assert row["signal"] == ""
