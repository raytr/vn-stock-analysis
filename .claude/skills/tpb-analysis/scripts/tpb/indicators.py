"""Chỉ báo kỹ thuật, thuần Python, không phụ thuộc pandas.

Toàn bộ chỉ báo tính trên chuỗi của MỘT nguồn duy nhất. Trộn chuỗi của hai
nhà cung cấp sẽ tạo ra biến động không có thật tại các mốc sự kiện quyền —
đo thực tế cho thấy Entrade và Yahoo lệch tới 7,82% ở 32/343 phiên.
"""

from .units import HOSE_LIMIT_PCT


def ema(values, span):
    """Trung bình động luỹ thừa. Phần tử đầu lấy chính giá trị đầu làm mầm."""
    if not values:
        return []
    k = 2.0 / (span + 1)
    acc = float(values[0])
    out = [acc]
    for v in values[1:]:
        acc = float(v) * k + acc * (1 - k)
        out.append(acc)
    return out


def sma(values, window):
    """Trung bình động giản đơn của `window` phần tử cuối."""
    if len(values) < window:
        return None
    return sum(float(v) for v in values[-window:]) / window


def rsi(closes, period=14):
    """RSI theo phương pháp làm mượt Wilder."""
    if len(closes) < period + 1:
        return None
    gains, losses = [], []
    for prev, cur in zip(closes, closes[1:]):
        d = float(cur) - float(prev)
        gains.append(max(d, 0.0))
        losses.append(max(-d, 0.0))
    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period
    for g, l in zip(gains[period:], losses[period:]):
        avg_gain = (avg_gain * (period - 1) + g) / period
        avg_loss = (avg_loss * (period - 1) + l) / period
    if avg_loss == 0:
        return 100.0 if avg_gain > 0 else 50.0
    rs = avg_gain / avg_loss
    return 100.0 - 100.0 / (1.0 + rs)


def macd(closes, fast=12, slow=26, signal=9):
    """MACD 12/26/9. Trả về dict rỗng-an-toàn nếu chuỗi quá ngắn."""
    if len(closes) < slow:
        return {"macd": None, "signal": None, "hist": None}
    fast_line = ema(closes, fast)
    slow_line = ema(closes, slow)
    macd_series = [f - s for f, s in zip(fast_line, slow_line)]
    signal_series = ema(macd_series, signal)
    m, s = macd_series[-1], signal_series[-1]
    return {"macd": m, "signal": s, "hist": m - s}


def flag_limit_breaks(dates, closes, limit=HOSE_LIMIT_PCT):
    """Tìm các phiên có biến động đóng-cửa-sang-đóng-cửa vượt biên độ sàn.

    Vượt biên độ nghĩa là sự kiện quyền hoặc lỗi dữ liệu, KHÔNG phải tín hiệu
    thị trường. Bằng chứng: TPB có 4 phiên như vậy trong 500 phiên gần nhất,
    trong đó 08/09/2025 giảm đúng -10,00% — bất khả thi trong phiên bình thường.
    """
    flags = []
    for i in range(1, len(closes)):
        prev = float(closes[i - 1])
        if prev == 0:
            continue
        change = (float(closes[i]) - prev) / prev * 100.0
        if abs(change) > limit:
            flags.append({"date": dates[i], "change_pct": round(change, 2)})
    return flags
