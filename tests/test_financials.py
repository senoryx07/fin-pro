from datetime import date, timedelta
from pathlib import Path

import pytest

from backend.app.financials.service import (
    build_annual,
    build_quarterly,
    choose_basis,
    fiscal_year_label,
    trailing_four,
)
from backend.app.models.financials import FinancialResult
from backend.app.models.market_data import DailyPrice
from backend.app.providers.nse_financial_data import (
    _quarter_start,
    parse_results_xbrl,
)
from backend.app.technicals.service import adjust_prices


FIXTURES = Path(__file__).parent / "fixtures"


def test_parse_integrated_filing():
    result = parse_results_xbrl(
        (FIXTURES / "reliance_integrated.xml").read_bytes()
    )

    assert result["period_start"] == date(2026, 4, 1)
    assert result["period_end"] == date(2026, 6, 30)
    assert result["is_bank"] is False
    assert result["revenue"] == 3118500000000
    assert result["net_profit_owners"] == 209460000000
    assert result["eps_basic"] == 15.48
    assert result["paid_up_capital"] / result["face_value"] == pytest.approx(
        13533000000
    )


def test_parse_bank_filing_uses_bank_elements():
    result = parse_results_xbrl(
        (FIXTURES / "hdfcbank_integrated.xml").read_bytes()
    )

    assert result["is_bank"] is True
    assert result["period_end"] == date(2026, 9, 30)
    # Revenue falls back to InterestEarned, finance costs to InterestExpended.
    assert result["revenue"] > 0
    assert result["finance_costs"] > 0
    assert result["net_profit"] > 0
    assert result["expenses"] == pytest.approx(
        result["total_income"] - result["profit_before_tax"]
    )


def test_parse_filing_with_undeclared_context():
    xml = b"""<?xml version="1.0"?>
    <xbrli:xbrl xmlns:xbrli="http://www.xbrl.org/2003/instance"
                xmlns:f="http://example.com/fin">
      <f:DateOfEndOfReportingPeriod contextRef="OneD">2021-12-31</f:DateOfEndOfReportingPeriod>
      <f:RevenueFromOperations contextRef="OneD">100</f:RevenueFromOperations>
      <f:RevenueFromOperations contextRef="FourD">300</f:RevenueFromOperations>
      <f:ProfitLossForPeriod contextRef="OneD">10</f:ProfitLossForPeriod>
    </xbrli:xbrl>"""

    result = parse_results_xbrl(xml)

    assert result["period_start"] == date(2021, 10, 1)
    assert result["period_end"] == date(2021, 12, 31)
    assert result["revenue"] == 100
    assert result["net_profit_owners"] == 10


def test_quarter_start_crosses_year():
    assert _quarter_start(date(2026, 3, 31)) == date(2026, 1, 1)
    assert _quarter_start(date(2026, 1, 31)) == date(2025, 11, 1)


def make_result(period_end: date, revenue: float, profit: float, **extra):
    return FinancialResult(
        security_id=1,
        period_start=_quarter_start(period_end),
        period_end=period_end,
        consolidated=extra.pop("consolidated", True),
        revenue=revenue,
        expenses=revenue * 0.8,
        finance_costs=1.0,
        depreciation=2.0,
        net_profit_owners=profit,
        paid_up_capital=1000.0,
        face_value=10.0,
        **extra,
    )


QUARTER_ENDS = [
    date(2024, 6, 30),
    date(2024, 9, 30),
    date(2024, 12, 31),
    date(2025, 3, 31),
    date(2025, 6, 30),
    date(2025, 9, 30),
    date(2025, 12, 31),
    date(2026, 3, 31),
]


@pytest.fixture
def results():
    return [
        make_result(end, revenue=100.0 + 10 * i, profit=10.0 + i)
        for i, end in enumerate(QUARTER_ENDS)
    ]


def test_fiscal_year_label():
    assert fiscal_year_label(date(2025, 6, 30)) == "FY26"
    assert fiscal_year_label(date(2026, 3, 31)) == "FY26"


def test_quarterly_growth_and_margins(results):
    quarters = build_quarterly(results, current_shares=100.0)
    latest = quarters[-1]

    assert latest.revenue_growth_yoy == pytest.approx(170 / 130 - 1)
    assert latest.profit_growth_yoy == pytest.approx(17 / 13 - 1)
    assert latest.net_margin == pytest.approx(17 / 170)
    # EBITDA = revenue - expenses + finance costs + depreciation.
    assert latest.operating_profit == pytest.approx(170 - 136 + 3)
    assert latest.adjusted_eps == pytest.approx(0.17)
    assert quarters[0].revenue_growth_yoy is None


def test_annual_requires_four_quarters(results):
    annual = build_annual(results[1:], current_shares=100.0)

    # FY25 is missing its June quarter, so only FY26 is complete.
    assert [a.fiscal_year for a in annual] == ["FY26"]
    assert annual[0].revenue == 140 + 150 + 160 + 170
    assert annual[0].revenue_growth is None


def test_annual_growth(results):
    fy25, fy26 = build_annual(results, current_shares=100.0)

    assert fy25.revenue == 100 + 110 + 120 + 130
    assert fy26.revenue_growth == pytest.approx(620 / 460 - 1)


def test_trailing_four_rejects_gaps(results):
    gapped = results[:2] + results[3:]

    assert trailing_four(results, 3) == results[:4]
    assert trailing_four(gapped, 3) is None


def test_choose_basis_prefers_fresh_consolidated(results):
    standalone = [
        make_result(r.period_end, r.revenue, r.net_profit_owners, consolidated=False)
        for r in results
    ]

    grouped = {"consolidated": results[:-1], "standalone": standalone}

    assert choose_basis(grouped) == "standalone"
    assert choose_basis({**grouped, "consolidated": results}) == "consolidated"
    assert choose_basis(grouped, "consolidated") == "consolidated"


def test_adjust_prices_for_bonus():
    start = date(2026, 1, 1)
    closes = [2000.0, 2010.0, 1000.0, 1010.0]
    # Day 3 is a 1:1 bonus ex-date; NSE reports the adjusted previous close.
    previous = [None, 2000.0, 1005.0, 1000.0]

    prices = [
        DailyPrice(
            security_id=1,
            trade_date=start + timedelta(days=i),
            close=close,
            open=close,
            high=close,
            low=close,
            previous_close=prev,
            volume=100,
        )
        for i, (close, prev) in enumerate(zip(closes, previous))
    ]

    bars, adjustments = adjust_prices(prices)

    assert len(adjustments) == 1
    assert adjustments[0].ratio == pytest.approx(2.0)
    assert [bar.close for bar in bars] == pytest.approx(
        [1000.0, 1005.0, 1000.0, 1010.0]
    )
    assert bars[0].volume == 200
    # Source rows are not mutated.
    assert prices[0].close == 2000.0


def test_adjust_prices_ignores_ordinary_dividend():
    start = date(2026, 1, 1)

    prices = [
        DailyPrice(
            security_id=1,
            trade_date=start,
            close=100.0,
        ),
        DailyPrice(
            security_id=1,
            trade_date=start + timedelta(days=1),
            close=98.0,
            previous_close=97.0,
        ),
    ]

    bars, adjustments = adjust_prices(prices)

    assert adjustments == []
    assert bars[0].close == 100.0


def test_shares_outstanding_repairs_bad_face_value():
    from backend.app.financials.service import shares_outstanding

    good = make_result(date(2026, 6, 30), 100.0, 10.0)
    good.eps_basic = 0.1  # 10 / 100 shares

    assert shares_outstanding(good) == 100

    # Face value misreported in the filing; paid-up capital is fine.
    bad = make_result(date(2026, 6, 30), 100.0, 10.0)
    bad.face_value = 1586949.0
    bad.eps_basic = 0.1

    assert shares_outstanding(bad) == 100

    # Nothing usable from capital: fall back to profit / EPS.
    bad.paid_up_capital = None

    assert shares_outstanding(bad) == pytest.approx(100)


def test_adjust_prices_detects_split_from_gap():
    # NSE reported an unadjusted previous close on this 1:5 split ex-date.
    start = date(2026, 1, 13)
    rows = [(2132.6, 2132.6, 2133.3), (426.0, 421.0, 2132.6)]

    prices = [
        DailyPrice(
            security_id=1,
            trade_date=start + timedelta(days=i),
            open=open_,
            close=close,
            previous_close=prev,
        )
        for i, (open_, close, prev) in enumerate(rows)
    ]

    bars, adjustments = adjust_prices(prices)

    assert [a.ratio for a in adjustments] == [5.0]
    assert bars[0].close == pytest.approx(2132.6 / 5)


def test_adjust_prices_ignores_gap_with_no_standard_ratio():
    start = date(2026, 1, 13)

    prices = [
        DailyPrice(security_id=1, trade_date=start, close=100.0),
        DailyPrice(
            security_id=1,
            trade_date=start + timedelta(days=1),
            # A 1.72x gap sits between the 3:2 and 2:1 ratios.
            open=58.0,
            close=58.0,
            previous_close=100.0,
        ),
    ]

    assert adjust_prices(prices)[1] == []


def test_corporate_normalize():
    from backend.app.ingestion.corporate_loader import normalize

    summary = {
        "shareholdings_patterns": {
            "data": {
                "30-Jun-2026": [
                    {"Promoter & Promoter Group": " 50.48"},
                    {"Public": " 49.52"},
                ],
                "31-Mar-2026": [
                    {"Promoter & Promoter Group": " 50.00"},
                    {"Public": " 50.00"},
                ],
            }
        },
        "corporate_actions": {
            "data": [{"exdate": "28-Oct-2024", "purpose": "Bonus 1:1"}]
        },
        "borad_meeting": {
            "data": [
                {"meetingdate": "30-Oct-2026", "purpose": "A much longer intimation text"},
                {"meetingdate": "30-Oct-2026", "purpose": "Results"},
            ]
        },
    }
    announcements = [
        {
            "an_dt": "29-Oct-2026 08:55:40",
            "desc": "Updates",
            "attchmntText": "word " * 200,
            "attchmntFile": "-",
        }
    ]

    data = normalize(summary, announcements)

    assert [s["date"] for s in data["shareholding"]] == ["2026-03-31", "2026-06-30"]
    assert data["shareholding"][-1]["promoter"] == 50.48
    assert data["actions"] == [{"ex_date": "2024-10-28", "purpose": "Bonus 1:1"}]
    assert data["meetings"] == [{"date": "2026-10-30", "purpose": "Results"}]
    assert len(data["announcements"][0]["text"]) <= 400
    assert data["announcements"][0]["url"] is None
