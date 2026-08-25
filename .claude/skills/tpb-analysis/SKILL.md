---
name: tpb-analysis
description: Phân tích cổ phiếu TPB (Ngân hàng TMCP Tiên Phong, HOSE) — biểu đồ kỹ thuật, tin tức mới nhất, báo cáo tài chính — rồi đưa ra khuyến nghị hành động kèm độ tin cậy, và ghi vào Google Sheet để theo dõi theo thời gian. Dùng nguồn dữ liệu Việt Nam (Entrade, CafeF).
version: 2.0.0
---

# Phân tích TPB

Chỉ phân tích **một mã: TPB**. Không mở rộng sang mã khác, không sang thị trường khác.

Mục tiêu không phải đoán đúng giá. Mục tiêu là **tích luỹ một chuỗi nhận định kiểm chứng
được**, để sau vài tháng biết nhận định nào đúng, nhận định nào sai, và sai theo kiểu gì.

## Nguồn sự thật: Google Sheet, không phải repo

Repo này **chỉ chứa code skill và chỉ được đọc**. Skill không commit, không push, không cần
quyền ghi GitHub. Toàn bộ trạng thái giữa các lần chạy nằm ở Google Sheet.

Hệ quả phải nhớ: **không có gì trong thư mục làm việc sống sót qua lần chạy sau.** Cái gì cần
nhớ thì phải nằm trên Sheet. Cái gì cần đưa cho người dùng thì gửi thẳng cho họ trong phiên.

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

Đọc sheet `1z4DhdV41EQa9eAi3-L6Hg4oRl4igtuc5Iz5wIMXAvJA` (tab `TPB Stock Monitor`) bằng
Google Drive MCP (`read_file_content` với `fileId` là ID trên).

Lấy về:

- ô `M1` = giá vốn bình quân, ô `M2` = khối lượng đang nắm
- dòng nhật ký của **5 phiên trước** — chuẩn bị cho bước 2
- **ô `Volume` của dòng cuối cùng có dữ liệu** — chứa ngày phiên đã phân tích lần trước,
  dùng cho bước 3b

**Đừng tin toạ độ ô một cách mù quáng.** Sheet này đã từng có giá vốn nằm ở `I1/I2` thay vì
`M1/M2`, và lần chạy đó đọc ra "trống → đứng ngoài" trong khi người dùng đang nắm 400 cp.
Đọc nhầm theo hướng này là **hỏng toàn bộ báo cáo**, vì `ĐỨNG NGOÀI` và `GIỮ` là hai lời khuyên
khác hẳn nhau. Nên: tìm ô có nhãn `Holding AVG Price` / `Holding Volume` ở ba dòng đầu và lấy
ô **ngay bên phải nhãn**, chứ không lấy cứng `M1/M2`. Nhãn nằm ở cột nào cũng đọc được.

Nếu tìm thấy nhãn mà ô giá trị trống, **hãy nghi ngờ trước khi kết luận đứng ngoài**: nói rõ
trong báo cáo là "đọc được ô vị thế và nó trống", để người dùng biết là đã đọc chứ không phải
đọc trượt.

`M2` trống hoặc bằng 0 nghĩa là đang đứng ngoài; báo cáo chuyển sang giọng "đang ngắm".
Có vị thế thì `Signal` **không được là `ĐỨNG NGOÀI`** — phải là `GIỮ` / `MUA THÊM` /
`GIẢM TỶ TRỌNG` / `THOÁT`, và `Lý do` phải nêu giá vốn cùng lãi/lỗ hiện tại bằng số.

### Bước 2 — Chấm lại nhận định cũ

Đối chiếu `Signal`, `Mức giá canh`, `Next Step plan` của 5 phiên trước với giá thực tế hôm
nay. Kết luận `Đúng` / `Sai` / `Chưa rõ` kèm một câu giải thích. **Làm xong bước này rồi mới
sang bước 3.** Lần chạy đầu tiên chưa có lịch sử thì ghi "chưa có lịch sử".

Bước này cần biết giá hiện tại, mà giá thì đến ở bước 3 — nên để giữ đúng tinh thần quy tắc 4:
**viết ra tiêu chí chấm trước khi chạy `fetch_tpb.py`**, dạng bảng "điều kiện nào thì Đúng,
điều kiện nào thì Sai, điều kiện nào thì Chưa rõ". Sau đó chỉ áp tiêu chí một cách máy móc.
Tiêu chí đặt sau khi thấy giá là tiêu chí đã bị nhiễm.

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

Kiểm tra thêm, không có trong `warnings`: **nếu khối `valuation` trả về toàn `null`** (P/B,
ROE, so sánh ngành) thì đó là mất dữ liệu nghiêm trọng chứ không phải nhiễu nhẹ. Chạy lại một
lần để phân biệt lỗi tạm thời với lỗi thật. Vẫn rỗng thì hạ độ tin và **nói rõ đang dùng số
của lần chạy nào**, không im lặng xài số cũ như số mới.

### Bước 3b — Có phiên mới không?

So `meta.session_date` với ngày phiên ghi trong ô `Volume` của dòng cuối có dữ liệu (bước 1):

- **Trùng nhau** → thị trường **không giao dịch** (ngày lễ), hoặc phiên này đã phân tích rồi.
  **Không ghi gì vào sheet**, báo cho người dùng một dòng, rồi **DỪNG**. Không phân tích lại.
- **Khác nhau** → có phiên mới, chạy tiếp.

Sheet chỉ chứa **dòng của những phiên đã thực sự phân tích** — không kẻ sẵn lịch, không có dòng
cuối tuần, không có dòng ngày lễ. Ngày không giao dịch thì đơn giản là không có dòng nào. Nhờ
vậy skill không cần biết lịch nghỉ Tết âm lịch hay Giỗ Tổ: cái gì sàn không giao dịch thì
`fetch_tpb.py` không trả về phiên mới, và không có dòng nào được sinh ra.

Chạy sáng thứ Hai thì phiên gần nhất là thứ Sáu — **đó là bình thường**, không phải ngày lễ.
Thị trường VN giao dịch thứ Hai–thứ Sáu, nghỉ Tết Nguyên đán, Giỗ Tổ 10/3 âm lịch, 30/4, 1/5, 2/9.

### Bước 4 — Đọc tin tức và báo cáo tài chính

WebSearch/WebFetch: tin TPB mới nhất, BCTC quý gần nhất. Tìm **NIM, CASA, NPL, tỷ lệ bao phủ
nợ xấu, nợ nhóm 2, CIR, CAR, tăng trưởng tín dụng và room tín dụng**. Trích dẫn nguồn.
Không tìm được thì ghi rõ là không có và hạ độ tin — không suy đoán.

**Nhiều trang tài chính VN bị network policy của môi trường chặn** (vietstock, cafef, baomoi,
vietnambiz, dnse, vsd, investing…). WebSearch vẫn trả về trích đoạn nội dung của chúng dù
WebFetch bị 403. Số lấy từ trích đoạn tìm kiếm là **nguồn gián tiếp** — dùng được, nhưng phải
ghi rõ là chưa đối chiếu bản gốc, và không nâng độ tin dựa trên nó.

Luôn kiểm tra **sự kiện quyền sắp tới** (ngày GDKHQ, tỷ lệ). TPB chia cổ tức bằng cổ phiếu rất
thường xuyên. Sự kiện quyền trong vài phiên tới làm **mọi mốc kỹ thuật hết hiệu lực** và phải
được nêu lên đầu báo cáo, không chôn ở cuối.

**Cổ tức bằng cổ phiếu trung tính về giá trị.** Nhận thêm 15% số cổ phiếu trong khi giá bị
chiết khấu tương ứng thì tài sản không đổi. Vì vậy nó **không bao giờ là lý do để giữ, và cũng
không phải lý do để bán**. Không được viết "giữ để nhận cổ phiếu thưởng" — đó đúng là ngộ nhận
phổ biến nhất của nhà đầu tư cá nhân quanh ngày GDKHQ, và skill này tồn tại một phần để không
lặp lại nó. Quyết định giữ hay bán phải dựa trên luận điểm, còn sự kiện quyền chỉ là phép chia.

### Bước 5 — Tổng hợp

Đọc `references/banking-metrics.md` trước khi kết luận.

Viết ra: **định giá** nói gì, **chất lượng tài sản** nói gì, **kỹ thuật** nói gì, **bối cảnh
thị trường** nói gì — và bốn cái đó đồng thuận hay mâu thuẫn ở đâu. Tín hiệu sinh ra từ đoạn
đó, **không từ phép cộng điểm**.

`Signal` chọn một trong: `MUA THÊM` / `GIỮ` / `GIẢM TỶ TRỌNG` / `THOÁT` / `ĐỨNG NGOÀI`.
Đây là động từ hành động gắn với vị thế đang có, không phải nhãn tốt/xấu cho cổ phiếu.

`Độ tin`: `Cao` / `TB` / `Thấp`, và phải nói rõ vì sao.

### Bước 6 — Ghi vào Sheet

```bash
python3 push_to_sheet.py \
  --date <YYYY-MM-DD> --close <giá> \
  --volume "phiên <YYYY-MM-DD> · <KL> (x.xx× TB20)" \
  --signal "<tín hiệu>" --confidence "<Cao|TB|Thấp>" \
  --reason "<một câu có số>" --levels "<HT ... / KC ... / CL ...>" \
  --next-step "<nếu ... thì ...>" --review "<kết quả bước 2>" \
  --webhook "$SHEET_WEBHOOK" --token "$SHEET_TOKEN"
```

`--date` là **ngày chạy** theo giờ VN. Cột `Volume` **bắt buộc mở đầu bằng `phiên <ngày phiên>`**
— đó là trí nhớ giữa các lần chạy mà bước 3b dựa vào. Bỏ tiền tố này là làm hỏng bước 3b.

#### Xác minh đã ghi — đọc kỹ đoạn này

Thấy `✅ Đã ghi vào sheet, dòng N` thì xong.

**Nhưng script có thể báo sai.** Apps Script trả kết quả qua một redirect sang
`script.googleusercontent.com`; domain đó thường bị egress proxy chặn. Khi đó `doPost` **đã
chạy và đã ghi**, nhưng script không đọc được phản hồi nên in ra
`⚠️ CHƯA ghi được (URLError: ... 403 Forbidden)`. Đây là âm tính giả.

Gặp cảnh báo đó thì **đọc lại sheet bằng Google Drive MCP để kiểm chứng**:

- Dòng của hôm nay đã có đủ dữ liệu → **đã ghi xong**. Nói rõ là xác minh bằng cách đọc lại,
  chứ không phải script xác nhận.
- Dòng vẫn trống → **CHƯA ghi được thật**. Đưa dòng dán tay cho người dùng và nói rõ.

Không được nói "đã ghi xong" khi chưa có một trong hai bằng chứng trên. Chạy lại
`push_to_sheet.py` là an toàn — Apps Script ghi đè đúng dòng theo ngày, không đẻ dòng trùng.

### Bước 7 — Giao báo cáo cho người dùng

Viết báo cáo đầy đủ ra `reports/YYYY-MM-DD.md` rồi **gửi thẳng file đó cho người dùng trong
phiên**. Không commit, không push — repo là chỉ đọc, và container sẽ bị thu hồi.

Chạy theo lịch thì phần tóm tắt đi kèm notification, vì đó là kênh duy nhất người dùng thực sự
nhìn thấy.

## Không làm

- **Không commit, không push, không tạo PR.** Skill này không cần quyền ghi GitHub. Gặp lỗi
  403 khi thao tác git nghĩa là đang làm sai quy trình, không phải cần xin thêm quyền.
- **Không tư vấn margin hay đòn bẩy.** Đây là chỗ nhà đầu tư cá nhân Việt Nam thiệt hại nặng
  nhất, và hệ thống này không biết sức chịu đựng tài chính của người dùng.
- **Không phân tích phái sinh VN30F hay chứng quyền CW.**
- **Không tự đặt giá mục tiêu bằng con số của riêng mình.** Chỉ trích dẫn target của công ty
  chứng khoán kèm nguồn.

Kết thúc mọi báo cáo bằng: _"Đây là phân tích định lượng dựa trên dữ liệu hiện có, không phải
lời khuyên đầu tư."_
