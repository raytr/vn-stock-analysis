# Cầu ghi Google Sheet

Sheet: `1z4DhdV41EQa9eAi3-L6Hg4oRl4igtuc5Iz5wIMXAvJA` — tab `TPB Stock Monitor`

## Vì sao cần cái này

Bộ connector Google Drive của Claude **không ghi được ô Sheet** — `update_file`
chỉ sửa metadata, `create_file` chỉ tạo file mới. Không có tool nào append được
một dòng. Nên cần một endpoint tự dựng.

## Cài một lần

1. Mở sheet → **Extensions → Apps Script** → dán toàn bộ `Code.gs`
2. **Project Settings → Script Properties** → thêm `TOKEN` = một chuỗi ngẫu nhiên
3. **Deploy → New deployment → Web app**

- Execute as: **Me**
- Who has access: **Anyone**

4. Copy URL dạng `https://script.google.com/macros/s/AKfy.../exec`

## Bố cục sheet cần chuẩn bị

| Vùng  | Ai ghi                                                   |
| ----- | -------------------------------------------------------- |
| A     | ngày, kẻ sẵn                                             |
| B–I   | **skill ghi**                                            |
| J     | công thức `=(B4-$M$1)*$M$2`, fill xuống                  |
| L1/M1 | nhãn `Holding AVG Price` / giá vốn — **người dùng nhập** |
| L2/M2 | nhãn `Holding Volume` / khối lượng — **người dùng nhập** |

Tiêu đề ở dòng 3: `Date | Close | Volume | Signal | Độ tin | Lý do | Mức giá canh | Next Step plan | Kiểm chứng | P/L`

## Kiểm tra sau khi deploy

⚠️ **Bắt buộc có `-L --post302`.** Apps Script trả 302 chuyển hướng sang
`script.googleusercontent.com`; curl mặc định **đổi POST thành GET** khi gặp 302, request
cuối thành GET, mà script chỉ có `doPost` → trả HTML "Không tìm thấy trang" chứ không phải
JSON. Rất dễ tưởng nhầm là sai token.

⚠️ **Không bao giờ dán URL hoặc token thật vào file này** — nó nằm trong git. Dùng biến môi
trường, giá trị thật để trong `.env` (đã gitignore).

```bash
curl -sS -L --post302 -X POST "$SHEET_WEBHOOK" -H 'Content-Type: application/json' \
  -d '{"token":"'"$SHEET_TOKEN"'","date":"2026-08-21","close":14500,"signal":"GIỮ"}'
```

Kỳ vọng: `{"ok":true,"row":<số dòng>,"written":[...]}`

Gọi lại lần hai cùng ngày phải ghi đè đúng dòng đó, không tạo dòng mới.

## Bảo mật

URL và token **không nằm trong repo**. Chúng ở trong prompt chạy trên Claude
Cloud, nên repo để public vẫn an toàn.
