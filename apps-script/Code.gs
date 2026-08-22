/**
 * Cầu ghi cho skill tpb-analysis.
 *
 * Chỉ ghi cột B–I của dòng khớp ngày. KHÔNG BAO GIỜ đụng vào:
 *   - cột L, M : vị thế do người dùng nhập
 *   - cột J    : công thức lãi/lỗ
 *
 * Idempotent: chạy hai lần cùng ngày thì ghi đè đúng dòng đó, không đẻ dòng trùng.
 */
const SHEET_NAME = 'TPB Stock Monitor';
const DATE_COL = 1;          // A
const FIRST_WRITE_COL = 2;   // B
// phải khớp đúng thứ tự mảng COLUMNS[1:] trong push_to_sheet.py
const FIELDS = ['close', 'volume', 'signal', 'confidence',
                'reason', 'levels', 'next_step', 'review'];  // B..I

function json_(obj) {
  return ContentService.createTextOutput(JSON.stringify(obj))
      .setMimeType(ContentService.MimeType.JSON);
}

/**
 * Tìm tab theo tên; không thấy thì rơi về tab đầu tiên.
 *
 * Bắt tên tab phải trùng chính xác là quá giòn — đổi tên tab một cái là hỏng
 * cả vòng ghi, mà thông báo lỗi lại không nói tab nào đang có.
 */
function pickSheet_(name) {
  const ss = SpreadsheetApp.getActive();
  const byName = ss.getSheetByName(name);
  if (byName) return byName;
  const all = ss.getSheets();
  return all.length ? all[0] : null;
}

function sameDay_(cell, wanted) {
  if (!cell) return false;
  const d = (cell instanceof Date)
      ? Utilities.formatDate(cell, 'GMT+7', 'yyyy-MM-dd')
      : String(cell).trim();
  if (d === wanted) return true;
  // sheet có thể hiển thị 08/21/2026 hoặc 2026/08/21
  const parts = wanted.split('-');
  return d === parts[1] + '/' + parts[2] + '/' + parts[0] ||
         d === wanted.replace(/-/g, '/');
}

function doPost(e) {
  try {
    const body = JSON.parse(e.postData.contents);
    const want = PropertiesService.getScriptProperties().getProperty('TOKEN');
    if (!want || body.token !== want) {
      return json_({ ok: false, error: 'unauthorized' });
    }
    if (!body.date) return json_({ ok: false, error: 'missing date' });

    const sheet = pickSheet_(body.sheet || SHEET_NAME);
    if (!sheet) {
      return json_({ ok: false, error: 'không có tab nào trong spreadsheet' });
    }

    // tìm dòng khớp ngày; không thấy thì thêm vào cuối
    const lastRow = Math.max(sheet.getLastRow(), 1);
    const dates = sheet.getRange(1, DATE_COL, lastRow, 1).getValues();
    let target = -1;
    for (let i = 0; i < dates.length; i++) {
      if (sameDay_(dates[i][0], body.date)) { target = i + 1; break; }
    }
    if (target === -1) {
      target = lastRow + 1;
      sheet.getRange(target, DATE_COL).setValue(body.date);
    }

    const values = FIELDS.map(function (f) {
      return (body[f] === undefined || body[f] === null) ? '' : body[f];
    });
    sheet.getRange(target, FIRST_WRITE_COL, 1, FIELDS.length)
         .setValues([values]);

    // trả cả tên tab để bên gọi biết chắc đã ghi vào đâu
    return json_({ ok: true, row: target, sheet: sheet.getName(),
                   written: FIELDS });
  } catch (err) {
    return json_({ ok: false, error: String(err) });
  }
}
