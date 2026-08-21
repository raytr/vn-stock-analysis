---
name: tpb-analysis
description: Phân tích cổ phiếu TPB (Ngân hàng TMCP Tiên Phong, HOSE) — biểu đồ kỹ thuật, tin tức mới nhất, báo cáo tài chính — rồi đưa ra khuyến nghị hành động kèm độ tin cậy, và ghi vào Google Sheet để theo dõi theo thời gian. Dùng nguồn dữ liệu Việt Nam (Entrade, CafeF).
version: 1.0.0
---

# Phân tích TPB

Chỉ phân tích **một mã: TPB**. Không mở rộng sang mã khác, không sang thị trường khác.

Mục tiêu không phải đoán đúng giá. Mục tiêu là **tích luỹ một chuỗi nhận định kiểm chứng
được**, để sau vài tháng biết nhận định nào đúng, nhận định nào sai, và sai theo kiểu gì.

## Bốn quy tắc bắt buộc

1. **Bắt buộc phản biện.** Nghiêng về mua thì phải viết bear case; nghiêng về bán thì phải
   viết bull case. Thiếu đoạn này thì báo cáo không hợp lệ.
2. **Thiếu dữ liệu thì nói thiếu.** Không lấp chỗ trống bằng phỏng đoán. Hạ độ tin xuống `Thấp`.
3. **Mọi lý do phải kèm số**, và số đó phải đến từ JSON của `fetch_tpb.py` hoặc từ nguồn
   trích dẫn được. **Không tự tính số mới.** "Kỹ thuật tích cực" bị loại; "RSI 44,6 hồi từ
   32, MACD hist dương, giá 14.500 trên SMA-20 (14.417) nhưng dưới SMA-50 (15.294)" được nhận.
4. **Chấm lại trước, phán đoán sau.** Điền cột `Kiểm chứng` cho nhận định 5 phiên trước
   **TRƯỚC KHI** nhìn số liệu hôm nay. Nghịch trực giác nhưng cố ý: nhìn kết quả mới rồi mới
   chấm điểm cũ thì sẽ chấm theo hướng có lợi cho mình.

## Quy trình

### Bước 1 — Đọc vị thế và lịch sử từ sheet

Đọc sheet `1z4DhdV41EQa9eAi3-L6Hg4oRl4igtuc5Iz5wIMXAvJA` (tab `TPB Stock Monitor`):
- ô `M1` = giá vốn bình quân, ô `M2` = khối lượng đang nắm
- dòng nhật ký của **5 phiên trước** — chuẩn bị cho bước 2

`M2` trống hoặc bằng 0 nghĩa là đang đứng ngoài; báo cáo chuyển sang giọng "đang ngắm".

### Bước 2 — Chấm lại nhận định cũ

Đối chiếu `Signal`, `Mức giá canh`, `Next Step plan` của 5 phiên trước với giá thực tế hôm
nay. Kết luận `Đúng` / `Sai` / `Chưa rõ` kèm một câu giải thích. **Làm xong bước này rồi mới
sang bước 3.** Lần chạy đầu tiên chưa có lịch sử thì ghi "chưa có lịch sử".

### Bước 3 — Lấy số liệu

```bash
cd .claude/skills/tpb-analysis/scripts
pip install -r requirements.txt          # chỉ lần đầu
python3 fetch_tpb.py --holding-avg <M1> --holding-volume <M2>
```

Không có vị thế thì bỏ hai tham số. Thêm `--no-sector` nếu chỉ cần chạy nhanh để debug.

Đọc kỹ `meta.warnings`. Có cảnh báo nào thì **phải phản ánh vào độ tin cậy**, đặc biệt:
- phiên vượt biên độ ±7% → là **sự kiện quyền hoặc lỗi dữ liệu**, tuyệt đối không mô tả như
  áp lực bán
- hai nguồn giá lệch > 2% → hạ độ tin xuống `Thấp`
- thanh khoản mỏng → hạ độ tin phần kỹ thuật

### Bước 4 — Đọc tin tức và báo cáo tài chính

WebSearch/WebFetch: tin TPB mới nhất, BCTC quý gần nhất. Tìm **NIM, CASA, NPL, tỷ lệ bao phủ
nợ xấu, nợ nhóm 2, CIR, CAR, tăng trưởng tín dụng và room tín dụng**. Trích dẫn nguồn.
Không tìm được thì ghi rõ là không có và hạ độ tin — không suy đoán.

### Bước 5 — Tổng hợp

Đọc `references/banking-metrics.md` trước khi kết luận.

Viết ra: **định giá** nói gì, **chất lượng tài sản** nói gì, **kỹ thuật** nói gì, **bối cảnh
thị trường** nói gì — và bốn cái đó đồng thuận hay mâu thuẫn ở đâu. Tín hiệu sinh ra từ đoạn
đó, **không từ phép cộng điểm**.

`Signal` chọn một trong: `MUA THÊM` / `GIỮ` / `GIẢM TỶ TRỌNG` / `THOÁT` / `ĐỨNG NGOÀI`.
Đây là động từ hành động gắn với vị thế đang có, không phải nhãn tốt/xấu cho cổ phiếu.

`Độ tin`: `Cao` / `TB` / `Thấp`, và phải nói rõ vì sao.

### Bước 6 — Ghi lại

```bash
python3 push_to_sheet.py \
  --date <YYYY-MM-DD> --close <giá> --volume "<KL (x.xx× TB20)>" \
  --signal "<tín hiệu>" --confidence "<Cao|TB|Thấp>" \
  --reason "<một câu có số>" --levels "<HT ... / KC ... / CL ...>" \
  --next-step "<nếu ... thì ...>" --review "<kết quả bước 2>" \
  --webhook "$SHEET_WEBHOOK" --token "$SHEET_TOKEN"
```

**Chỉ được nói "đã ghi xong" khi thấy `✅ Đã ghi vào sheet, dòng N`.** Nếu ra chế độ dán tay
thì đưa dòng đó cho người dùng và nói rõ là **CHƯA** ghi được.

Cuối cùng: ghi báo cáo đầy đủ vào `reports/YYYY-MM-DD.md`, thêm một dòng JSON vào
`data/journal/TPB.jsonl`, rồi commit cả hai.

## Không làm

- **Không tư vấn margin hay đòn bẩy.** Đây là chỗ nhà đầu tư cá nhân Việt Nam thiệt hại nặng
  nhất, và hệ thống này không biết sức chịu đựng tài chính của người dùng.
- **Không phân tích phái sinh VN30F hay chứng quyền CW.**
- **Không tự đặt giá mục tiêu bằng con số của riêng mình.** Chỉ trích dẫn target của công ty
  chứng khoán kèm nguồn.

Kết thúc mọi báo cáo bằng: *"Đây là phân tích định lượng dựa trên dữ liệu hiện có, không phải
lời khuyên đầu tư."*
