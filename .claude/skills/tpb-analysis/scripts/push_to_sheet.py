#!/usr/bin/env python3
"""push_to_sheet.py — đẩy một dòng nhật ký lên Google Sheet qua Apps Script.

Module này không biết gì về chứng khoán. Nó chỉ chuyển một dòng đi.

Không có webhook thì KHÔNG crash: in ra dòng đã format sẵn để dán tay.
Secret không nằm trong repo — truyền qua tham số hoặc biến môi trường,
nguồn gốc là prompt chạy trên Claude Cloud.
"""
import argparse
import json
import os
import ssl
import sys
import urllib.request

_CTX = ssl.create_default_context()

# đúng thứ tự cột B..I trong sheet, phải khớp mảng FIELDS trong Code.gs
COLUMNS = ["date", "close", "volume", "signal", "confidence",
           "reason", "levels", "next_step", "review"]


def build_row(date, close=None, volume=None, signal=None, confidence=None,
              reason=None, levels=None, next_step=None, review=None):
    """Dựng đúng các trường ghi được. Ngày nghỉ: close='—', còn lại rỗng."""
    return {
        "date": date,
        "close": close if close is not None else "—",
        "volume": volume or "",
        "signal": signal or "",
        "confidence": confidence or "",
        "reason": reason or "",
        "levels": levels or "",
        "next_step": next_step or "",
        "review": review or "",
    }


def format_manual(row):
    """Dòng ngăn cách bằng tab, dán thẳng vào sheet được."""
    return "\t".join(str(row.get(c, "")) for c in COLUMNS)


def push(row, webhook, token):
    """POST lên Apps Script. Thiếu webhook hoặc lỗi mạng -> chế độ dán tay."""
    if not webhook or not token:
        return {"ok": False, "mode": "manual", "manual": format_manual(row),
                "reason": "chưa cấu hình SHEET_WEBHOOK/SHEET_TOKEN"}
    body = json.dumps({"token": token, **row}).encode("utf-8")
    req = urllib.request.Request(
        webhook, data=body, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=30, context=_CTX) as resp:
            result = json.loads(resp.read().decode("utf-8", "replace"))
    except Exception as exc:
        return {"ok": False, "mode": "manual", "manual": format_manual(row),
                "reason": f"{type(exc).__name__}: {exc}"}
    if not result.get("ok"):
        return {"ok": False, "mode": "manual", "manual": format_manual(row),
                "reason": result.get("error", "apps script từ chối")}
    return {"ok": True, "mode": "webhook", "row": result.get("row")}


def main():
    ap = argparse.ArgumentParser(description="Đẩy một dòng lên Google Sheet")
    for col in COLUMNS:
        ap.add_argument(f"--{col.replace('_', '-')}", default=None)
    ap.add_argument("--webhook", default=os.environ.get("SHEET_WEBHOOK"))
    ap.add_argument("--token", default=os.environ.get("SHEET_TOKEN"))
    args = ap.parse_args()

    if not args.date:
        print("Lỗi: thiếu --date", file=sys.stderr)
        sys.exit(2)

    row = build_row(**{c: getattr(args, c) for c in COLUMNS})
    result = push(row, args.webhook, args.token)
    if result["ok"]:
        print(f"✅ Đã ghi vào sheet, dòng {result['row']}")
    else:
        print(f"⚠️  CHƯA ghi được ({result['reason']}). Dán tay dòng sau:",
              file=sys.stderr)
        print(result["manual"])
    # luôn thoát 0 — không ghi được sheet không phải lỗi của phần phân tích
    sys.exit(0)


if __name__ == "__main__":
    main()
