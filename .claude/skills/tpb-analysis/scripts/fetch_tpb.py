#!/usr/bin/env python3
"""fetch_tpb.py — thu thập số liệu TPB, in ra một object JSON trên stdout.

Đây là toàn bộ phần "tính toán" của skill. Claude đọc JSON này và chỉ diễn
giải; Claude KHÔNG tính thêm bất kỳ con số nào.

Script này không có credential Google nên không tự đọc sheet được. Vị thế do
Claude đọc từ sheet rồi truyền vào qua tham số.

    python3 fetch_tpb.py
    python3 fetch_tpb.py --holding-avg 14200 --holding-volume 5000
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tpb.assemble import build                                    # noqa: E402
from tpb.sources_vn import fetch_cafef_indices, fetch_entrade     # noqa: E402
from tpb.sources_yahoo import fetch_bank, fetch_sector            # noqa: E402


def main():
    ap = argparse.ArgumentParser(description="Thu thập số liệu TPB")
    ap.add_argument("--holding-avg", type=int, default=None,
                    help="Giá vốn bình quân (VND), Claude đọc từ ô M1 của sheet")
    ap.add_argument("--holding-volume", type=int, default=None,
                    help="Số lượng đang nắm, Claude đọc từ ô M2 của sheet")
    ap.add_argument("--days", type=int, default=400)
    ap.add_argument("--no-sector", action="store_true",
                    help="Bỏ qua quét 22 ngân hàng (nhanh hơn, dùng khi debug)")
    args = ap.parse_args()

    ok, failed = [], []

    ohlcv = fetch_entrade("TPB", days=args.days)
    (ok if ohlcv else failed).append("entrade")
    if not ohlcv:
        print("[warn] không lấy được giá TPB từ Entrade", file=sys.stderr)

    index_raw = fetch_entrade("VNINDEX", days=args.days, kind="index")
    # chỉ số là điểm số, dùng raw_closes chứ không phải closes đã quy VND
    index_series = index_raw["raw_closes"] if index_raw else []

    indices = fetch_cafef_indices()
    (ok if indices else failed).append("cafef")

    fundamentals = fetch_bank("TPB")
    (ok if fundamentals else failed).append("yahoo")
    yahoo_close = fundamentals.get("price") if fundamentals else None

    peers = [] if args.no_sector else (fetch_sector() if fundamentals else [])

    if not ohlcv and not fundamentals:
        print("Lỗi: cả Entrade lẫn Yahoo đều không phản hồi. Dừng, không ghi gì.",
              file=sys.stderr)
        sys.exit(1)

    payload = build(
        ohlcv=ohlcv, fundamentals=fundamentals, peers=peers,
        indices=indices, index_series=index_series,
        position={"avg_price": args.holding_avg,
                  "volume": args.holding_volume},
        sources_ok=ok, sources_failed=failed, yahoo_close=yahoo_close,
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
