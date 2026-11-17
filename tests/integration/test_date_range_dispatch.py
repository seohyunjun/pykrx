from datetime import date, datetime
from unittest.mock import patch

import pytest

from pykrx import stock

DISPATCHERS = [
    ("get_market_ohlcv", "get_market_ohlcv_by_date", "get_market_ohlcv_by_ticker"),
    ("get_market_cap", "get_market_cap_by_date", "get_market_cap_by_ticker"),
    (
        "get_exhaustion_rates_of_foreign_investment",
        "get_exhaustion_rates_of_foreign_investment_by_date",
        "get_exhaustion_rates_of_foreign_investment_by_ticker",
    ),
    (
        "get_market_fundamental",
        "get_market_fundamental_by_date",
        "get_market_fundamental_by_ticker",
    ),
    ("get_index_ohlcv", "get_index_ohlcv_by_date", "get_index_ohlcv_by_ticker"),
    (
        "get_index_fundamental",
        "get_index_fundamental_by_date",
        "get_index_fundamental_by_ticker",
    ),
    (
        "get_shorting_balance",
        "get_shorting_balance_by_date",
        "get_shorting_balance_by_ticker",
    ),
]


@pytest.mark.parametrize("name, by_date, by_ticker", DISPATCHERS)
def test_date_range_dispatch(name, by_date, by_ticker):
    func = getattr(stock, name)
    with (
        patch.object(stock.stock_api, by_date) as date_mock,
        patch.object(stock.stock_api, by_ticker) as ticker_mock,
    ):
        func("20210118", "20210126", "005930")
        func("20210118", todate="20210126", ticker="005930")
        func(fromdate="20210118", todate="20210126", ticker="005930")
        assert date_mock.call_count == 3
        ticker_mock.assert_not_called()

        func("20210118")
        func(date="20210118")
        assert ticker_mock.call_count == 2
        assert date_mock.call_count == 3


def test_market_price_change_accepts_mixed_date_args():
    with patch.object(stock.stock_api, "get_market_price_change_by_ticker") as mock:
        stock.get_market_price_change("20210118", todate="20210126")
        mock.assert_called_once_with("20210118", todate="20210126")


DATE_RANGES = [
    ("20210118", "20210126"),
    (date(2021, 1, 18), date(2021, 1, 26)),
    ("20210118", date(2021, 1, 26)),
    (date(2021, 1, 18), "20210126"),
    (datetime(2021, 1, 18, 15, 30), datetime(2021, 1, 26, 9)),
]
CALL_STYLES = ["positional", "mixed", "keywords"]


def call_with_style(func, names, values, style):
    if style == "positional":
        return func(*values)
    if style == "mixed":
        return func(values[0], **dict(zip(names[1:], values[1:], strict=True)))
    return func(**dict(zip(names, values, strict=True)))


@pytest.mark.parametrize(
    "value", ["20210118", "2021-01-18", date(2021, 1, 18), datetime(2021, 1, 18, 15)]
)
@pytest.mark.parametrize("style", CALL_STYLES)
def test_index_portfolio_normalizes_date(value, style):
    with patch.object(
        stock.stock_api.krx, "get_index_portfolio_deposit_file", return_value=["005930"]
    ) as backend:
        result = call_with_style(
            stock.get_index_portfolio_deposit_file,
            ["ticker", "date"],
            ["1001", value],
            style,
        )
    assert result == ["005930"]
    backend.assert_called_once_with("20210118", "1001")


@pytest.mark.parametrize(
    "value", ["20140501", "2014-05-01", date(2014, 5, 1), datetime(2014, 5, 1)]
)
def test_index_portfolio_rejects_dates_before_cutoff(value):
    with patch.object(
        stock.stock_api.krx, "get_index_portfolio_deposit_file"
    ) as backend:
        assert stock.get_index_portfolio_deposit_file("1001", value) == []
    backend.assert_not_called()


@pytest.mark.parametrize(
    "value", ["20140502", "2014-05-02", date(2014, 5, 2), datetime(2014, 5, 2)]
)
def test_index_portfolio_cutoff_and_alternative(value):
    with (
        patch.object(
            stock.stock_api.krx,
            "get_index_portfolio_deposit_file",
            side_effect=[[], ["005930"]],
        ) as backend,
        patch.object(
            stock.stock_api,
            "get_nearest_business_day_in_a_week",
            return_value="20140430",
        ) as nearest,
    ):
        assert stock.get_index_portfolio_deposit_file(
            "1001", value, alternative=True
        ) == ["005930"]
    nearest.assert_called_once_with("20140502")
    assert backend.call_args_list[0].args == ("20140502", "1001")
    assert backend.call_args_list[1].args == ("20140430", "1001")


@pytest.mark.parametrize("fromdate,todate", DATE_RANGES)
@pytest.mark.parametrize("style", CALL_STYLES)
@pytest.mark.parametrize("prev", [True, False])
def test_index_fundamental_normalizes_dates(fromdate, todate, style, prev):
    with patch.object(stock.stock_api.krx, "get_index_fundamental_by_date") as backend:
        result = call_with_style(
            stock.get_index_fundamental_by_date,
            ["fromdate", "todate", "ticker", "prev"],
            [fromdate, todate, "1001", prev],
            style,
        )
    assert result is backend.return_value
    backend.assert_called_once_with("20210118", "20210126", "1001")


ETF_VARIANTS = [
    ([], [], "get_trading_volume_and_value_by_investor"),
    (["ticker"], ["069500"], "get_indivisual_trading_volume_and_value_by_investor"),
    (
        ["query_type1", "query_type2"],
        ["거래대금", "순매수"],
        "get_trading_volume_and_value_by_date",
    ),
    (
        ["ticker", "query_type1", "query_type2"],
        ["069500", "거래량", "매수"],
        "get_indivisual_trading_volume_and_value_by_date",
    ),
]


@pytest.mark.parametrize("names,values,backend_name", ETF_VARIANTS)
@pytest.mark.parametrize("fromdate,todate", DATE_RANGES)
@pytest.mark.parametrize("style", CALL_STYLES)
def test_etf_trading_normalizes_dates(
    names, values, backend_name, fromdate, todate, style
):
    with patch.object(stock.stock_api.krx, backend_name) as backend:
        result = call_with_style(
            stock.get_etf_trading_volume_and_value,
            ["fromdate", "todate", *names],
            [fromdate, todate, *values],
            style,
        )
    assert result is backend.return_value
    backend.assert_called_once_with("20210118", "20210126", *values)


@pytest.mark.parametrize(
    "args,kwargs",
    [
        (("20210118",), {}),
        (("20210118", "20210126"), {"unknown": "x"}),
        (("20210118", "20210126"), {"query_type1": "거래량"}),
        (("20210118", "20210126", "069500"), {"ticker": "069500"}),
        (("20210118", "20210126", "069500", "거래량", "매수", "extra"), {}),
    ],
)
def test_etf_trading_rejects_invalid_arguments(args, kwargs):
    with pytest.raises(TypeError):
        stock.get_etf_trading_volume_and_value(*args, **kwargs)
