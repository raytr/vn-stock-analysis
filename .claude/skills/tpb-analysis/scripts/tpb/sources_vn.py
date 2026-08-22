"""Nguồn dữ liệu Việt Nam: Entrade (DNSE) và CafeF.

Entrade  — OHLCV cổ phiếu, VN-Index, VN30, có lịch sử.
CafeF    — ảnh chụp chỉ số kèm giá trị giao dịch.

Cả hai đều là API công khai, không cần khoá. Các nguồn khác đã bị loại sau
khi kiểm chứng: TCBS bị Cloudflare chặn (403), VNDirect 406/timeout,
Simplize 404, Fireant 401 đòi auth.
"""
import datetime as dt
import json
import ssl
import time
import urllib.request

from .units import entrade_to_vnd

# không bao giờ tắt xác thực chứng chỉ — script cũ có nhánh CERT_NONE, đã loại
_CTX = ssl.create_default_context()
_UA = {
    "User-Agent": ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                   "AppleWebKit/537.36 (KHTML, like Gecko) "
                   "Chrome/120.0 Safari/537.36"),
    "Accept": "application/json, text/plain, */*",
}

ENTRADE = "https://services.entrade.com.vn/chart-api/v2/ohlcs"


def _get_json(url, referer=None, timeout=25):
    headers = dict(_UA)
    if referer:
        headers["Referer"] = referer
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout, context=_CTX) as resp:
        return json.loads(resp.read().decode("utf-8", "replace"))


def parse_entrade(payload):
    """Payload Entrade -> {dates, closes(VND int), raw_closes, volumes}.

    `closes` dùng cho cổ phiếu (quy về VND nguyên).
    `raw_closes` dùng cho chỉ số, vì VN-Index là điểm số chứ không phải giá.
    """
    if not payload or not payload.get("t"):
        return None
    return {
        "dates": [dt.datetime.utcfromtimestamp(t).strftime("%Y-%m-%d")
                  for t in payload["t"]],
        "closes": [entrade_to_vnd(c) for c in payload["c"]],
        "raw_closes": [float(c) for c in payload["c"]],
        "volumes": [int(v) for v in payload.get("v", [])],
    }


def fetch_entrade(symbol, days=400, kind="stock"):
    """kind='stock' cho cổ phiếu, kind='index' cho VNINDEX/VN30. Lỗi -> None."""
    now = int(time.time())
    url = (f"{ENTRADE}/{kind}?from={now - days * 86400}&to={now}"
           f"&symbol={symbol}&resolution=1D")
    try:
        return parse_entrade(_get_json(url))
    except Exception:
        return None


CAFEF_INDICES = "https://banggia.cafef.vn/stockhandler.ashx?index=true"


def _num(text):
    """'1,734.24' -> 1734.24 ; '' -> None"""
    if text is None:
        return None
    cleaned = str(text).replace(",", "").strip()
    if not cleaned:
        return None
    try:
        return float(cleaned)
    except ValueError:
        return None


def parse_cafef_indices(rows):
    """Danh sách chỉ số CafeF -> dict theo tên. Rỗng -> None."""
    if not rows:
        return None
    out = {}
    for row in rows:
        name = row.get("name")
        if not name:
            continue
        volume = _num(row.get("volume"))
        out[name] = {
            "value": _num(row.get("index")),
            "change": _num(row.get("change")),
            "change_pct": _num(row.get("percent")),
            "volume": int(volume) if volume is not None else None,
            "value_bn": _num(row.get("value")),
        }
    return out or None


def fetch_cafef_indices():
    """Ảnh chụp VN-Index / VN30 / HNX / UPCoM. Lỗi -> None (không chặn luồng)."""
    try:
        return parse_cafef_indices(
            _get_json(CAFEF_INDICES, referer="https://banggia.cafef.vn/"))
    except Exception:
        return None
