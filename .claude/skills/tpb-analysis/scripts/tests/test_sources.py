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


def test_keeps_raw_closes_for_index_series():
    # chỉ số là điểm số (1734.24), không phải giá nghìn đồng
    out = parse_entrade(PAYLOAD)
    assert out["raw_closes"] == [14.35, 14.5]


def test_dates_are_iso_strings():
    out = parse_entrade(PAYLOAD)
    assert out["dates"][0] == "2025-08-17"


def test_volumes_preserved_as_int():
    assert parse_entrade(PAYLOAD)["volumes"] == [3707900, 7658000]


def test_empty_payload_returns_none():
    assert parse_entrade({"t": [], "c": []}) is None
    assert parse_entrade(None) is None


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
