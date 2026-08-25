# Hợp đồng cột với Google Sheet

Sheet `1z4DhdV41EQa9eAi3-L6Hg4oRl4igtuc5Iz5wIMXAvJA`, tab `TPB Stock Monitor`.

## Ranh giới sở hữu

| Vùng        | Ai ghi          | Nội dung                                               |
| ----------- | --------------- | ------------------------------------------------------ |
| `L1` / `M1` | **người dùng**  | nhãn `Holding AVG Price` / giá vốn bình quân (VND)     |
| `L2` / `M2` | **người dùng**  | nhãn `Holding Volume` / khối lượng, `0` nếu đứng ngoài |
| `A`         | **skill**       | ngày chạy — khoá để tìm dòng                           |
| `B`–`I`     | **skill**       | nhật ký, xem bảng dưới                                 |
| `J`         | công thức sheet | lãi/lỗ chưa thực hiện, có guard rỗng                   |

Skill **không bao giờ** ghi vào L, M hay J. Ràng buộc này nằm trong `Code.gs` chứ không phụ
thuộc Claude nhớ: ghi bắt đầu từ cột B (`FIRST_WRITE_COL = 2`) và dài đúng 8 cột.

Số tiền lãi/lỗ để sheet tự tính bằng công thức — nó không nên phụ thuộc việc một mô hình
ngôn ngữ nhân đúng hay sai. Công thức có guard rỗng vì **0 đồng lãi và không có vị thế là hai
chuyện khác nhau**, không được hiển thị giống nhau:

```
=IF(OR($M$1="",$M$2="",$M$2=0,B{row}="",NOT(ISNUMBER(B{row}))),"",(B{row}-$M$1)*$M$2)
```

> **Cảnh báo đã xảy ra thật.** Sheet từng để giá vốn ở `I1/I2` thay vì `L1/M1`, `L2/M2`. Cột
> `I` là vùng skill ghi (`Kiểm chứng`), nên đó là va chạm chờ xảy ra — và trong khi chờ, skill
> đọc `M1/M2` thấy trống rồi kết luận "đang đứng ngoài" cho một người đang nắm 400 cp. Khi đọc
> vị thế, **dò theo nhãn `Holding …` rồi lấy ô bên phải**, đừng lấy cứng toạ độ.

## Không kẻ sẵn lịch

Sheet **chỉ chứa dòng của những phiên đã thực sự phân tích**. Không có dòng cuối tuần, không có
dòng ngày lễ, không có dòng kẻ sẵn còn trống.

Lý do: kẻ sẵn lịch buộc ai đó phải biết lịch nghỉ Tết âm lịch, Giỗ Tổ 10/3 âm lịch, và các ngày
nghỉ bù — một bảng dữ liệu phải bảo trì hằng năm và sẽ sai vào đúng năm không ai để ý. Còn nếu
để dòng sinh ra theo lần chạy thật, thì ngày sàn đóng cửa đơn giản là không có dòng nào, không
cần biết vì sao nó đóng.

`apps-script/cleanup.gs` dọn sheet về trạng thái này, chạy một lần.

## Cột nhật ký, dữ liệu ngay dưới dòng tiêu đề

| Cột | Tên              | Nội dung                                                                                 |
| --- | ---------------- | ---------------------------------------------------------------------------------------- |
| B   | `Close`          | giá đóng cửa phiên gần nhất, VND nguyên                                                  |
| C   | `Volume`         | **ngày phiên** + KLGD kèm bội số TB20, ví dụ `phiên 2026-08-21 · 6.285.000 (0,81× TB20)` |
| D   | `Signal`         | `MUA THÊM` / `GIỮ` / `GIẢM TỶ TRỌNG` / `THOÁT` / `ĐỨNG NGOÀI`                            |
| E   | `Độ tin`         | `Cao` / `TB` / `Thấp`                                                                    |
| F   | `Lý do`          | một câu, **bắt buộc chứa số**                                                            |
| G   | `Mức giá canh`   | hỗ trợ / kháng cự / cắt lỗ                                                               |
| H   | `Next Step plan` | dạng `nếu … thì …`                                                                       |
| I   | `Kiểm chứng`     | chấm lại nhận định 5 phiên trước: `Đúng` / `Sai` / `Chưa rõ` + một câu                   |

## Vì sao mỗi cột tồn tại

- **`Signal` dùng động từ hành động**, không dùng BUY/HOLD/SELL. Người dùng đang nắm cổ
  phiếu, nên câu hỏi thật là "làm gì với vị thế hiện có", không phải "cổ phiếu này tốt hay xấu".
  Hệ quả: `M2 > 0` thì `ĐỨNG NGOÀI` là **giá trị không hợp lệ** — không thể khuyên ai đứng
  ngoài khi họ đang ở trong.
- **`Độ tin` là bắt buộc.** Không có nó thì không phân biệt được nói đúng lúc tự tin với nói
  đúng lúc mò — và như vậy thì không chấm điểm được.
- **`Kiểm chứng` là trái tim của thiết kế.** Nhận định sai bị ghi vĩnh viễn ngay cạnh nhận
  định mới. Đây là cơ chế duy nhất khiến hệ khá lên thay vì lặp lại cùng một giọng lạc quan.

Ngày nghỉ và cuối tuần: **không ghi dòng nào cả**. Không bịa số, và cũng không kẻ dòng rỗng.

## Vì sao cột `Volume` mang cả ngày phiên

Cột `A` là **ngày chạy**, không phải ngày phiên. Hai thứ này lệch nhau thường xuyên: chạy sáng
thứ Hai thì phiên gần nhất là thứ Sáu.

Skill cần biết "phiên này đã phân tích chưa" để không phân tích lại vào ngày lễ. Trước đây
thông tin đó nằm ở `data/journal/TPB.jsonl` trong repo — nhưng repo là chỉ đọc và container
bị thu hồi sau mỗi lần chạy, nên file đó không sống sót.

Nhét ngày phiên vào đầu cột `Volume` giữ được trí nhớ đó **mà không phải đổi `Code.gs` hay
thêm cột**. Sheet trở thành nơi duy nhất giữ trạng thái, đúng như nó vốn nên thế.
