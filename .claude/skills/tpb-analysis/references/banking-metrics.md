# Khung đọc chỉ số ngân hàng Việt Nam

## Vì sao ngân hàng phải đọc khác

Ngân hàng **không định giá bằng P/E được**: lợi nhuận bị bóp méo bởi trích lập dự phòng, một
quý trích mạnh làm P/E vọt lên mà doanh nghiệp chẳng xấu đi. Tài sản ngân hàng lại chủ yếu là
tài sản tài chính, nên **giá trị sổ sách có ý nghĩa thật** — khác hẳn doanh nghiệp sản xuất.

Trục chính là **P/B đi kèm ROE**: trả bao nhiêu cho mỗi đồng vốn, và đồng vốn đó đẻ ra bao nhiêu.

## Bốn trục chỉ số

| Trục | Chỉ số | Ghi chú |
|---|---|---|
| **Định giá** | P/B, ROE, P/B÷ROE | trục chính; P/E chỉ tham khảo |
| **Chất lượng tài sản** | NPL, tỷ lệ bao phủ nợ xấu (LLR), **nợ nhóm 2**, chi phí dự phòng/LNTT | nợ nhóm 2 là chỉ báo sớm của nợ xấu quý sau |
| **Sinh lời** | NIM, **CASA**, CIR, thu nhập ngoài lãi | CASA là lợi thế riêng của TPB nhờ mảng số hoá |
| **Tăng trưởng & an toàn vốn** | tăng trưởng tín dụng, room NHNN cấp, CAR, LDR | room tín dụng là trần do NHNN áp, không do ngân hàng tự quyết |
| **Dòng tiền khối ngoại** | mua/bán ròng, room ngoại còn lại | tỷ trọng NĐT cá nhân ở VN rất cao nên chuỗi bán ròng của khối ngoại thường đi trước áp lực giá |
| **Bối cảnh thị trường** | VN-Index, VN30, GTGD toàn sàn, sức mạnh tương đối | trả lời: TPB yếu vì bản thân nó hay vì cả thị trường |

## Ba phép so — không có ngưỡng tuyệt đối

Đây là chỗ hệ thống cũ chết. Nó dùng `P/E < 15 = rẻ`, calibrate cho tech Mỹ, nên **mọi cổ
phiếu VN đều ra "rẻ"** vì P/E thị trường VN vốn 10–14. Kết quả: 5/5 blue chip đều BUY.

**1. So với ngành** — 22 ngân hàng niêm yết, xếp hạng theo P/B÷ROE (hạng 1 = rẻ nhất trên mỗi
điểm ROE). Số liệu đo ngày 2026-08-21:

| | P/B | ROE | P/B÷ROE |
|---|---|---|---|
| TPB | 0,88 | 17,4% | 0,0505 — **hạng 3/20** |
| Trung vị ngành | — | — | 0,0742 |

TPB rẻ hơn trung vị ngành ~32% trên mỗi điểm ROE. **Nhưng có hai ngân hàng còn rẻ hơn.**
Khung này **bắt buộc phải nêu tên chúng ra**, không được giấu. Nếu luận điểm mua TPB là "rẻ
so với chất lượng", thì mã rẻ hơn với chất lượng tương đương là phản biện trực tiếp.

**2. So với chính TPB trong quá khứ** — P/B hiện tại nằm ở phân vị nào của 3–5 năm gần nhất.
Xu hướng quan trọng hơn mức tuyệt đối.

**3. So với kỳ vọng lần trước** — cột `Kiểm chứng` trong sheet.

## Cơ chế thị trường phải tôn trọng

- **Biên độ ±7% (HOSE).** Chạm trần hoặc sàn là **trạng thái mất thanh khoản một chiều**,
  không phải một mức giá bình thường. Phải nêu rõ khi xảy ra.
- **Biến động một phiên vượt ±7% là bất khả thi** trong giao dịch bình thường → đó là sự kiện
  quyền hoặc lỗi dữ liệu. `fetch_tpb.py` đã gắn cờ vào `meta.warnings`. **Không bao giờ mô tả
  chúng như áp lực bán.**
- **Thanh toán T+2.** Bán hôm nay thì T+2 mới có tiền. Kế hoạch ở cột `Next Step plan` phải
  tính độ trễ này, không giả định xoay vòng vốn trong ngày.
- **Thanh khoản mỏng.** KLGD dưới 50% trung bình 20 phiên làm chỉ báo kỹ thuật nhiễu nặng →
  hạ độ tin phần kỹ thuật.
- **Sự kiện quyền.** TPB chia cổ tức bằng cổ phiếu rất thường xuyên — 10 sự kiện từ 2018.
  Ngày giao dịch không hưởng quyền, giá bị điều chỉnh giảm **theo kỹ thuật, không phải do bán
  tháo**. Đọc nhầm chỗ này là đọc ngược hoàn toàn.
