"""Chuẩn hoá đơn vị giá. Mọi giá trong hệ thống là VND nguyên, kiểu int.

Entrade trả giá theo nghìn đồng (14.5), Yahoo trả VND nguyên (14500).
Quy đổi xảy ra đúng một lần, tại đây, không nơi nào khác.

Đây là lỗi đã giết script cũ: nó fetch trường `currency` rồi không dùng,
và in giá 69.000đ ra thành "$69000.00".
"""

HOSE_LIMIT_PCT = 7.0  # biên độ dao động một phiên của sàn HOSE


def entrade_to_vnd(value):
    """14.5 -> 14500. None đi xuyên qua."""
    if value is None:
        return None
    return int(round(float(value) * 1000))


def yahoo_to_vnd(value):
    """14500.0 -> 14500. None đi xuyên qua."""
    if value is None:
        return None
    return int(round(float(value)))
