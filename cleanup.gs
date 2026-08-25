/**
 * cleanup.gs — chạy MỘT LẦN để dọn lại cấu trúc sheet.
 *
 * Mở Apps Script editor của spreadsheet, dán file này vào, chọn hàm
 * `cleanupSheet` rồi bấm Run. Chạy lại nhiều lần cũng không sao (idempotent).
 *
 * Làm bốn việc:
 *   1. Chuyển ô vị thế từ H/I sang L/M — ra khỏi vùng B–I mà skill ghi đè.
 *   2. Viết lại dòng tiêu đề cho khớp nội dung thật đang được ghi.
 *   3. Xoá mọi dòng không có dữ liệu — cuối tuần, ngày lễ, dòng kẻ sẵn còn trống.
 *   4. Đặt lại công thức lãi/lỗ ở cột J cho các dòng còn lại.
 *
 * Sau khi chạy: mỗi dòng = một phiên đã thực sự phân tích. Không còn lịch kẻ sẵn.
 */
const SHEET_NAME = 'TPB Stock Monitor';

const HEADERS = ['Date', 'Close', 'Volume (phiên)', 'Signal', 'Độ tin',
                 'Lý do', 'Mức giá canh', 'Next Step plan', 'Kiểm chứng',
                 'Lãi/Lỗ'];   // A..J

function cleanupSheet() {
  const ss = SpreadsheetApp.getActive();
  const sheet = ss.getSheetByName(SHEET_NAME) || ss.getSheets()[0];
  if (!sheet) throw new Error('không tìm thấy tab nào');

  const moved = moveHoldingCells_(sheet);
  const headerRow = writeHeaders_(sheet);
  const removed = deleteEmptyRows_(sheet, headerRow);
  const formulas = setPnlFormulas_(sheet, headerRow);

  const msg = [
    'Vị thế: ' + moved,
    'Tiêu đề: viết lại tại dòng ' + headerRow,
    'Đã xoá ' + removed + ' dòng trống',
    'Đã đặt công thức lãi/lỗ cho ' + formulas + ' dòng',
  ].join('\n');
  Logger.log(msg);
  SpreadsheetApp.getActive().toast(msg, 'cleanupSheet xong', 10);
  return msg;
}

/**
 * Tìm ô nhãn "Holding AVG Price" / "Holding Volumn" ở đâu đó trong 3 dòng đầu
 * rồi chuyển nhãn sang cột L, giá trị sang cột M.
 *
 * Không hard-code H/I: sheet này đã từng lệch so với tài liệu một lần rồi,
 * nên dò theo nội dung an toàn hơn dò theo toạ độ.
 */
function moveHoldingCells_(sheet) {
  const scan = sheet.getRange(1, 1, 3, Math.max(sheet.getLastColumn(), 13))
                    .getValues();
  const want = [
    { match: /holding\s*avg/i, label: 'Holding AVG Price', row: 1 },
    { match: /holding\s*volum/i, label: 'Holding Volume', row: 2 },
  ];
  const found = [];

  want.forEach(function (w) {
    for (let r = 0; r < scan.length; r++) {
      for (let c = 0; c < scan[r].length; c++) {
        if (typeof scan[r][c] === 'string' && w.match.test(scan[r][c])) {
          const value = scan[r][c + 1];
          // đã nằm đúng chỗ (L=12, M=13) thì thôi
          if (c + 1 !== 11) {
            sheet.getRange(r + 1, c + 1, 1, 2).clearContent();
          }
          sheet.getRange(w.row, 12).setValue(w.label + ':');
          sheet.getRange(w.row, 13).setValue(value === undefined ? '' : value);
          found.push(w.label + '=' + value);
          return;
        }
      }
    }
    found.push(w.label + '=không tìm thấy, để trống M' + w.row);
    sheet.getRange(w.row, 12).setValue(w.label + ':');
  });

  return found.join(', ');
}

/** Viết lại dòng tiêu đề. Trả về số dòng của nó. */
function writeHeaders_(sheet) {
  const lastRow = Math.max(sheet.getLastRow(), 1);
  const colA = sheet.getRange(1, 1, lastRow, 1).getValues();

  let headerRow = 0;
  for (let i = 0; i < colA.length; i++) {
    if (String(colA[i][0]).trim().toLowerCase() === 'date') {
      headerRow = i + 1;
      break;
    }
  }
  // chưa có dòng tiêu đề thì đặt ngay trên dòng dữ liệu đầu tiên
  if (!headerRow) headerRow = 3;

  sheet.getRange(headerRow, 1, 1, HEADERS.length)
       .setValues([HEADERS])
       .setFontWeight('bold');
  return headerRow;
}

/**
 * Xoá mọi dòng dưới tiêu đề mà cột B–I đều rỗng.
 *
 * Đây là định nghĩa "không giao dịch" đáng tin nhất có thể làm trong sheet:
 * không cần bảng ngày lễ âm lịch, không cần biết hôm đó sàn mở hay đóng —
 * dòng nào skill chưa từng ghi gì vào thì dòng đó không mang thông tin.
 *
 * Duyệt từ dưới lên: xoá từ trên xuống sẽ làm lệch chỉ số dòng.
 */
function deleteEmptyRows_(sheet, headerRow) {
  const lastRow = sheet.getLastRow();
  if (lastRow <= headerRow) return 0;

  const n = lastRow - headerRow;
  const data = sheet.getRange(headerRow + 1, 2, n, 8).getValues();  // B..I

  let removed = 0;
  for (let i = n - 1; i >= 0; i--) {
    const hasData = data[i].some(function (v) {
      return v !== '' && v !== null && v !== undefined;
    });
    if (!hasData) {
      sheet.deleteRow(headerRow + 1 + i);
      removed++;
    }
  }
  return removed;
}

/**
 * Cột J = lãi/lỗ chưa thực hiện, do sheet tự tính.
 *
 * Có guard rỗng để khi đứng ngoài (M2 trống) thì J không hiện số 0 giả —
 * 0 đồng lãi và không có vị thế là hai chuyện khác nhau.
 */
function setPnlFormulas_(sheet, headerRow) {
  const lastRow = sheet.getLastRow();
  if (lastRow <= headerRow) return 0;

  const formulas = [];
  for (let r = headerRow + 1; r <= lastRow; r++) {
    formulas.push(['=IF(OR($M$1="",$M$2="",$M$2=0,B' + r + '="",NOT(ISNUMBER(B' + r + '))),"",(B' + r + '-$M$1)*$M$2)']);
  }
  sheet.getRange(headerRow + 1, 10, formulas.length, 1).setFormulas(formulas);
  return formulas.length;
}
