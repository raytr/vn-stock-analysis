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
