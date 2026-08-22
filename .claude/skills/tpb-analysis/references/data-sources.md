# Nguồn dữ liệu

Toàn bộ đã kiểm chứng bằng request thật ngày 2026-08-21.

## Đang dùng

| Cần gì | Nguồn | Trạng thái |
|---|---|---|
| OHLCV lịch sử TPB | **Entrade (DNSE)** 🇻🇳 `/chart-api/v2/ohlcs/stock` | ✅ 273 phiên |
| VN-Index, VN30 lịch sử | **Entrade** 🇻🇳 `/ohlcs/index?symbol=VNINDEX\|VN30` | ✅ 273 phiên |
| Chỉ số realtime + GTGD | **CafeF** 🇻🇳 `stockhandler.ashx?index=true` | ✅ |
| P/B, ROE, book value, EPS, target — 22 ngân hàng | Yahoo qua `yfinance`, hậu tố `.VN` | ✅ |
| NIM, CASA, NPL, LLR, CIR, CAR | BCTC, đọc bằng WebSearch/WebFetch | thủ công |

Toàn bộ dữ liệu **giá và chỉ số thị trường** đến từ nguồn Việt Nam. Yahoo thu hẹp còn đúng
một việc: chỉ số cơ bản ngành ngân hàng — không nguồn Việt Nam nào thay được mà không cần auth.

## Đã loại, kèm lý do

| Nguồn | Lý do |
|---|---|
| TCBS | Cloudflare chặn bot, trả trang "Just a moment..." với mọi header |
| VNDirect | 406 và timeout |
| Simplize | 404 |
| Vietstock | 404, số liệu render bằng JS nên WebFetch cũng không đọc được |
| Fireant | 401, đòi auth |
| VN-Index trên Yahoo | không tồn tại — `^VNINDEX`, `^VN30`, `^VNI`, `VNINDEX.VN` đều 404 |
| VNM (VanEck Vietnam ETF) | niêm yết ở Mỹ, ngoài phạm vi |
| Alpha Vantage | không phủ sàn Việt Nam; chỉ báo kỹ thuật tự tính từ OHLCV chính xác hơn |

## Chuẩn hoá đơn vị

Entrade trả `14.5`, Yahoo trả `14500`, **cùng là 14.500 đồng**. Đây đúng loại lỗi đã giết hệ
thống cũ (in giá VND kèm ký hiệu `$`). Quy đổi tập trung trong `tpb/units.py`, xảy ra đúng
một lần tại lớp đọc dữ liệu.

## Đối chiếu chéo — chỉ phiên gần nhất

Hai nguồn giá độc lập thì dùng để kiểm tra lẫn nhau. Lệch > 2% ⇒ cảnh báo + hạ độ tin `Thấp`.

**Phạm vi bị giới hạn có chủ đích.** Đo trên 343 phiên chung của TPB: chuỗi lịch sử lệch tới
**7,82% ở 32 phiên** (cụm vào các mốc sự kiện quyền, vì hai nhà cung cấp điều chỉnh ở thời
điểm khác nhau), trong khi **phiên gần nhất khớp tuyệt đối**. Quét toàn chuỗi sẽ báo động giả
liên tục.

Hệ quả: **chỉ báo kỹ thuật tính từ một nguồn duy nhất (Entrade), tuyệt đối không trộn chuỗi.**

## Khi nguồn hỏng

| Tình huống | Hành vi |
|---|---|
| Entrade hỏng | dùng Yahoo, ghi `sources_failed`, hạ độ tin `TB` |
| Cả Entrade và Yahoo hỏng | dừng, báo rõ, **không ghi gì vào sheet** |
| CafeF hỏng | bỏ phần bối cảnh thị trường, ghi cảnh báo, vẫn chạy tiếp |
| Hai nguồn giá lệch > 2% | cảnh báo, hạ độ tin `Thấp` |
| Không có webhook, hoặc POST hỏng | in dòng ra để dán tay, **không crash**, thoát mã 0 |
| Ngày nghỉ | cột B ghi `—`, không bịa số |

## Chưa có nguồn

**Khối ngoại.** Bảng giá CafeF (`?center=1`) trả về dữ liệu nhưng tên cột (`a`–`z`) chưa được
giải mã theo schema công bố nào. Trường `foreign` để `null` kèm cảnh báo, **không bịa tên
trường cho khớp spec**.
