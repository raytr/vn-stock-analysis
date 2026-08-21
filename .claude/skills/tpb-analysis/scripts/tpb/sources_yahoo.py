"""Yahoo Finance — chỉ dùng cho chỉ số cơ bản của ngành ngân hàng.

Không nguồn Việt Nam nào cung cấp P/B và ROE mà không cần auth (TCBS bị
Cloudflare chặn, VNDirect 406/timeout, Simplize 404, Fireant 401). Toàn bộ
dữ liệu giá và chỉ số thị trường lấy từ nguồn Việt Nam, không qua đây.
"""
import statistics

from .units import yahoo_to_vnd

# 22 ngân hàng niêm yết lấy được dữ liệu, kiểm chứng ngày 2026-08-21
BANKS = ["VCB", "BID", "CTG", "TCB", "VPB", "MBB", "ACB", "HDB", "STB", "TPB",
         "VIB", "SHB", "LPB", "MSB", "OCB", "EIB", "SSB", "NAB", "KLB", "VAB",
         "BVB", "VBB"]


def extract_fundamentals(info):
    """dict `.info` của yfinance -> chỉ số cơ bản. Thiếu thì None, không bịa."""
    info = info or {}
    pb = info.get("priceToBook")
    roe = info.get("returnOnEquity")
    pb_per_roe = None
    if pb is not None and roe:        # roe = 0 cũng bị loại, tránh chia cho 0
        pb_per_roe = pb / (roe * 100.0)
    return {
        "price": yahoo_to_vnd(info.get("currentPrice")
                              or info.get("regularMarketPrice")),
        "pb": pb,
        "roe": roe,
        "pe": info.get("trailingPE"),
        "book_value": yahoo_to_vnd(info.get("bookValue")),
        "eps": yahoo_to_vnd(info.get("trailingEps")),
        "analyst_target": yahoo_to_vnd(info.get("targetMeanPrice")),
        "analyst_count": info.get("numberOfAnalystOpinions"),
        "market_cap": info.get("marketCap"),
        "pb_per_roe": pb_per_roe,
    }


def sector_stats(peers):
    """Trung vị ngành và xếp hạng theo P/B÷ROE. Mã thiếu dữ liệu bị loại.

    Xếp hạng 1 = rẻ nhất trên mỗi điểm ROE. Khung bắt buộc nêu ra mã nào rẻ
    hơn TPB thay vì giấu đi.
    """
    usable = [p for p in peers if p.get("pb") and p.get("pb_per_roe")]
    if not usable:
        return {"n": 0, "median_pb": None, "median_roe": None,
                "median_pb_per_roe": None, "rank_pb_per_roe": {}}
    ordered = sorted(usable, key=lambda p: p["pb_per_roe"])
    roes = [p["roe"] for p in usable if p.get("roe")]
    return {
        "n": len(usable),
        "median_pb": round(statistics.median([p["pb"] for p in usable]), 4),
        "median_roe": round(statistics.median(roes), 4) if roes else None,
        "median_pb_per_roe": round(statistics.median(
            [p["pb_per_roe"] for p in usable]), 4),
        "rank_pb_per_roe": {p["code"]: i + 1 for i, p in enumerate(ordered)},
    }


def fetch_bank(code):
    """Chỉ số cơ bản một ngân hàng. Lỗi -> None."""
    try:
        import yfinance as yf
        info = yf.Ticker(f"{code}.VN").info
    except Exception:
        return None
    out = extract_fundamentals(info)
    out["code"] = code
    return out


def fetch_sector(codes=None):
    """Quét toàn ngành. Mã nào hỏng thì bỏ qua, không làm chết cả lượt."""
    results = []
    for code in (codes or BANKS):
        row = fetch_bank(code)
        if row:
            results.append(row)
    return results
