# TPB Analysis Skill — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Claude Code Skill that analyses TPB (HOSE) — chart, news, financials — and records every call into a Google Sheet plus a git-versioned journal so past judgements can be scored.

**Architecture:** Python fetches and computes numbers only; Claude interprets only. Data comes from Vietnamese sources first (Entrade for OHLCV + VN-Index/VN30, CafeF for index snapshot), with Yahoo narrowed to the one gap it alone fills — P/B and ROE across 22 listed banks. Memory lives in `data/journal/TPB.jsonl` (canonical, git) and mirrors to a Google Sheet through an Apps Script webhook.

**Tech Stack:** Python 3.9+ stdlib, `yfinance==1.2.0`, Google Apps Script, Claude Code Skill format.

**Spec:** `docs/superpowers/specs/2026-08-21-tpb-analysis-skill-design.md` (committed: `b49e144`)

---

## Context

The repo currently holds a third-party `stock-analysis` skill written for US equities, plus three unrelated scraped markdown files. Running it against Vietnamese tickers was verified to fail four ways: US-calibrated thresholds make **5 of 5 VN blue chips return BUY** (P/E < 15 fires on every VN stock because the market's P/E is structurally 10–14); VND prices print with a `$` sign; a hardcoded vote table impersonates investment judgement; and nothing persists between runs.

Ray holds/watches TPB and will invoke this repo from a prompt on Claude Cloud. Because each run is a cold session, memory must live outside the model. The point is not to predict price — it is to accumulate a **falsifiable** record of calls so that in three months it is knowable which were right.

Two design errors were caught by measuring real data rather than reasoning from assumption, and both are already fixed in the spec:
- Cross-checking two price sources across full history false-alarms on **32/343 sessions** (max 7.82% divergence) because providers adjust corporate actions on different dates. Cross-check is therefore narrowed to the latest close only, where the two sources agree exactly.
- TPB has **10 corporate actions since 2018**; 4 sessions in the last 500 moved beyond HOSE's ±7% band, one at exactly −10.00%. These are technical adjustments, not selling. Unfiltered, RSI/MACD read them as a crash.

## Global Constraints

- **All prices are integer VND.** Entrade returns thousands (`14.5`); Yahoo returns whole VND (`14500`). Conversion happens exactly once, at the source layer.
- **Indicators are computed from a single source's series (Entrade).** Never blend two providers' history.
- **Cross-check applies to the latest close only.** Divergence > 2% ⇒ warning + confidence `Thấp`.
- **Any close-to-close move beyond ±7% is a corporate action or data error**, never a market signal. Flag into `meta.warnings`, exclude from momentum narrative.
- **Missing data stays `null`.** Never substitute an estimate. Python emits numbers; Claude never computes new ones.
- **Secrets never enter git.** `SHEET_WEBHOOK` / `SHEET_TOKEN` arrive via CLI args or env, supplied in Ray's Cloud prompt.
- Pin `yfinance==1.2.0`. No silent `pip install` at runtime.
- Skill writes sheet columns **B–I only**. Columns L/M (position) and J (formula) are off-limits.

---

## File Structure

```
.claude/skills/tpb-analysis/
├── SKILL.md                     6-step procedure + the 4 hard rules
├── references/
│   ├── banking-metrics.md       bank reading frame, 3 comparisons
│   ├── sheet-contract.md        column contract A–J, L–M
│   └── data-sources.md          which source for what, failure modes
└── scripts/
    ├── requirements.txt
    ├── tpb/
    │   ├── __init__.py
    │   ├── units.py             VND normalisation          (Task 2)
    │   ├── indicators.py        RSI/MACD/SMA + ±7% filter  (Tasks 3, 4)
    │   ├── sources_vn.py        Entrade + CafeF            (Tasks 5, 6)
    │   ├── sources_yahoo.py     fundamentals + 22 banks    (Task 7)
    │   └── assemble.py          JSON contract + crosscheck (Task 8)
    ├── fetch_tpb.py             CLI entry                  (Task 9)
    ├── push_to_sheet.py         sheet bridge               (Task 10)
    └── tests/
        ├── test_units.py            test_indicators.py
        ├── test_corp_actions.py     test_assemble.py
        ├── test_sheet_row.py        test_degradation.py
        └── test_no_fabrication.py
apps-script/Code.gs                                          (Task 11)
data/journal/.gitkeep     reports/.gitkeep
```

Split by responsibility, not layer. `units.py` and `indicators.py` are pure functions with zero network and zero pandas — the two modules carrying the rules that previously broke, kept trivially testable.

---

## Task 1: Clear the repo and scaffold

**Files:**
- Delete: `stock-analysis/`, `ask-questions.md`, `best-practices-agents.md`, `code-documentation-skill.md`
- Rewrite: `README.md`
- Create: package dirs, `requirements.txt`, `.gitignore`

**Interfaces:** Produces the directory tree every later task writes into.

- [ ] **Step 1: Commit the baseline before deleting anything**

The old files are untracked — deleting them now is unrecoverable. Capture them first.

```bash
git add -A && git commit -m "chore: baseline trước khi xoá logic thị trường Mỹ"
```

- [ ] **Step 2: Delete the US-market logic**

```bash
git rm -r --quiet stock-analysis
git rm --quiet ask-questions.md best-practices-agents.md code-documentation-skill.md
```

- [ ] **Step 3: Create the tree**

```bash
mkdir -p .claude/skills/tpb-analysis/references
mkdir -p .claude/skills/tpb-analysis/scripts/tpb
mkdir -p .claude/skills/tpb-analysis/scripts/tests
mkdir -p apps-script data/journal reports
touch .claude/skills/tpb-analysis/scripts/tpb/__init__.py
touch data/journal/.gitkeep reports/.gitkeep
printf 'yfinance==1.2.0\n' > .claude/skills/tpb-analysis/scripts/requirements.txt
printf '__pycache__/\n*.pyc\n.venv/\n.env\n' > .gitignore
```

- [ ] **Step 4: Rewrite README.md**

```markdown
# vn-stock-analysis

Claude Code Skill phân tích cổ phiếu **TPB** (Ngân hàng TMCP Tiên Phong, HOSE).

Chạy bằng cách trỏ Claude vào repo này. Skill lấy số liệu từ nguồn Việt Nam
(Entrade, CafeF), đọc tin tức và BCTC, rồi ghi nhận định vào Google Sheet.

- Thiết kế: `docs/superpowers/specs/2026-08-21-tpb-analysis-skill-design.md`
- Bộ nhớ: `data/journal/TPB.jsonl` + Google Sheet

Không phải lời khuyên đầu tư.
```

- [ ] **Step 5: Verify only intended files remain, then commit**

```bash
git status --short && ls
git add -A && git commit -m "chore: xoá logic thị trường Mỹ, dựng khung skill TPB"
```

Expected: no trace of `analyze_stock.py`; `docs/` and the new tree present.

---

## Task 2: VND normalisation

**Files:**
- Create: `.claude/skills/tpb-analysis/scripts/tpb/units.py`
- Test: `.claude/skills/tpb-analysis/scripts/tests/test_units.py`

**Interfaces:**
- Produces: `entrade_to_vnd(x: float) -> int`, `yahoo_to_vnd(x: float) -> int`, `HOSE_LIMIT_PCT: float = 7.0`

- [ ] **Step 1: Write the failing test**

```python
# scripts/tests/test_units.py
from tpb.units import entrade_to_vnd, yahoo_to_vnd, HOSE_LIMIT_PCT

def test_entrade_thousands_to_vnd():
    assert entrade_to_vnd(14.5) == 14500
    assert entrade_to_vnd(6.9) == 6900

def test_yahoo_already_vnd():
    assert yahoo_to_vnd(14500.0) == 14500

def test_two_sources_agree_after_normalisation():
    # đây chính là lỗi đã giết script cũ: 14.5 và 14500 là cùng một giá
    assert entrade_to_vnd(14.5) == yahoo_to_vnd(14500.0)

def test_always_int_never_float():
    assert isinstance(entrade_to_vnd(14.5), int)
    assert isinstance(yahoo_to_vnd(14500.0), int)

def test_none_passes_through():
    assert entrade_to_vnd(None) is None
    assert yahoo_to_vnd(None) is None

def test_hose_limit_is_seven_percent():
    assert HOSE_LIMIT_PCT == 7.0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd .claude/skills/tpb-analysis/scripts && python3 -m pytest tests/test_units.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'tpb.units'`

- [ ] **Step 3: Write minimal implementation**

```python
# scripts/tpb/units.py
"""Chuẩn hoá đơn vị giá. Mọi giá trong hệ thống là VND nguyên, kiểu int.

Entrade trả giá theo nghìn đồng (14.5), Yahoo trả VND nguyên (14500).
Quy đổi xảy ra đúng một lần, tại đây, không nơi nào khác.
"""

HOSE_LIMIT_PCT = 7.0  # biên độ dao động một phiên của sàn HOSE


def entrade_to_vnd(value):
    """14.5 -> 14500. None đi xuyên qua."""
    if value is None:
        return None
    return int(round(float(value) * 1000))


def yahoo_to_vnd(value):
    """14500.0 -> 14500. None đi xuyên qua."""
    if value is None:
        return None
    return int(round(float(value)))
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/test_units.py -v`
Expected: 6 passed

- [ ] **Step 5: Commit**

```bash
git add .claude/skills/tpb-analysis/scripts/tpb/units.py .claude/skills/tpb-analysis/scripts/tests/test_units.py
git commit -m "feat: chuẩn hoá đơn vị giá về VND nguyên"
```

---

## Task 3: Technical indicators

**Files:**
- Create: `.claude/skills/tpb-analysis/scripts/tpb/indicators.py`
- Test: `.claude/skills/tpb-analysis/scripts/tests/test_indicators.py`

**Interfaces:**
- Consumes: nothing (pure functions, no pandas, no network)
- Produces: `ema(values, span) -> list[float]`, `sma(values, window) -> float | None`, `rsi(closes, period=14) -> float | None`, `macd(closes) -> dict` with keys `macd`, `signal`, `hist`

- [ ] **Step 1: Write the failing test**

Tests use sequences whose answers are verifiable by hand — not magic constants copied from another library.

```python
# scripts/tests/test_indicators.py
from tpb.indicators import ema, sma, rsi, macd

def test_sma_is_mean_of_last_window():
    # 5 phần tử cuối của 1..10 là 6,7,8,9,10 -> 40/5 = 8
    assert sma(list(range(1, 11)), 5) == 8.0

def test_sma_returns_none_when_series_too_short():
    assert sma([1, 2, 3], 5) is None

def test_ema_seeds_with_first_value():
    assert ema([100.0, 100.0, 100.0], 3)[0] == 100.0

def test_ema_of_constant_series_stays_constant():
    assert ema([50.0] * 20, 5)[-1] == 50.0

def test_rsi_is_100_when_every_session_gains():
    assert rsi([float(i) for i in range(1, 40)], 14) == 100.0

def test_rsi_is_0_when_every_session_loses():
    assert rsi([float(i) for i in range(40, 1, -1)], 14) == 0.0

def test_rsi_none_when_not_enough_history():
    assert rsi([1.0, 2.0, 3.0], 14) is None

def test_macd_of_constant_series_is_zero():
    out = macd([100.0] * 60)
    assert round(out["macd"], 9) == 0.0
    assert round(out["hist"], 9) == 0.0

def test_macd_positive_in_uptrend():
    out = macd([float(i) for i in range(1, 80)])
    assert out["macd"] > 0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_indicators.py -v`
Expected: FAIL — `No module named 'tpb.indicators'`

- [ ] **Step 3: Write minimal implementation**

```python
# scripts/tpb/indicators.py
"""Chỉ báo kỹ thuật, thuần Python, không phụ thuộc pandas.

Toàn bộ chỉ báo tính trên chuỗi của MỘT nguồn duy nhất. Trộn chuỗi của hai
nhà cung cấp sẽ tạo ra biến động không có thật tại các mốc sự kiện quyền.
"""


def ema(values, span):
    """Trung bình động luỹ thừa. Phần tử đầu lấy chính giá trị đầu làm mầm."""
    if not values:
        return []
    k = 2.0 / (span + 1)
    acc = float(values[0])
    out = [acc]
    for v in values[1:]:
        acc = float(v) * k + acc * (1 - k)
        out.append(acc)
    return out


def sma(values, window):
    """Trung bình động giản đơn của `window` phần tử cuối."""
    if len(values) < window:
        return None
    return sum(float(v) for v in values[-window:]) / window


def rsi(closes, period=14):
    """RSI theo phương pháp làm mượt Wilder."""
    if len(closes) < period + 1:
        return None
    gains, losses = [], []
    for prev, cur in zip(closes, closes[1:]):
        d = float(cur) - float(prev)
        gains.append(max(d, 0.0))
        losses.append(max(-d, 0.0))
    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period
    for g, l in zip(gains[period:], losses[period:]):
        avg_gain = (avg_gain * (period - 1) + g) / period
        avg_loss = (avg_loss * (period - 1) + l) / period
    if avg_loss == 0:
        return 100.0 if avg_gain > 0 else 50.0
    rs = avg_gain / avg_loss
    return 100.0 - 100.0 / (1.0 + rs)


def macd(closes, fast=12, slow=26, signal=9):
    """MACD 12/26/9. Trả về dict rỗng-an-toàn nếu chuỗi quá ngắn."""
    if len(closes) < slow:
        return {"macd": None, "signal": None, "hist": None}
    fast_line = ema(closes, fast)
    slow_line = ema(closes, slow)
    macd_series = [f - s for f, s in zip(fast_line, slow_line)]
    signal_series = ema(macd_series, signal)
    m, s = macd_series[-1], signal_series[-1]
    return {"macd": m, "signal": s, "hist": m - s}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/test_indicators.py -v`
Expected: 9 passed

- [ ] **Step 5: Commit**

```bash
git add .claude/skills/tpb-analysis/scripts/tpb/indicators.py .claude/skills/tpb-analysis/scripts/tests/test_indicators.py
git commit -m "feat: chỉ báo RSI/MACD/SMA thuần Python"
```

---

## Task 4: Corporate-action filter (±7% band)

**Files:**
- Modify: `.claude/skills/tpb-analysis/scripts/tpb/indicators.py`
- Test: `.claude/skills/tpb-analysis/scripts/tests/test_corp_actions.py`

**Interfaces:**
- Consumes: `HOSE_LIMIT_PCT` from `tpb.units`
- Produces: `flag_limit_breaks(dates, closes, limit=HOSE_LIMIT_PCT) -> list[dict]` — each dict has `date`, `change_pct`

This is the rule that keeps a −10.00% adjustment from being narrated as a crash. It exists because measurement found 4 such sessions in TPB's last 500.

- [ ] **Step 1: Write the failing test**

```python
# scripts/tests/test_corp_actions.py
from tpb.indicators import flag_limit_breaks

DATES = ["2026-08-17", "2026-08-18", "2026-08-19", "2026-08-20"]

def test_flags_move_beyond_hose_band():
    # 10000 -> 9000 là -10%, bất khả thi trong một phiên HOSE bình thường
    flags = flag_limit_breaks(DATES, [10000, 9000, 9000, 9000])
    assert len(flags) == 1
    assert flags[0]["date"] == "2026-08-18"
    assert flags[0]["change_pct"] == -10.0

def test_ignores_move_inside_the_band():
    # -6.9% là biến động thị trường hợp lệ, không được gắn cờ
    flags = flag_limit_breaks(DATES, [10000, 9310, 9310, 9310])
    assert flags == []

def test_flags_upside_break_too():
    flags = flag_limit_breaks(DATES, [10000, 10800, 10800, 10800])
    assert len(flags) == 1
    assert flags[0]["change_pct"] == 8.0

def test_empty_series_is_safe():
    assert flag_limit_breaks([], []) == []

def test_zero_previous_close_does_not_divide_by_zero():
    assert flag_limit_breaks(DATES, [0, 9000, 9000, 9000]) == []
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_corp_actions.py -v`
Expected: FAIL — `cannot import name 'flag_limit_breaks'`

- [ ] **Step 3: Append the implementation to indicators.py**

```python
from .units import HOSE_LIMIT_PCT


def flag_limit_breaks(dates, closes, limit=HOSE_LIMIT_PCT):
    """Tìm các phiên có biến động đóng-cửa-sang-đóng-cửa vượt biên độ sàn.

    Vượt biên độ nghĩa là sự kiện quyền hoặc lỗi dữ liệu, KHÔNG phải tín hiệu
    thị trường. Bằng chứng: TPB có 4 phiên như vậy trong 500 phiên gần nhất,
    trong đó 08/09/2025 giảm đúng -10,00%.
    """
    flags = []
    for i in range(1, len(closes)):
        prev = float(closes[i - 1])
        if prev == 0:
            continue
        change = (float(closes[i]) - prev) / prev * 100.0
        if abs(change) > limit:
            flags.append({"date": dates[i], "change_pct": round(change, 2)})
    return flags
```

- [ ] **Step 4: Run the full suite**

Run: `python3 -m pytest tests/ -v`
Expected: all passed (units + indicators + corp actions)

- [ ] **Step 5: Commit**

```bash
git add .claude/skills/tpb-analysis/scripts/tpb/indicators.py .claude/skills/tpb-analysis/scripts/tests/test_corp_actions.py
git commit -m "feat: bộ lọc biên độ ±7% cho sự kiện quyền"
```

---

## Task 5: Entrade source (OHLCV + VN-Index + VN30)

**Files:**
- Create: `.claude/skills/tpb-analysis/scripts/tpb/sources_vn.py`
- Test: `.claude/skills/tpb-analysis/scripts/tests/test_sources.py`

**Interfaces:**
- Consumes: `entrade_to_vnd` from `tpb.units`
- Produces: `parse_entrade(payload) -> dict` with keys `dates: list[str]`, `closes: list[int]`, `volumes: list[int]`; `fetch_entrade(symbol, days=400, kind="stock") -> dict | None`

Verified live: `/ohlcs/stock?symbol=TPB` and `/ohlcs/index?symbol=VNINDEX|VN30` both return 274 sessions.

- [ ] **Step 1: Write the failing test**

Parsing is tested against a fixture, not the network — the test must stay green offline.

```python
# scripts/tests/test_sources.py
from tpb.sources_vn import parse_entrade

PAYLOAD = {
    "t": [1755388800, 1755475200],   # 2025-08-17, 2025-08-18
    "o": [14.4, 14.35], "h": [14.5, 14.5], "l": [14.3, 14.2],
    "c": [14.35, 14.5], "v": [3707900, 7658000],
}

def test_converts_thousands_to_integer_vnd():
    out = parse_entrade(PAYLOAD)
    assert out["closes"] == [14350, 14500]
    assert all(isinstance(c, int) for c in out["closes"])

def test_dates_are_iso_strings():
    out = parse_entrade(PAYLOAD)
    assert out["dates"][0] == "2025-08-17"

def test_volumes_preserved_as_int():
    assert parse_entrade(PAYLOAD)["volumes"] == [3707900, 7658000]

def test_empty_payload_returns_none():
    assert parse_entrade({"t": [], "c": []}) is None
    assert parse_entrade(None) is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_sources.py -v`
Expected: FAIL — `No module named 'tpb.sources_vn'`

- [ ] **Step 3: Write minimal implementation**

```python
# scripts/tpb/sources_vn.py
"""Nguồn dữ liệu Việt Nam: Entrade (DNSE) và CafeF.

Entrade  — OHLCV cổ phiếu, VN-Index, VN30, có lịch sử.
CafeF    — ảnh chụp chỉ số kèm giá trị giao dịch.
Cả hai đều là API công khai, không cần khoá.
"""
import datetime as dt
import json
import ssl
import time
import urllib.request

from .units import entrade_to_vnd

_CTX = ssl.create_default_context()   # không bao giờ tắt xác thực chứng chỉ
_UA = {
    "User-Agent": ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                   "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"),
    "Accept": "application/json, text/plain, */*",
}
ENTRADE = "https://services.entrade.com.vn/chart-api/v2/ohlcs"


def _get_json(url, referer=None, timeout=25):
    headers = dict(_UA)
    if referer:
        headers["Referer"] = referer
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout, context=_CTX) as resp:
        return json.loads(resp.read().decode("utf-8", "replace"))


def parse_entrade(payload):
    """Payload Entrade -> {dates, closes(VND int), volumes}. Rỗng -> None."""
    if not payload or not payload.get("t"):
        return None
    return {
        "dates": [dt.datetime.utcfromtimestamp(t).strftime("%Y-%m-%d")
                  for t in payload["t"]],
        "closes": [entrade_to_vnd(c) for c in payload["c"]],
        "volumes": [int(v) for v in payload.get("v", [])],
    }


def fetch_entrade(symbol, days=400, kind="stock"):
    """kind='stock' cho cổ phiếu, kind='index' cho VNINDEX/VN30. Lỗi -> None."""
    now = int(time.time())
    url = (f"{ENTRADE}/{kind}?from={now - days * 86400}&to={now}"
           f"&symbol={symbol}&resolution=1D")
    try:
        return parse_entrade(_get_json(url))
    except Exception:
        return None
```

> Note on index series: Entrade index closes are already point values, not thousands. Task 8 calls `fetch_entrade(..., kind="index")` and must read `payload["c"]` directly rather than the VND-converted `closes`. Add `raw_closes` to the parse output if Task 8 needs it — see Task 8 Step 3.

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/test_sources.py -v`
Expected: 4 passed

- [ ] **Step 5: Smoke-test against the live API, then commit**

```bash
python3 -c "
from tpb.sources_vn import fetch_entrade
d = fetch_entrade('TPB')
print('phiên:', len(d['dates']), 'gần nhất:', d['dates'][-1], d['closes'][-1])
"
```
Expected: ~270+ sessions, latest close a 5-digit integer such as `14500`.

```bash
git add .claude/skills/tpb-analysis/scripts/tpb/sources_vn.py .claude/skills/tpb-analysis/scripts/tests/test_sources.py
git commit -m "feat: nguồn Entrade cho OHLCV và chỉ số"
```

---

## Task 6: CafeF index snapshot

**Files:**
- Modify: `.claude/skills/tpb-analysis/scripts/tpb/sources_vn.py`
- Modify: `.claude/skills/tpb-analysis/scripts/tests/test_sources.py`

**Interfaces:**
- Produces: `parse_cafef_indices(rows) -> dict` keyed by index name, each `{value, change, change_pct, volume, value_bn}`; `fetch_cafef_indices() -> dict | None`

Verified live: returns VNINDEX, HNXINDEX, HNXUPCOMINDEX, VN30, HNX30 with comma-grouped string numbers.

- [ ] **Step 1: Write the failing test**

```python
# append to scripts/tests/test_sources.py
from tpb.sources_vn import parse_cafef_indices

CAFEF_ROWS = [
    {"change": "7.55", "index": "1,734.24", "name": "VNINDEX",
     "percent": "0.44", "volume": "464,412,231", "value": "13,471.96"},
    {"change": "11.33", "index": "1,887.06", "name": "VN30",
     "percent": "0.60", "volume": "203,541,056", "value": "8,063.95"},
]

def test_strips_thousand_separators_to_float():
    out = parse_cafef_indices(CAFEF_ROWS)
    assert out["VNINDEX"]["value"] == 1734.24
    assert out["VNINDEX"]["volume"] == 464412231

def test_keeps_percent_change():
    out = parse_cafef_indices(CAFEF_ROWS)
    assert out["VN30"]["change_pct"] == 0.60

def test_trading_value_in_billions():
    assert parse_cafef_indices(CAFEF_ROWS)["VNINDEX"]["value_bn"] == 13471.96

def test_empty_rows_return_none():
    assert parse_cafef_indices([]) is None
    assert parse_cafef_indices(None) is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_sources.py -v`
Expected: FAIL — `cannot import name 'parse_cafef_indices'`

- [ ] **Step 3: Append the implementation**

```python
CAFEF_INDICES = "https://banggia.cafef.vn/stockhandler.ashx?index=true"


def _num(text):
    """'1,734.24' -> 1734.24 ; '' -> None"""
    if text is None:
        return None
    cleaned = str(text).replace(",", "").strip()
    if not cleaned:
        return None
    try:
        return float(cleaned)
    except ValueError:
        return None


def parse_cafef_indices(rows):
    """Danh sách chỉ số CafeF -> dict theo tên. Rỗng -> None."""
    if not rows:
        return None
    out = {}
    for row in rows:
        name = row.get("name")
        if not name:
            continue
        volume = _num(row.get("volume"))
        out[name] = {
            "value": _num(row.get("index")),
            "change": _num(row.get("change")),
            "change_pct": _num(row.get("percent")),
            "volume": int(volume) if volume is not None else None,
            "value_bn": _num(row.get("value")),
        }
    return out or None


def fetch_cafef_indices():
    """Ảnh chụp VN-Index / VN30 / HNX / UPCoM. Lỗi -> None (không chặn luồng)."""
    try:
        return parse_cafef_indices(
            _get_json(CAFEF_INDICES, referer="https://banggia.cafef.vn/"))
    except Exception:
        return None
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/ -v`
Expected: all passed

- [ ] **Step 5: Smoke-test live, then commit**

```bash
python3 -c "
from tpb.sources_vn import fetch_cafef_indices
d = fetch_cafef_indices()
print('VN-Index', d['VNINDEX']['value'], d['VNINDEX']['change_pct'], '%')
print('VN30    ', d['VN30']['value'], d['VN30']['change_pct'], '%')
"
```

```bash
git add .claude/skills/tpb-analysis/scripts/tpb/sources_vn.py .claude/skills/tpb-analysis/scripts/tests/test_sources.py
git commit -m "feat: ảnh chụp chỉ số VN-Index/VN30 từ CafeF"
```

> **Known unknown — foreign flow.** The spec lists foreign net buy/sell as a metric. CafeF's `?center=1` board was verified to return data but its column letters (`a`–`z`) were **not** decoded to a documented schema, so no field name can be asserted here. Handle it honestly: leave `foreign: null` in the JSON contract and add `"khối ngoại: chưa có nguồn tự động"` to `meta.warnings`. Do **not** invent field names. If Ray wants it later, that is its own task starting with decoding the board payload.

---

## Task 7: Yahoo fundamentals + 22-bank sector

**Files:**
- Create: `.claude/skills/tpb-analysis/scripts/tpb/sources_yahoo.py`
- Test: `.claude/skills/tpb-analysis/scripts/tests/test_no_fabrication.py`

**Interfaces:**
- Consumes: `yahoo_to_vnd` from `tpb.units`
- Produces: `BANKS: list[str]`, `extract_fundamentals(info: dict) -> dict`, `sector_stats(peers: list[dict]) -> dict`, `fetch_bank(code) -> dict | None`, `fetch_sector() -> list[dict]`

Yahoo is narrowed to exactly one job: P/B and ROE across listed banks. No VN source serves these without auth.

- [ ] **Step 1: Write the failing test**

```python
# scripts/tests/test_no_fabrication.py
from tpb.sources_yahoo import extract_fundamentals, sector_stats, BANKS

def test_all_22_banks_listed():
    assert len(BANKS) == 22
    assert "TPB" in BANKS and "SHB" in BANKS

def test_missing_fields_stay_none_not_zero():
    # nguồn trả rỗng thì phải là None, tuyệt đối không bịa số
    out = extract_fundamentals({})
    assert out["pb"] is None
    assert out["roe"] is None
    assert out["pb_per_roe"] is None

def test_extracts_and_derives_pb_per_roe():
    out = extract_fundamentals({"priceToBook": 0.88, "returnOnEquity": 0.174})
    assert out["pb"] == 0.88
    assert round(out["pb_per_roe"], 3) == 0.051   # 0.88 / 17.4

def test_pb_per_roe_none_when_roe_is_zero():
    out = extract_fundamentals({"priceToBook": 1.0, "returnOnEquity": 0.0})
    assert out["pb_per_roe"] is None

def test_sector_median_ignores_incomplete_peers():
    peers = [
        {"code": "TPB", "pb": 0.88, "roe": 0.174, "pb_per_roe": 0.051},
        {"code": "SHB", "pb": 0.78, "roe": 0.175, "pb_per_roe": 0.045},
        {"code": "XXX", "pb": None, "roe": None, "pb_per_roe": None},
    ]
    stats = sector_stats(peers)
    assert stats["n"] == 2                      # mã thiếu dữ liệu bị loại
    assert stats["median_pb"] == 0.83
    assert stats["rank_pb_per_roe"]["TPB"] == 2  # SHB rẻ hơn -> hạng 1

def test_sector_stats_empty_is_safe():
    assert sector_stats([])["n"] == 0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_no_fabrication.py -v`
Expected: FAIL — `No module named 'tpb.sources_yahoo'`

- [ ] **Step 3: Write minimal implementation**

```python
# scripts/tpb/sources_yahoo.py
"""Yahoo Finance — chỉ dùng cho chỉ số cơ bản của ngành ngân hàng.

Không nguồn Việt Nam nào cung cấp P/B và ROE mà không cần auth (TCBS bị
Cloudflare chặn, VNDirect 406/timeout, Simplize 404, Fireant 401).
Toàn bộ dữ liệu giá và chỉ số thị trường lấy từ nguồn Việt Nam.
"""
import statistics

from .units import yahoo_to_vnd

# 22 ngân hàng niêm yết lấy được dữ liệu, kiểm chứng ngày 2026-08-21
BANKS = ["VCB", "BID", "CTG", "TCB", "VPB", "MBB", "ACB", "HDB", "STB", "TPB",
         "VIB", "SHB", "LPB", "MSB", "OCB", "EIB", "SSB", "NAB", "KLB", "VAB",
         "BVB", "VBB"]


def extract_fundamentals(info):
    """dict `.info` của yfinance -> chỉ số cơ bản. Thiếu thì None, không bịa."""
    info = info or {}
    pb = info.get("priceToBook")
    roe = info.get("returnOnEquity")
    pb_per_roe = None
    if pb is not None and roe:            # roe = 0 cũng bị loại, tránh chia 0
        pb_per_roe = pb / (roe * 100.0)
    return {
        "pb": pb,
        "roe": roe,
        "pe": info.get("trailingPE"),
        "book_value": yahoo_to_vnd(info.get("bookValue")),
        "eps": yahoo_to_vnd(info.get("trailingEps")),
        "analyst_target": yahoo_to_vnd(info.get("targetMeanPrice")),
        "analyst_count": info.get("numberOfAnalystOpinions"),
        "market_cap": info.get("marketCap"),
        "pb_per_roe": pb_per_roe,
    }


def sector_stats(peers):
    """Trung vị ngành và xếp hạng theo P/B÷ROE. Mã thiếu dữ liệu bị loại."""
    usable = [p for p in peers if p.get("pb") and p.get("pb_per_roe")]
    if not usable:
        return {"n": 0, "median_pb": None, "median_roe": None,
                "median_pb_per_roe": None, "rank_pb_per_roe": {}}
    ordered = sorted(usable, key=lambda p: p["pb_per_roe"])   # rẻ nhất hạng 1
    return {
        "n": len(usable),
        "median_pb": round(statistics.median([p["pb"] for p in usable]), 4),
        "median_roe": round(statistics.median(
            [p["roe"] for p in usable if p.get("roe")]), 4),
        "median_pb_per_roe": round(statistics.median(
            [p["pb_per_roe"] for p in usable]), 4),
        "rank_pb_per_roe": {p["code"]: i + 1 for i, p in enumerate(ordered)},
    }


def fetch_bank(code):
    """Chỉ số cơ bản một ngân hàng. Lỗi -> None."""
    try:
        import yfinance as yf
        info = yf.Ticker(f"{code}.VN").info
    except Exception:
        return None
    out = extract_fundamentals(info)
    out["code"] = code
    return out


def fetch_sector(codes=None):
    """Quét toàn ngành. Mã nào hỏng thì bỏ qua, không làm chết cả lượt."""
    results = []
    for code in (codes or BANKS):
        row = fetch_bank(code)
        if row:
            results.append(row)
    return results
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/test_no_fabrication.py -v`
Expected: 6 passed

- [ ] **Step 5: Commit**

```bash
git add .claude/skills/tpb-analysis/scripts/tpb/sources_yahoo.py .claude/skills/tpb-analysis/scripts/tests/test_no_fabrication.py
git commit -m "feat: chỉ số cơ bản ngành ngân hàng từ Yahoo"
```

---

## Task 8: Assemble the JSON contract

**Files:**
- Create: `.claude/skills/tpb-analysis/scripts/tpb/assemble.py`
- Test: `.claude/skills/tpb-analysis/scripts/tests/test_assemble.py`

**Interfaces:**
- Consumes: `rsi`, `macd`, `sma`, `flag_limit_breaks` (`tpb.indicators`); `sector_stats` (`tpb.sources_yahoo`)
- Produces: `cross_check(entrade_close, yahoo_close, tol_pct=2.0) -> dict`; `rel_strength(stock_closes, index_closes, window=20) -> float | None`; `build(...) -> dict` matching spec §6

- [ ] **Step 1: Write the failing test**

```python
# scripts/tests/test_assemble.py
from tpb.assemble import cross_check, rel_strength

def test_cross_check_passes_when_sources_agree():
    out = cross_check(14500, 14500)
    assert out["ok"] is True and out["diff_pct"] == 0.0

def test_cross_check_fails_beyond_two_percent():
    out = cross_check(14500, 13000)   # lệch ~11,5%
    assert out["ok"] is False
    assert out["diff_pct"] > 2.0

def test_cross_check_tolerates_small_gap():
    assert cross_check(14500, 14400)["ok"] is True   # 0,69%

def test_cross_check_missing_source_is_not_a_failure():
    out = cross_check(14500, None)
    assert out["ok"] is True and out["diff_pct"] is None

def test_rel_strength_zero_when_stock_matches_market():
    stock = [100, 110]; index = [1000, 1100]        # cả hai +10%
    assert round(rel_strength(stock, index, window=1), 6) == 0.0

def test_rel_strength_negative_when_stock_lags():
    stock = [100, 105]; index = [1000, 1100]        # +5% so với +10%
    assert round(rel_strength(stock, index, window=1), 2) == -5.0

def test_rel_strength_none_when_history_too_short():
    assert rel_strength([100], [1000], window=20) is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_assemble.py -v`
Expected: FAIL — `No module named 'tpb.assemble'`

- [ ] **Step 3: Write minimal implementation**

```python
# scripts/tpb/assemble.py
"""Ghép dữ liệu các nguồn thành đúng hợp đồng JSON ở mục 6 của spec.

Ranh giới: mọi con số dừng lại ở đây. Claude đọc JSON này và chỉ diễn giải,
không tính thêm số nào.
"""
import datetime as dt

from .indicators import flag_limit_breaks, macd, rsi, sma
from .sources_yahoo import sector_stats

CROSS_CHECK_TOL_PCT = 2.0


def cross_check(entrade_close, yahoo_close, tol_pct=CROSS_CHECK_TOL_PCT):
    """Đối chiếu CHỈ giá đóng cửa phiên gần nhất.

    Không quét toàn chuỗi: đo thực tế cho thấy 32/343 phiên lệch trên 2% tại
    các mốc sự kiện quyền, trong khi phiên gần nhất hai nguồn khớp tuyệt đối.
    """
    if entrade_close is None or yahoo_close is None or not yahoo_close:
        return {"entrade": entrade_close, "yahoo": yahoo_close,
                "diff_pct": None, "ok": True}
    diff = abs(entrade_close - yahoo_close) / yahoo_close * 100.0
    return {"entrade": entrade_close, "yahoo": yahoo_close,
            "diff_pct": round(diff, 2), "ok": diff <= tol_pct}


def rel_strength(stock_closes, index_closes, window=20):
    """Hiệu suất cổ phiếu trừ hiệu suất chỉ số, tính theo `window` phiên.

    Trả lời: TPB yếu vì bản thân nó, hay vì cả thị trường đang yếu.
    """
    if len(stock_closes) <= window or len(index_closes) <= window:
        return None
    def pct(series):
        start, end = float(series[-1 - window]), float(series[-1])
        return None if start == 0 else (end - start) / start * 100.0
    a, b = pct(stock_closes), pct(index_closes)
    return None if a is None or b is None else a - b


def build(ohlcv, fundamentals, peers, indices, index_series, position=None,
          sources_ok=None, sources_failed=None, yahoo_close=None):
    """Dựng object JSON hoàn chỉnh. Trường nào thiếu thì để None."""
    warnings = []
    closes = ohlcv["closes"] if ohlcv else []
    dates = ohlcv["dates"] if ohlcv else []
    volumes = ohlcv["volumes"] if ohlcv else []
    close = closes[-1] if closes else None

    breaks = flag_limit_breaks(dates, closes)
    if breaks:
        warnings.append(
            f"{len(breaks)} phiên vượt biên độ ±7% — sự kiện quyền hoặc lỗi "
            f"dữ liệu, đã loại khỏi diễn giải động lượng: "
            f"{[b['date'] for b in breaks[-3:]]}")

    xc = cross_check(close, yahoo_close)
    if not xc["ok"]:
        warnings.append(
            f"Hai nguồn giá lệch {xc['diff_pct']}% — hạ độ tin xuống Thấp")

    vol_avg20 = sma(volumes, 20) if volumes else None
    vol = volumes[-1] if volumes else None
    if vol and vol_avg20 and vol < vol_avg20 * 0.5:
        warnings.append("KLGD dưới 50% trung bình 20 phiên — hạ độ tin phần kỹ thuật")

    warnings.append("khối ngoại: chưa có nguồn tự động")

    m = macd(closes) if closes else {"macd": None, "signal": None, "hist": None}
    f = fundamentals or {}
    vn = (indices or {}).get("VNINDEX") or {}
    vn30 = (indices or {}).get("VN30") or {}

    pos = dict(position or {})
    if pos.get("avg_price") and pos.get("volume") and close:
        pos["unrealized_pl"] = int((close - pos["avg_price"]) * pos["volume"])
    else:
        pos.setdefault("avg_price", None)
        pos.setdefault("volume", None)
        pos["unrealized_pl"] = None

    return {
        "meta": {
            "ticker": "TPB",
            "run_at": dt.datetime.now().astimezone().isoformat(timespec="seconds"),
            "session_date": dates[-1] if dates else None,
            "is_trading_day": bool(dates),
            "sources_ok": sources_ok or [],
            "sources_failed": sources_failed or [],
            "warnings": warnings,
            "limit_breaks": breaks,
        },
        "price": {
            "close": close,
            "volume": vol,
            "volume_avg20": int(vol_avg20) if vol_avg20 else None,
            "volume_ratio": round(vol / vol_avg20, 2) if vol and vol_avg20 else None,
            "high_52w": max(closes[-250:]) if closes else None,
            "low_52w": min(closes[-250:]) if closes else None,
            "cross_check": xc,
        },
        "technicals": {
            "rsi14": round(rsi(closes), 1) if closes else None,
            "macd": m["macd"], "macd_signal": m["signal"], "macd_hist": m["hist"],
            "sma20": int(sma(closes, 20)) if sma(closes, 20) else None,
            "sma50": int(sma(closes, 50)) if sma(closes, 50) else None,
            "sma200": int(sma(closes, 200)) if sma(closes, 200) else None,
        },
        "valuation": {
            "pb": f.get("pb"), "roe": f.get("roe"), "pe": f.get("pe"),
            "book_value": f.get("book_value"),
            "analyst_target": f.get("analyst_target"),
            "analyst_count": f.get("analyst_count"),
            "pb_per_roe": f.get("pb_per_roe"),
            "sector": sector_stats(peers or []),
            "peers": peers or [],
        },
        "market": {
            "vnindex": vn or None,
            "vn30": vn30 or None,
            "tpb_rel_strength_20d": round(
                rel_strength(closes, index_series or []), 2)
            if closes and index_series and
            rel_strength(closes, index_series or []) is not None else None,
        },
        "foreign": None,
        "position": pos,
    }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/ -v`
Expected: all passed

- [ ] **Step 5: Commit**

```bash
git add .claude/skills/tpb-analysis/scripts/tpb/assemble.py .claude/skills/tpb-analysis/scripts/tests/test_assemble.py
git commit -m "feat: dựng hợp đồng JSON, đối chiếu chéo, sức mạnh tương đối"
```

---

## Task 9: CLI entry `fetch_tpb.py`

**Files:**
- Create: `.claude/skills/tpb-analysis/scripts/fetch_tpb.py`

**Interfaces:**
- Consumes: everything from Tasks 5–8
- Produces: a single JSON object on stdout. CLI: `--holding-avg`, `--holding-volume`, `--days`

Position values come from Claude reading the Sheet and passing them in — `fetch_tpb.py` has no Google credentials and must never try to read the Sheet itself.

- [ ] **Step 1: Write the implementation**

```python
#!/usr/bin/env python3
"""fetch_tpb.py — thu thập số liệu TPB, in ra một object JSON trên stdout.

Đây là toàn bộ phần "tính toán" của skill. Claude đọc JSON này và chỉ diễn
giải; Claude không tính thêm bất kỳ con số nào.

    python3 fetch_tpb.py
    python3 fetch_tpb.py --holding-avg 14200 --holding-volume 5000
"""
import argparse
import json
import sys

from tpb.assemble import build
from tpb.sources_vn import fetch_cafef_indices, fetch_entrade
from tpb.sources_yahoo import fetch_bank, fetch_sector


def main():
    ap = argparse.ArgumentParser(description="Thu thập số liệu TPB")
    ap.add_argument("--holding-avg", type=int, default=None,
                    help="Giá vốn bình quân (VND), Claude đọc từ ô M1 của sheet")
    ap.add_argument("--holding-volume", type=int, default=None,
                    help="Số lượng đang nắm, Claude đọc từ ô M2 của sheet")
    ap.add_argument("--days", type=int, default=400)
    args = ap.parse_args()

    ok, failed = [], []

    ohlcv = fetch_entrade("TPB", days=args.days)
    (ok if ohlcv else failed).append("entrade")
    if not ohlcv:
        print("Lỗi: không lấy được dữ liệu giá TPB từ Entrade.", file=sys.stderr)

    index_raw = fetch_entrade("VNINDEX", days=args.days, kind="index")
    # chỉ số là điểm số, không phải giá nghìn đồng -> lấy lại giá trị gốc
    index_series = [c / 1000.0 for c in index_raw["closes"]] if index_raw else []

    indices = fetch_cafef_indices()
    (ok if indices else failed).append("cafef")

    fundamentals = fetch_bank("TPB")
    (ok if fundamentals else failed).append("yahoo")
    yahoo_close = None
    peers = fetch_sector() if fundamentals else []

    if not ohlcv and not fundamentals:
        print("Lỗi: cả Entrade lẫn Yahoo đều không phản hồi. Dừng.", file=sys.stderr)
        sys.exit(1)

    payload = build(
        ohlcv=ohlcv, fundamentals=fundamentals, peers=peers,
        indices=indices, index_series=index_series,
        position={"avg_price": args.holding_avg, "volume": args.holding_volume},
        sources_ok=ok, sources_failed=failed, yahoo_close=yahoo_close,
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run it and inspect the contract**

```bash
cd .claude/skills/tpb-analysis/scripts
python3 fetch_tpb.py > /tmp/tpb.json && python3 -c "
import json; d = json.load(open('/tmp/tpb.json'))
print('phiên   :', d['meta']['session_date'])
print('giá     :', d['price']['close'], 'VND')
print('RSI/MACD:', d['technicals']['rsi14'], round(d['technicals']['macd_hist'], 1))
print('P/B, ROE:', d['valuation']['pb'], d['valuation']['roe'])
print('ngành n :', d['valuation']['sector']['n'], 'hạng TPB:',
      d['valuation']['sector']['rank_pb_per_roe'].get('TPB'))
print('VN-Index:', d['market']['vnindex']['value'])
print('cảnh báo:', d['meta']['warnings'])
"
```

Expected: close is a 5-digit int; `sector.n` around 20–22; VN-Index near 1,7xx; warnings mention the ±7% breaks and the missing foreign flow.

- [ ] **Step 3: Verify prices are integers, not floats**

```bash
python3 -c "
import json; d = json.load(open('/tmp/tpb.json'))
assert isinstance(d['price']['close'], int), 'giá phải là int VND'
assert d['price']['close'] > 1000, 'giá phải là VND nguyên, không phải nghìn đồng'
print('OK — đơn vị đúng')
"
```

- [ ] **Step 4: Commit**

```bash
git add .claude/skills/tpb-analysis/scripts/fetch_tpb.py
git commit -m "feat: CLI fetch_tpb.py in ra hợp đồng JSON"
```

---

## Task 10: Sheet bridge `push_to_sheet.py`

**Files:**
- Create: `.claude/skills/tpb-analysis/scripts/push_to_sheet.py`
- Test: `.claude/skills/tpb-analysis/scripts/tests/test_sheet_row.py`, `tests/test_degradation.py`

**Interfaces:**
- Produces: `build_row(**kwargs) -> dict` with exactly keys `date, close, volume, signal, confidence, reason, levels, next_step, review`; `push(row, webhook, token) -> dict`; `format_manual(row) -> str`

Missing webhook must never crash — it prints a paste-ready line instead.

- [ ] **Step 1: Write the failing tests**

```python
# scripts/tests/test_sheet_row.py
from push_to_sheet import build_row

FULL = dict(date="2026-08-21", close=14500, volume="6,285,000 (68% TB20)",
            signal="GIỮ", confidence="TB", reason="P/B 0,88 vs trung vị ngành 1,10",
            levels="HT 14.300 / KC 15.400 / CL 13.700",
            next_step="nếu đóng cửa trên 15.400 thì xem xét gia tăng",
            review="Đúng — nhận định 5 phiên trước về vùng hỗ trợ đã đúng")

def test_row_has_exactly_the_eight_writable_columns_plus_date():
    row = build_row(**FULL)
    assert list(row.keys()) == ["date", "close", "volume", "signal",
                                "confidence", "reason", "levels",
                                "next_step", "review"]

def test_row_never_contains_holding_or_pl_columns():
    # cột L, M là của người dùng; cột J là công thức — skill không được đụng
    row = build_row(**FULL)
    for forbidden in ("holding_avg", "holding_volume", "pl"):
        assert forbidden not in row

def test_non_trading_day_uses_dash_and_blanks():
    row = build_row(date="2026-08-22", close=None, volume=None, signal=None,
                    confidence=None, reason=None, levels=None,
                    next_step=None, review=None)
    assert row["close"] == "—"
    assert row["signal"] == ""
```

```python
# scripts/tests/test_degradation.py
from push_to_sheet import format_manual, push

ROW = {"date": "2026-08-21", "close": 14500, "volume": "6,285,000",
       "signal": "GIỮ", "confidence": "TB", "reason": "P/B 0,88",
       "levels": "HT 14.300", "next_step": "nếu vượt 15.400 thì...",
       "review": "Chưa rõ"}

def test_missing_webhook_returns_manual_instead_of_raising():
    out = push(ROW, webhook=None, token=None)
    assert out["ok"] is False
    assert out["mode"] == "manual"
    assert "2026-08-21" in out["manual"]

def test_manual_line_is_tab_separated_for_pasting():
    line = format_manual(ROW)
    assert line.count("\t") == 8      # 9 cột -> 8 dấu tab
    assert line.startswith("2026-08-21")
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m pytest tests/test_sheet_row.py tests/test_degradation.py -v`
Expected: FAIL — `No module named 'push_to_sheet'`

- [ ] **Step 3: Write minimal implementation**

```python
#!/usr/bin/env python3
"""push_to_sheet.py — đẩy một dòng nhật ký lên Google Sheet qua Apps Script.

Module này không biết gì về chứng khoán. Nó chỉ chuyển một dòng đi.

Không có webhook thì KHÔNG crash: in ra dòng đã format sẵn để dán tay.
Secret không nằm trong repo — truyền qua tham số hoặc biến môi trường.
"""
import argparse
import json
import os
import ssl
import sys
import urllib.request

_CTX = ssl.create_default_context()

COLUMNS = ["date", "close", "volume", "signal", "confidence",
           "reason", "levels", "next_step", "review"]


def build_row(date, close=None, volume=None, signal=None, confidence=None,
              reason=None, levels=None, next_step=None, review=None):
    """Dựng đúng 9 trường ghi được. Ngày nghỉ: close='—', còn lại rỗng."""
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
        print(f"⚠️  Chưa ghi được ({result['reason']}). Dán tay dòng sau:\n",
              file=sys.stderr)
        print(result["manual"])
    sys.exit(0)          # luôn thoát 0 — thiếu sheet không phải lỗi phân tích


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python3 -m pytest tests/ -v`
Expected: all passed

- [ ] **Step 5: Verify graceful degradation for real**

```bash
python3 push_to_sheet.py --date 2026-08-21 --close 14500 --signal "GIỮ"; echo "exit=$?"
```
Expected: prints the warning plus a tab-separated line, and `exit=0` — never a traceback.

- [ ] **Step 6: Commit**

```bash
git add .claude/skills/tpb-analysis/scripts/push_to_sheet.py .claude/skills/tpb-analysis/scripts/tests/test_sheet_row.py .claude/skills/tpb-analysis/scripts/tests/test_degradation.py
git commit -m "feat: cầu ghi Google Sheet, suy giảm nhẹ nhàng khi thiếu webhook"
```

---

## Task 11: Apps Script write bridge

**Files:**
- Create: `apps-script/Code.gs`
- Create: `apps-script/README.md`

**Interfaces:**
- Consumes: the JSON body `push_to_sheet.py` sends — `{token, date, close, volume, signal, confidence, reason, levels, next_step, review}`
- Produces: `{ok, row, written}` JSON response

- [ ] **Step 1: Write Code.gs**

```javascript
/**
 * Cầu ghi cho skill tpb-analysis.
 *
 * Chỉ ghi cột B–I của dòng khớp ngày. Không bao giờ đụng vào:
 *   - cột L, M : vị thế do người dùng nhập
 *   - cột J    : công thức lãi/lỗ
 */
const SHEET_NAME = 'TPB Stock Monitor';
const DATE_COL = 1;   // A
const FIRST_WRITE_COL = 2;   // B
const FIELDS = ['close', 'volume', 'signal', 'confidence',
                'reason', 'levels', 'next_step', 'review'];  // B..I

function json_(obj) {
  return ContentService.createTextOutput(JSON.stringify(obj))
      .setMimeType(ContentService.MimeType.JSON);
}

function sameDay_(cell, wanted) {
  if (!cell) return false;
  const d = (cell instanceof Date)
      ? Utilities.formatDate(cell, 'GMT+7', 'yyyy-MM-dd')
      : String(cell).trim();
  return d === wanted || d === wanted.replace(/-/g, '/');
}

function doPost(e) {
  try {
    const body = JSON.parse(e.postData.contents);
    const want = PropertiesService.getScriptProperties().getProperty('TOKEN');
    if (!want || body.token !== want) {
      return json_({ ok: false, error: 'unauthorized' });
    }
    if (!body.date) return json_({ ok: false, error: 'missing date' });

    const sheet = SpreadsheetApp.getActive().getSheetByName(SHEET_NAME);
    if (!sheet) return json_({ ok: false, error: 'sheet not found: ' + SHEET_NAME });

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

    // ghi đè đúng dòng đó -> chạy hai lần cùng ngày không đẻ dòng trùng
    const values = FIELDS.map(function (f) {
      return body[f] === undefined || body[f] === null ? '' : body[f];
    });
    sheet.getRange(target, FIRST_WRITE_COL, 1, FIELDS.length)
         .setValues([values]);

    return json_({ ok: true, row: target, written: FIELDS });
  } catch (err) {
    return json_({ ok: false, error: String(err) });
  }
}
```

- [ ] **Step 2: Write apps-script/README.md**

```markdown
# Cầu ghi Google Sheet

Sheet: `1z4DhdV41EQa9eAi3-L6Hg4oRl4igtuc5Iz5wIMXAvJA` — tab `TPB Stock Monitor`

## Cài một lần

1. Mở sheet → **Extensions → Apps Script** → dán toàn bộ `Code.gs`
2. **Project Settings → Script Properties** → thêm `TOKEN` = một chuỗi ngẫu nhiên
3. **Deploy → New deployment → Web app**
   - Execute as: **Me**
   - Who has access: **Anyone**
4. Copy URL dạng `https://script.google.com/macros/s/AKfy.../exec`

## Bố cục sheet

| Vùng | Ai ghi |
|---|---|
| A | ngày, kẻ sẵn |
| B–I | **skill ghi** |
| J | công thức `=(B{row}-$M$1)*$M$2` |
| L1/M1, L2/M2 | **người dùng nhập** giá vốn và khối lượng |

## Kiểm tra

```bash
curl -sS -X POST "$SHEET_WEBHOOK" -H 'Content-Type: application/json' \
  -d '{"token":"'"$SHEET_TOKEN"'","date":"2026-08-21","close":14500,"signal":"GIỮ"}'
```
Kỳ vọng: `{"ok":true,"row":<số dòng>,"written":[...]}`

Bảo mật: URL và token **không nằm trong repo**. Chúng ở trong prompt chạy trên Claude Cloud.
```

- [ ] **Step 3: Sheet preparation (manual, by Ray)**

In the sheet: move the position block to `L1`/`M1` (label + value, giá vốn) and `L2`/`M2` (label + value, khối lượng); put headers in row 3 as `Date | Close | Volume | Signal | Độ tin | Lý do | Mức giá canh | Next Step plan | Kiểm chứng | P/L`; set `J4` to `=(B4-$M$1)*$M$2` and fill down.

- [ ] **Step 4: Deploy and verify end-to-end**

Run the `curl` from the README with real values. Expected `{"ok":true,...}` and the row visibly filled in the sheet, with L/M untouched.

- [ ] **Step 5: Commit**

```bash
git add apps-script/
git commit -m "feat: Apps Script ghi cột B-I, idempotent theo ngày"
```

---

## Task 12: SKILL.md and references

**Files:**
- Create: `.claude/skills/tpb-analysis/SKILL.md`
- Create: `references/banking-metrics.md`, `references/sheet-contract.md`, `references/data-sources.md`

**Interfaces:** Consumes every script from Tasks 9–11. This is what Claude actually reads at run time.

- [ ] **Step 1: Write SKILL.md**

````markdown
---
name: tpb-analysis
description: Phân tích cổ phiếu TPB (Ngân hàng TMCP Tiên Phong, HOSE) — biểu đồ kỹ thuật, tin tức mới nhất, báo cáo tài chính — rồi đưa ra khuyến nghị hành động kèm độ tin cậy, và ghi vào Google Sheet để theo dõi. Dùng nguồn dữ liệu Việt Nam (Entrade, CafeF).
version: 1.0.0
---

# Phân tích TPB

Chỉ phân tích **một mã: TPB**. Không mở rộng sang mã khác, không sang thị trường khác.

## Bốn quy tắc bắt buộc

1. **Bắt buộc phản biện.** Nghiêng về mua thì phải viết bear case; nghiêng về bán thì
   phải viết bull case. Thiếu đoạn này thì báo cáo không hợp lệ.
2. **Thiếu dữ liệu thì nói thiếu.** Không lấp chỗ trống bằng phỏng đoán. Hạ độ tin xuống `Thấp`.
3. **Mọi lý do phải kèm số**, và số đó phải đến từ JSON của `fetch_tpb.py` hoặc từ nguồn
   trích dẫn được. **Không tự tính số mới.**
4. **Chấm lại trước, phán đoán sau.** Điền cột `Kiểm chứng` cho nhận định 5 phiên trước
   TRƯỚC KHI nhìn số liệu hôm nay — tránh chấm điểm theo hướng có lợi cho mình.

## Quy trình

### Bước 1 — Đọc vị thế từ sheet
Đọc sheet `1z4DhdV41EQa9eAi3-L6Hg4oRl4igtuc5Iz5wIMXAvJA`, lấy ô `M1` (giá vốn) và `M2`
(khối lượng). Đồng thời đọc dòng nhật ký của **5 phiên trước** để chuẩn bị cho bước 2.

### Bước 2 — Chấm lại nhận định cũ
Đối chiếu `Signal`, `Mức giá canh`, `Next Step plan` của 5 phiên trước với giá thực tế hôm
nay. Kết luận `Đúng` / `Sai` / `Chưa rõ` kèm một câu giải thích. **Làm bước này trước bước 3.**

### Bước 3 — Lấy số liệu
```bash
cd .claude/skills/tpb-analysis/scripts
pip install -r requirements.txt      # lần đầu
python3 fetch_tpb.py --holding-avg <M1> --holding-volume <M2>
```
Không có vị thế thì bỏ hai tham số.

### Bước 4 — Đọc tin tức và BCTC
WebSearch/WebFetch: tin TPB mới nhất, BCTC quý gần nhất. Tìm **NIM, CASA, NPL, tỷ lệ bao
phủ nợ xấu, nợ nhóm 2, CIR, CAR, tăng trưởng tín dụng**. Trích dẫn nguồn. Không tìm được
thì ghi rõ là không có, hạ độ tin.

### Bước 5 — Tổng hợp
Đọc `references/banking-metrics.md`. Viết ra: định giá nói gì, chất lượng tài sản nói gì,
kỹ thuật nói gì, bối cảnh thị trường nói gì — và bốn cái đó đồng thuận hay mâu thuẫn ở đâu.
Tín hiệu sinh ra từ đoạn đó, **không từ phép cộng điểm**.

`Signal` chọn một trong: `MUA THÊM` / `GIỮ` / `GIẢM TỶ TRỌNG` / `THOÁT` / `ĐỨNG NGOÀI`.

### Bước 6 — Ghi lại
```bash
python3 push_to_sheet.py --date <YYYY-MM-DD> --close <giá> --volume "<KL (x% TB20)>" \
  --signal "<tín hiệu>" --confidence "<Cao|TB|Thấp>" --reason "<một câu có số>" \
  --levels "<HT / KC / CL>" --next-step "<nếu ... thì ...>" --review "<kết quả bước 2>" \
  --webhook "$SHEET_WEBHOOK" --token "$SHEET_TOKEN"
```
Chỉ được nói "đã ghi xong" khi thấy `{"ok":true}`. Nếu ra chế độ dán tay thì đưa dòng đó
cho người dùng và nói rõ là **chưa** ghi được.

Cuối cùng: ghi báo cáo đầy đủ vào `reports/YYYY-MM-DD.md`, thêm một dòng vào
`data/journal/TPB.jsonl`, rồi commit.

## Không làm

Không tư vấn margin/đòn bẩy. Không phân tích phái sinh VN30F hay chứng quyền. Không tự đặt
giá mục tiêu bằng con số của riêng mình — chỉ trích dẫn target của CTCK kèm nguồn.

Kết thúc mọi báo cáo bằng: *"Đây là phân tích định lượng dựa trên dữ liệu hiện có, không
phải lời khuyên đầu tư."*
````

- [ ] **Step 2: Write references/banking-metrics.md**

Content: the four axes (định giá / chất lượng tài sản / sinh lời / tăng trưởng & an toàn vốn) and the three comparisons from spec §9, verbatim, including the worked example — TPB P/B 0.88 & ROE 17.4% ⇒ 0.051 per ROE point vs sector median 0.062, while SHB sits at 0.045; the frame must surface that SHB is cheaper rather than hide it. Plus §9.2 market mechanics: ±7% band, T+2, thin-liquidity confidence penalty.

- [ ] **Step 3: Write references/sheet-contract.md**

Content: the column table from spec §7 (A–J writable map, L/M owned by Ray, J a formula), and the rule that non-trading days get `—` in column B.

- [ ] **Step 4: Write references/data-sources.md**

Content: the source matrix from spec §5 with verification status, the rejected sources and why (TCBS Cloudflare, VNDirect 406, Simplize 404, Fireant 401, VN-Index absent from Yahoo), and the failure-handling table from spec §11.

- [ ] **Step 5: Commit**

```bash
git add .claude/skills/tpb-analysis/SKILL.md .claude/skills/tpb-analysis/references/
git commit -m "feat: SKILL.md và tài liệu tham chiếu"
```

---

## Task 13: End-to-end run

**Files:** Create `reports/<today>.md`, append `data/journal/TPB.jsonl`

- [ ] **Step 1: Full test suite green**

Run: `cd .claude/skills/tpb-analysis/scripts && python3 -m pytest tests/ -v`
Expected: all passed across all 7 test files.

- [ ] **Step 2: Run the skill for real**

Invoke Claude with the skill, supplying `SHEET_WEBHOOK` and `SHEET_TOKEN`. Confirm the six steps run in order — in particular that step 2 (scoring the old call) happens **before** step 3.

- [ ] **Step 3: Check the report against the hard rules**

- [ ] contains a counter-argument section
- [ ] every stated reason carries a number
- [ ] confidence is stated and justified
- [ ] `Kiểm chứng` refers to an actual earlier row (or says "chưa có lịch sử" on first run)
- [ ] closes with the not-investment-advice line
- [ ] no target price invented by Claude
- [ ] any ±7% break is described as a corporate action, never as selling pressure

- [ ] **Step 4: Confirm the sheet row landed**

Open the sheet. Columns B–I filled for today; **L and M unchanged**; J recalculated by formula.

- [ ] **Step 5: Confirm memory persists**

`data/journal/TPB.jsonl` has one JSON object for today. Re-run and confirm the sheet row is **overwritten, not duplicated** (idempotency).

- [ ] **Step 6: Commit**

```bash
git add data/journal/ reports/
git commit -m "chore: lần chạy đầu tiên — báo cáo và journal TPB"
```

---

## Verification

```bash
# 1. tất cả test xanh
cd .claude/skills/tpb-analysis/scripts && python3 -m pytest tests/ -v

# 2. hợp đồng JSON đúng, đơn vị đúng
python3 fetch_tpb.py | python3 -c "
import json,sys; d=json.load(sys.stdin)
assert isinstance(d['price']['close'], int) and d['price']['close'] > 1000
assert d['valuation']['sector']['n'] >= 15
assert d['market']['vnindex']['value'] > 1000
print('OK', d['meta']['session_date'], d['price']['close'], 'VND')"

# 3. thiếu webhook thì không chết
python3 push_to_sheet.py --date 2026-08-21 --close 14500; echo "exit=$?"   # phải là 0

# 4. sạch dấu vết thị trường Mỹ
grep -ri "alpha.vantage\|AAPL\|analyze_stock" --include="*.py" --include="*.md" . || echo "sạch"
```

## Self-Review Notes

**Spec coverage:** §3 lessons → Tasks 1–4; §5 sources → Tasks 5–7; §5.1 units → Task 2; §5.2 cross-check → Task 8; §5.3 corporate actions → Task 4; §6 contract → Tasks 8–9; §6.1 position provenance → Task 9 (CLI args, no Google access in Python); §7 sheet schema → Tasks 10–11; §8 bridge + secrets → Tasks 10–11; §9 banking frame → Task 12; §10 four rules → Task 12 SKILL.md; §11 error handling → Tasks 5, 6, 9, 10; §12 tests → Tasks 2–10; §14 completion criteria → Task 13.

**One spec item degrades:** foreign flow (§9) has no verified endpoint. Task 6 ships `foreign: null` plus an explicit warning rather than inventing field names — consistent with the no-fabrication rule.

**Type consistency checked:** `entrade_to_vnd`/`yahoo_to_vnd` (Task 2) used identically in Tasks 5 and 7. `flag_limit_breaks` signature matches between Tasks 4 and 8. `build_row` keys (Task 10) match `FIELDS` in `Code.gs` (Task 11) exactly, in the same order. `sector_stats` returns `rank_pb_per_roe` as a dict in both Task 7 and Task 8.

**Note for the executor:** this plan lives at the plan-mode path. Copy it to `docs/superpowers/plans/2026-08-21-tpb-analysis-skill.md` and commit it alongside Task 1 so it travels with the repo.
