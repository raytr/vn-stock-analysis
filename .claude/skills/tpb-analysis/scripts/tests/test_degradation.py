from push_to_sheet import format_manual, push

ROW = {"date": "2026-08-21", "close": 14500, "volume": "6,285,000",
       "signal": "GIỮ", "confidence": "TB", "reason": "P/B 0,88",
       "levels": "HT 14.300", "next_step": "nếu vượt 15.294 thì...",
       "review": "Chưa rõ"}


def test_missing_webhook_returns_manual_instead_of_raising():
    out = push(ROW, webhook=None, token=None)
    assert out["ok"] is False
    assert out["mode"] == "manual"
    assert "2026-08-21" in out["manual"]


def test_manual_line_is_tab_separated_for_pasting():
    line = format_manual(ROW)
    assert line.count("\t") == 8      # 9 cột -> 8 dấu tab
    assert line.startswith("2026-08-21")


def test_unreachable_webhook_degrades_not_crashes():
    out = push(ROW, webhook="https://127.0.0.1:9/nope", token="x")
    assert out["ok"] is False and out["mode"] == "manual"
