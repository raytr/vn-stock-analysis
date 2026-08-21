# Thiết kế: Skill phân tích cổ phiếu TPB

- **Ngày:** 2026-08-21
- **Trạng thái:** Chờ duyệt
- **Phạm vi:** Một mã duy nhất — TPB (Ngân hàng TMCP Tiên Phong, HOSE)

---

## 1. Bối cảnh và mục tiêu

Repo này sẽ là một **Claude Code Skill**. Người dùng chạy prompt của mình trên Claude Cloud,
trỏ vào repo, và nhận một báo cáo phân tích TPB kèm khuyến nghị hành động.

Vì mỗi lần chạy là một phiên độc lập — Claude không nhớ gì từ lần trước — **bộ nhớ phải nằm
ngoài mô hình**. Bộ nhớ đó gồm hai lớp:

1. **Journal trong repo** (`data/journal/TPB.jsonl`) — bộ nhớ chính, versioned bằng git.
2. **Google Sheet** — mặt kính người dùng nhìn vào, đồng thời là nơi khai báo vị thế đang nắm.

Mục tiêu không phải là "đoán đúng giá". Mục tiêu là **tích luỹ một chuỗi nhận định có thể
kiểm chứng được**, để sau vài tháng biết được nhận định nào đúng, nhận định nào sai, và sai
theo kiểu gì.

## 2. Phi mục tiêu

Loại bỏ dứt khoát, không làm:

- Không quét toàn sàn, không screener. Đúng một mã TPB.
- Không chạy theo lịch. Người dùng tự chạy prompt.
- Không đặt lệnh, không kết nối tài khoản chứng khoán.
- Không backtest, không tối ưu tham số.
- Không phân tích mã ngoài thị trường Việt Nam.
- Không giữ lại bất kỳ logic nào của hệ thống cũ.

## 3. Bài học từ hệ thống cũ

Repo hiện chứa một skill `stock-analysis` viết cho cổ phiếu Mỹ. Đã kiểm chứng bằng cách chạy
thật, và nó hỏng theo bốn cách — spec này tồn tại để không lặp lại:

| Lỗi cũ | Bằng chứng | Cách phòng trong thiết kế mới |
|---|---|---|
| Ngưỡng calibrate cho thị trường Mỹ | 5/5 blue chip VN đều ra BUY; `P/E < 15 = rẻ` fire trên mọi mã VN vì P/E thị trường VN vốn 10–14 | Không dùng ngưỡng tuyệt đối. Chỉ so tương đối: với ngành, với chính TPB trong quá khứ, với kỳ vọng lần trước |
| Đơn vị tiền tệ sai | Fetch `currency` rồi không dùng; in `$69000.00` cho giá 69.000đ | Mọi giá quy về VND nguyên. Có test khẳng định phép qua lại giữa hai nguồn |
| LLM và code lẫn vai | Bảng vote `if pe < 15` đóng vai "phán đoán đầu tư" | Python chỉ ra số. Claude chỉ diễn giải. Không bên nào lấn sang bên kia |
| Không có bộ nhớ | Mỗi lần chạy là một ảnh chụp rời rạc, không so được với lần trước | Journal + cột `Kiểm chứng` bắt buộc chấm lại nhận định cũ |

Ngoài ra, hệ cũ có `pip install` ngầm lúc chạy và một nhánh SSL tắt xác thực chứng chỉ. Cả hai
bị loại bỏ.

## 4. Kiến trúc

Nguyên tắc xuyên suốt:

> **LLM không bao giờ tự tính số. Python không bao giờ tự đưa ra khuyến nghị.**

```
.claude/skills/tpb-analysis/
├── SKILL.md                    quy trình 6 bước
├── references/
│   ├── banking-metrics.md      khung đọc chỉ số ngân hàng VN
│   ├── sheet-contract.md       hợp đồng cột với Google Sheet
│   └── data-sources.md         nguồn nào lấy gì, hỏng thì làm sao
└── scripts/
    ├── fetch_tpb.py            số liệu → JSON trên stdout
    ├── push_to_sheet.py        đẩy một dòng lên Apps Script
    ├── requirements.txt        yfinance==1.2.0 (pin)
    └── tests/
        ├── test_indicators.py     RSI/MACD/SMA trên chuỗi cố định
        ├── test_units.py          chuẩn hoá đơn vị giá
        ├── test_sheet_row.py      dựng dòng gửi sheet
        ├── test_degradation.py    thiếu webhook thì không crash
        └── test_no_fabrication.py nguồn rỗng thì null, không bịa
apps-script/Code.gs             người dùng dán vào Apps Script
data/journal/TPB.jsonl          bộ nhớ chính, mỗi dòng một lần chạy
reports/YYYY-MM-DD.md           báo cáo đầy đủ, commit vào git
```

Bốn đơn vị tách rời, mỗi đơn vị một trách nhiệm:

| Đơn vị | Trách nhiệm | Phụ thuộc | Kiểm chứng bằng |
|---|---|---|---|
| `fetch_tpb.py` | Số → JSON. Không diễn giải, không khuyến nghị | yfinance, stdlib | test với chuỗi giá cố định |
| `push_to_sheet.py` | Đẩy một dòng. Không biết gì về chứng khoán | stdlib | test với endpoint giả |
| `SKILL.md` | Quy trình và phán đoán. Không tính toán | Claude | chạy thử |
| `banking-metrics.md` | Kiến thức ngành | — | review bằng mắt |

## 5. Nguồn dữ liệu

Toàn bộ đã kiểm chứng bằng request thật ngày 2026-08-21.

| Cần gì | Nguồn | Endpoint | Trạng thái |
|---|---|---|---|
| OHLCV lịch sử TPB | **Entrade (DNSE)** 🇻🇳 | `services.entrade.com.vn/chart-api/v2/ohlcs/stock` | ✅ 274 phiên |
| VN-Index, VN30 lịch sử | **Entrade** 🇻🇳 | `.../ohlcs/index?symbol=VNINDEX\|VN30` | ✅ 274 phiên |
| Chỉ số realtime + GTGD | **CafeF** 🇻🇳 | `banggia.cafef.vn/stockhandler.ashx?index=true` | ✅ |
| Bảng giá toàn sàn | **CafeF** 🇻🇳 | `.../stockhandler.ashx?center=1` | ✅ 110KB |
| P/B, ROE, book value, EPS, target — 22 ngân hàng | Yahoo | `yfinance` với hậu tố `.VN` | ✅ |
| NIM, CASA, NPL, LLR, CIR, CAR | BCTC | Claude WebSearch/WebFetch | chưa verify |
| Tin doanh nghiệp | CafeF, Vietstock, IR TPBank | Claude WebSearch | chưa verify |

Đã loại, kèm lý do:

- **TCBS** — Cloudflare chặn bot, trả trang "Just a moment..." với mọi header.
- **VNDirect** — 406 và timeout.
- **Simplize, Vietstock, Fireant** — 404, hoặc 401 đòi auth.
- **VN-Index trên Yahoo** — không tồn tại. `^VNINDEX`, `^VN30`, `^VNI`, `VNINDEX.VN` đều 404.
- **VNM (VanEck Vietnam ETF)** — niêm yết ở Mỹ, ngoài phạm vi.

Vai trò của Yahoo thu hẹp còn đúng một việc: chỉ số cơ bản của ngành ngân hàng. Không nguồn
Việt Nam nào thay được mà không cần auth. Toàn bộ dữ liệu giá và chỉ số thị trường lấy từ
nguồn Việt Nam.

### 5.1 Chuẩn hoá đơn vị

Entrade trả `14.5`, Yahoo trả `14500`, cùng là 14.500 đồng. Đây đúng loại lỗi đã giết hệ cũ.

**Quy tắc:** mọi giá trong hệ thống là **VND nguyên, kiểu số nguyên**. Chuyển đổi xảy ra đúng
một lần, ngay tại lớp đọc dữ liệu, không nơi nào khác. `test_units.py` khẳng định
`round(entrade_close * 1000) == yahoo_close`.

### 5.2 Đối chiếu chéo

Có hai nguồn giá độc lập thì phải dùng để kiểm tra lẫn nhau. Lệch quá **2%** thì ghi cảnh báo
vào JSON và **hạ độ tin cậy xuống `Thấp`**. Không âm thầm tin một bên.

## 6. Hợp đồng dữ liệu

`fetch_tpb.py` in ra stdout đúng một object JSON. Đây là ranh giới giữa Python và Claude.

```json
{
  "meta": {
    "ticker": "TPB",
    "run_at": "2026-08-21T09:30:00+07:00",
    "session_date": "2026-08-20",
    "is_trading_day": true,
    "sources_ok": ["entrade", "cafef", "yahoo"],
    "sources_failed": [],
    "warnings": []
  },
  "price": {
    "close": 14500,
    "change_pct": 0.0,
    "volume": 6285000,
    "volume_avg20": 9179015,
    "volume_ratio": 0.68,
    "high_52w": 21000,
    "low_52w": 13750,
    "range_position_pct": 10.3,
    "cross_check": { "entrade": 14500, "yahoo": 14500, "diff_pct": 0.0, "ok": true }
  },
  "technicals": {
    "rsi14": 41.1,
    "macd": -220.6, "macd_signal": -295.2, "macd_hist": 74.6,
    "sma20": 14388, "sma50": 15407, "sma200": 16384
  },
  "valuation": {
    "pb": 0.88, "roe": 0.174, "pe": 5.3, "book_value": 16515,
    "pb_per_roe": 0.050,
    "sector": { "n": 22, "median_pb": 1.10, "median_roe": 0.171,
                "median_pb_per_roe": 0.062, "rank_pb_per_roe": 2 },
    "peers": [{ "code": "SHB", "pb": 0.78, "roe": 0.175, "pb_per_roe": 0.045 }]
  },
  "market": {
    "vnindex": { "value": 1734.24, "change_pct": 0.44, "value_bn": 13471.96 },
    "vn30": { "value": 1887.06, "change_pct": 0.60, "value_bn": 8063.95 },
    "vnindex_vs_sma50": "above",
    "tpb_rel_strength_20d": -4.2
  },
  "position": { "avg_price": null, "volume": null, "unrealized_pl": null }
}
```

`tpb_rel_strength_20d` là hiệu suất TPB trừ hiệu suất VN-Index trong 20 phiên. Nó trả lời câu
hỏi: TPB yếu vì bản thân nó, hay vì cả thị trường đang yếu.

Trường nào không lấy được thì để `null` và ghi vào `meta.warnings`. **Không bịa số.**

### 6.1 Khối `position` do đâu mà có

`fetch_tpb.py` **không có credential Google, không tự đọc sheet được**. Luồng đúng là:

1. Claude đọc sheet qua connector Google Drive (`read_file_content`), lấy `M1` và `M2`.
2. Claude truyền vào script: `fetch_tpb.py --holding-avg 14200 --holding-volume 5000`.
3. Script tính `unrealized_pl` và điền khối `position`.

Không truyền tham số thì cả ba trường là `null`, và báo cáo chuyển sang giọng "đang ngắm" thay
vì "đang nắm". Đây là ranh giới rõ ràng: **Python không biết Google, Claude không biết tính toán.**

## 7. Schema Google Sheet

Sheet: `1z4DhdV41EQa9eAi3-L6Hg4oRl4igtuc5Iz5wIMXAvJA`, tab `TPB Stock Monitor`.

### 7.1 Khối vị thế — người dùng nhập, skill chỉ đọc

| Ô | Nội dung |
|---|---|
| `L1` / `M1` | nhãn `Holding AVG Price` / giá vốn bình quân (VND) |
| `L2` / `M2` | nhãn `Holding Volume` / số lượng đang nắm, để `0` nếu đứng ngoài |

Chuyển khối này sang cột L–M để không đè lên vùng nhật ký. Đây là ranh giới sở hữu: skill
**không bao giờ** ghi vào L hoặc M.

### 7.2 Khối nhật ký — skill ghi, tiêu đề ở dòng 3, dữ liệu từ dòng 4

| Cột | Tên | Ai ghi | Nội dung |
|---|---|---|---|
| A | `Date` | người dùng kẻ sẵn | ngày phiên, khoá để tìm dòng |
| B | `Close` | skill | giá đóng cửa phiên gần nhất, VND nguyên |
| C | `Volume` | skill | KLGD kèm phần trăm so với trung bình 20 phiên |
| D | `Signal` | skill | `MUA THÊM` / `GIỮ` / `GIẢM TỶ TRỌNG` / `THOÁT` / `ĐỨNG NGOÀI` |
| E | `Độ tin` | skill | `Cao` / `TB` / `Thấp` |
| F | `Lý do` | skill | một câu, **bắt buộc chứa số** |
| G | `Mức giá canh` | skill | hỗ trợ / kháng cự / cắt lỗ |
| H | `Next Step plan` | skill | dạng `nếu … thì …` |
| I | `Kiểm chứng` | skill | chấm lại dòng của 5 phiên trước: `Đúng` / `Sai` / `Chưa rõ` kèm một câu |
| J | `P/L` | công thức sheet | `=(B{row}-$M$1)*$M$2`, skill không ghi |

Vì sao là những cột này:

- **`Signal` dùng động từ hành động**, không dùng BUY/HOLD/SELL. Người dùng đang nắm cổ phiếu,
  nên câu hỏi thật là "làm gì với vị thế hiện có", không phải "cổ phiếu này tốt hay xấu".
- **`Độ tin` là bắt buộc.** Không có nó thì không phân biệt được nói đúng lúc tự tin với nói
  đúng lúc mò — và như vậy thì không chấm điểm được.
- **`Lý do` phải có số.** "Kỹ thuật tích cực" bị loại. "RSI 41 hồi từ 32, MACD hist dương ba
  phiên, giá vượt SMA-20 nhưng còn dưới SMA-50 tại 15.407" được nhận.
- **`Kiểm chứng` là trái tim của thiết kế.** Mỗi lần chạy, việc đầu tiên là đọc lại dòng của 5
  phiên trước, đối chiếu với giá thực tế, rồi tự chấm. Nhận định sai bị ghi vĩnh viễn ngay
  cạnh nhận định mới. Đây là cơ chế duy nhất khiến hệ khá lên thay vì lặp lại cùng một giọng
  lạc quan mỗi ngày.
- **`P/L` là công thức sheet.** Số tiền lãi lỗ không nên phụ thuộc việc một mô hình ngôn ngữ
  nhân đúng hay sai.

Ngày nghỉ và cuối tuần: ghi `—` vào cột B, các cột còn lại bỏ trống.

## 8. Cầu ghi Google Sheet

Bộ connector Google Drive **không ghi được ô Sheet** — đã kiểm chứng: `update_file` chỉ sửa
metadata, `create_file` chỉ tạo file mới, không có tool nào append được dòng. Nên cần một cầu ghi.

`apps-script/Code.gs` dựng một endpoint `doPost` gắn với sheet:

```javascript
function doPost(e) {
  const b = JSON.parse(e.postData.contents);
  const want = PropertiesService.getScriptProperties().getProperty('TOKEN');
  if (b.token !== want) return json({ ok: false, error: 'unauthorized' });
  // tìm dòng có cột A khớp b.date; không thấy thì append cuối bảng
  // ghi cột B..I; không đụng L, M, hay J
  return json({ ok: true, row: rowIndex, written: [...] });
}
```

Ba ràng buộc ép vào trong script, không phụ thuộc Claude nhớ:

1. **Chỉ ghi cột B–I.** Cột L, M là của người dùng. Cột J là công thức.
2. **Idempotent.** Chạy hai lần cùng ngày thì ghi đè đúng dòng đó, không đẻ dòng trùng.
3. **Trả `{ok, row, written}`.** Skill phải đọc phản hồi này mới được nói "đã ghi xong".
   Không có xác nhận thì báo là chưa ghi được.

Người dùng setup một lần: dán `Code.gs` vào Apps Script của sheet → Script Properties thêm
`TOKEN` → Deploy as Web app (Execute as Me, Access Anyone) → lấy URL.

### 8.1 Secret nằm ngoài git

URL và token **không vào repo**. Chúng nằm trong prompt người dùng chạy trên Claude Cloud:

```
Phân tích TPB theo skill tpb-analysis trong repo.
SHEET_WEBHOOK=https://script.google.com/macros/s/AKfy.../exec
SHEET_TOKEN=<chuỗi ngẫu nhiên>
```

Prompt nằm trong cấu hình routine của Claude Cloud, không đi vào git. **Repo có thể public.**

Thiếu webhook thì `push_to_sheet.py` **không crash** — nó in ra dòng đã format sẵn để người
dùng dán tay. Phân tích vẫn hoàn tất, chỉ bước ghi chuyển sang thủ công.

## 9. Khung phân tích ngân hàng

Ngân hàng không định giá bằng P/E được, vì lợi nhuận bị bóp méo bởi trích lập dự phòng. Tài
sản ngân hàng chủ yếu là tài sản tài chính nên giá trị sổ sách có ý nghĩa thật. Trục chính là
**P/B đi kèm ROE**.

| Trục | Chỉ số |
|---|---|
| Định giá | P/B, ROE, P/B÷ROE |
| Chất lượng tài sản | NPL, tỷ lệ bao phủ nợ xấu, **nợ nhóm 2**, chi phí dự phòng trên LNTT |
| Sinh lời | NIM, **CASA**, CIR, thu nhập ngoài lãi |
| Tăng trưởng và an toàn vốn | tăng trưởng tín dụng, room NHNN cấp, CAR, LDR |
| Kỹ thuật | giá so với SMA20/50/200, RSI-14, MACD, thanh khoản so với TB20, vị trí trong biên 52 tuần |
| Bối cảnh thị trường | VN-Index, VN30, GTGD toàn sàn, sức mạnh tương đối của TPB so với VN-Index |

Nợ nhóm 2 là chỉ báo sớm của nợ xấu quý sau. CASA là lợi thế riêng của TPB nhờ mảng số hoá.
Room tín dụng là trần tăng trưởng do NHNN áp, không do ngân hàng tự quyết.

### 9.1 Ba phép so, không có ngưỡng tuyệt đối

1. **So với ngành** — 22 ngân hàng niêm yết, xếp hạng theo P/B÷ROE.
2. **So với chính TPB trong quá khứ** — P/B hiện tại ở phân vị nào của 3–5 năm.
3. **So với kỳ vọng lần trước** — cột `Kiểm chứng`.

Số liệu ngày 2026-08-21 minh hoạ vì sao phép so ngành là bắt buộc: TPB có P/B 0,88 với ROE
17,4%, tức 0,050 cho mỗi điểm ROE, rẻ hơn trung vị ngành (0,062) khoảng 18%. Nhưng SHB đang ở
0,045 — rẻ hơn nữa với ROE tương đương. Nếu luận điểm mua TPB là "rẻ so với chất lượng" thì
SHB đang rẻ hơn, và khung **bắt buộc phải nói ra điều đó** thay vì giấu đi.

## 10. Quy tắc sinh tín hiệu

Claude **không cộng điểm**. Claude viết ra: định giá đang nói gì, chất lượng tài sản đang nói
gì, kỹ thuật đang nói gì, bối cảnh thị trường đang nói gì — và bốn cái đó đồng thuận hay mâu
thuẫn ở đâu. Tín hiệu và độ tin cậy sinh ra từ đoạn đó.

Bốn quy tắc ép cứng trong `SKILL.md`:

1. **Bắt buộc phản biện.** Nghiêng về mua thì phải viết bear case; nghiêng về bán thì phải
   viết bull case. Thiếu đoạn này thì báo cáo không hợp lệ.
2. **Thiếu dữ liệu thì nói thiếu.** BCTC quý chưa ra, không tìm được NPL → ghi rõ và hạ độ tin
   xuống `Thấp`. Không lấp chỗ trống bằng phỏng đoán.
3. **Mọi lý do phải kèm số**, và số đó phải đến từ JSON của `fetch_tpb.py` hoặc từ nguồn Claude
   đọc được và trích dẫn. Claude không tự tính toán số mới.
4. **Chấm lại trước, phán đoán sau.** Bước đầu tiên mỗi lần chạy là điền cột `Kiểm chứng` cho
   nhận định 5 phiên trước, trước khi nhìn số liệu hôm nay.

## 11. Xử lý lỗi

| Tình huống | Hành vi |
|---|---|
| Entrade hỏng | Dùng Yahoo, ghi vào `sources_failed`, hạ độ tin xuống `TB` |
| Cả Entrade và Yahoo hỏng | Dừng. Báo rõ. Không ghi gì vào sheet |
| CafeF hỏng | Bỏ phần bối cảnh thị trường, ghi cảnh báo, vẫn chạy tiếp |
| Hai nguồn giá lệch quá 2% | Ghi cảnh báo, hạ độ tin xuống `Thấp` |
| Không có webhook, hoặc POST hỏng | In dòng ra để dán tay. Không crash |
| Ngày nghỉ | Ghi `—` vào cột B. Không bịa số |
| BCTC chưa có quý mới | Dùng quý gần nhất, ghi rõ là quý nào |

## 12. Kiểm thử

| Test | Khẳng định điều gì |
|---|---|
| `test_indicators.py` | RSI/MACD/SMA trên chuỗi giá cố định ra đúng giá trị đã biết |
| `test_units.py` | `round(entrade * 1000) == yahoo`; mọi giá là số nguyên VND |
| `test_sheet_row.py` | Dòng gửi lên sheet có đúng 8 trường B–I, đúng thứ tự |
| `test_degradation.py` | Thiếu webhook thì in ra dòng và thoát mã 0, không crash |
| `test_no_fabrication.py` | Nguồn trả rỗng thì trường tương ứng là `null`, không phải số bịa |

Không test nội dung phán đoán của Claude — cái đó không đơn định. Cột `Kiểm chứng` mới là cơ
chế đánh giá phán đoán, và nó chạy theo thời gian thực chứ không phải trong CI.

## 13. Rủi ro và điểm chưa kiểm chứng

| Rủi ro | Mức | Ứng phó |
|---|---|---|
| Sandbox Claude Cloud chặn gọi ra `script.google.com` | Trung bình | Chưa verify được từ máy local. Fallback in dòng đã có sẵn |
| Sandbox chặn `services.entrade.com.vn` hoặc `cafef.vn` | Trung bình | Yahoo làm nguồn dự phòng cho giá |
| Endpoint Entrade/CafeF là API nội bộ, có thể đổi không báo trước | Cao | Hai nguồn giá độc lập; đối chiếu chéo phát hiện được ngay |
| `.info` của yfinance vốn hay vỡ khi Yahoo đổi cấu trúc | Trung bình | Pin `yfinance==1.2.0`; thiếu trường thì `null` chứ không crash |
| Không có nguồn tự động cho NIM/CASA/NPL | Cao | Claude đọc BCTC qua WebFetch và **trích dẫn nguồn**; thiếu thì hạ độ tin |
| Người dùng quên cập nhật vị thế trong sheet | Trung bình | Vị thế cũ hơn 30 phiên thì cảnh báo trong báo cáo |

## 14. Tiêu chí hoàn thành

- [ ] Toàn bộ logic thị trường nước ngoài bị xoá khỏi repo
- [ ] `fetch_tpb.py` in ra JSON đúng hợp đồng ở mục 6, không có trường bịa
- [ ] Toàn bộ giá là VND nguyên; test đơn vị xanh
- [ ] Đối chiếu chéo hai nguồn hoạt động và hạ độ tin khi lệch
- [ ] `Code.gs` ghi đúng cột B–I, idempotent, không đụng L/M/J
- [ ] Thiếu webhook thì in dòng ra để dán tay, không crash
- [ ] `SKILL.md` ép đủ bốn quy tắc ở mục 10
- [ ] Chạy thật một lần trên TPB, ra báo cáo có phản biện và có cột `Kiểm chứng`
- [ ] Journal ghi được và đọc lại được ở lần chạy kế tiếp
