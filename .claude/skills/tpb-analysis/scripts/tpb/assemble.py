"""Ghép dữ liệu các nguồn thành đúng hợp đồng JSON ở mục 6 của spec.

Ranh giới: mọi con số dừng lại ở đây. Claude đọc JSON này và chỉ diễn giải,
không tính thêm số nào.
"""
import datetime as dt

from .indicators import flag_limit_breaks, macd, rsi, sma
from .sources_yahoo import sector_stats

CROSS_CHECK_TOL_PCT = 2.0


def cross_check(entrade_close, yahoo_close, tol_pct=CROSS_CHECK_TOL_PCT):
    """Đối chiếu CHỈ giá đóng cửa phiên gần nhất.

    Không quét toàn chuỗi: đo thực tế cho thấy 32/343 phiên lệch trên 2% tại
    các mốc sự kiện quyền, trong khi phiên gần nhất hai nguồn khớp tuyệt đối.
    Quét toàn chuỗi sẽ báo động giả liên tục.
    """
    if entrade_close is None or yahoo_close is None or not yahoo_close:
        return {"entrade": entrade_close, "yahoo": yahoo_close,
                "diff_pct": None, "ok": True}
    diff = abs(entrade_close - yahoo_close) / yahoo_close * 100.0
    return {"entrade": entrade_close, "yahoo": yahoo_close,
            "diff_pct": round(diff, 2), "ok": diff <= tol_pct}


def rel_strength(stock_closes, index_closes, window=20):
    """Hiệu suất cổ phiếu trừ hiệu suất chỉ số, tính theo `window` phiên.

    Trả lời: TPB yếu vì bản thân nó, hay vì cả thị trường đang yếu.
    """
    if len(stock_closes) <= window or len(index_closes) <= window:
        return None

    def pct(series):
        start, end = float(series[-1 - window]), float(series[-1])
        return None if start == 0 else (end - start) / start * 100.0

    a, b = pct(stock_closes), pct(index_closes)
    return None if a is None or b is None else a - b


def build(ohlcv, fundamentals, peers, indices, index_series, position=None,
          sources_ok=None, sources_failed=None, yahoo_close=None):
    """Dựng object JSON hoàn chỉnh. Trường nào thiếu thì để None, không bịa."""
    warnings = []
    closes = ohlcv["closes"] if ohlcv else []
    dates = ohlcv["dates"] if ohlcv else []
    volumes = ohlcv["volumes"] if ohlcv else []
    close = closes[-1] if closes else None

    breaks = flag_limit_breaks(dates, closes)
    if breaks:
        recent = [b["date"] for b in breaks[-3:]]
        warnings.append(
            f"{len(breaks)} phiên vượt biên độ ±7% — sự kiện quyền hoặc lỗi "
            f"dữ liệu, KHÔNG phải tín hiệu thị trường. Gần nhất: {recent}")

    xc = cross_check(close, yahoo_close)
    if not xc["ok"]:
        warnings.append(
            f"Hai nguồn giá lệch {xc['diff_pct']}% — hạ độ tin xuống Thấp")

    vol_avg20 = sma(volumes, 20) if volumes else None
    vol = volumes[-1] if volumes else None
    if vol and vol_avg20 and vol < vol_avg20 * 0.5:
        warnings.append(
            "KLGD dưới 50% trung bình 20 phiên — thanh khoản mỏng, "
            "hạ độ tin phần kỹ thuật")

    warnings.append("khối ngoại: chưa có nguồn tự động, để trống")

    m = macd(closes) if closes else {"macd": None, "signal": None, "hist": None}
    f = fundamentals or {}
    vn = (indices or {}).get("VNINDEX") or {}
    vn30 = (indices or {}).get("VN30") or {}

    pos = dict(position or {})
    if pos.get("avg_price") and pos.get("volume") and close:
        pos["unrealized_pl"] = int((close - pos["avg_price"]) * pos["volume"])
    else:
        pos.setdefault("avg_price", None)
        pos.setdefault("volume", None)
        pos["unrealized_pl"] = None

    rs = rel_strength(closes, index_series or []) if (closes and index_series) else None

    def _int(v):
        return int(v) if v is not None else None

    return {
        "meta": {
            "ticker": "TPB",
            "run_at": dt.datetime.now().astimezone().isoformat(timespec="seconds"),
            "session_date": dates[-1] if dates else None,
            "is_trading_day": bool(dates),
            "sources_ok": sources_ok or [],
            "sources_failed": sources_failed or [],
            "warnings": warnings,
            "limit_breaks": breaks,
        },
        "price": {
            "close": close,
            "volume": vol,
            "volume_avg20": _int(vol_avg20),
            "volume_ratio": round(vol / vol_avg20, 2) if vol and vol_avg20 else None,
            "high_52w": max(closes[-250:]) if closes else None,
            "low_52w": min(closes[-250:]) if closes else None,
            "cross_check": xc,
        },
        "technicals": {
            "rsi14": round(rsi(closes), 1) if closes and rsi(closes) is not None else None,
            "macd": m["macd"], "macd_signal": m["signal"], "macd_hist": m["hist"],
            "sma20": _int(sma(closes, 20)),
            "sma50": _int(sma(closes, 50)),
            "sma200": _int(sma(closes, 200)),
        },
        "valuation": {
            "pb": f.get("pb"), "roe": f.get("roe"), "pe": f.get("pe"),
            "book_value": f.get("book_value"),
            "analyst_target": f.get("analyst_target"),
            "analyst_count": f.get("analyst_count"),
            "pb_per_roe": f.get("pb_per_roe"),
            "sector": sector_stats(peers or []),
            "peers": peers or [],
        },
        "market": {
            "vnindex": vn or None,
            "vn30": vn30 or None,
            "tpb_rel_strength_20d": round(rs, 2) if rs is not None else None,
        },
        "foreign": None,
        "position": pos,
    }
