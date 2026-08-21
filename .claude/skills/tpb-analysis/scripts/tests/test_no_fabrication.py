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
    assert stats["n"] == 2                       # mã thiếu dữ liệu bị loại
    assert stats["median_pb"] == 0.83
    assert stats["rank_pb_per_roe"]["TPB"] == 2  # SHB rẻ hơn -> hạng 1


def test_sector_stats_empty_is_safe():
    assert sector_stats([])["n"] == 0


def test_price_extracted_for_cross_check():
    # không có trường này thì cơ chế đối chiếu chéo thành code chết
    assert extract_fundamentals({"currentPrice": 14500.0})["price"] == 14500
    assert extract_fundamentals({"regularMarketPrice": 14500.0})["price"] == 14500
    assert extract_fundamentals({})["price"] is None
