#!/usr/bin/env python3
"""Backtest dividend yield and dividend growth for DGRO+DIVO vs SCHD.

Uses Yahoo Finance chart API directly (no third-party Python packages).
Outputs a JSON file that the HTML dashboard can load.
"""

from __future__ import annotations

import json
import time
import urllib.parse
import urllib.request
from collections import defaultdict
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from statistics import mean, median
from typing import Dict, List, Tuple

TICKERS = ["DGRO", "DIVO", "SCHD"]
BLEND_DEFAULT_DGRO_WEIGHT = 0.5
WEIGHT_GRID = [i / 100 for i in range(0, 101, 5)]

# DIVO inception is late 2016. Start from 2017-01 to keep data stable.
START_DATE = datetime(2017, 1, 1, tzinfo=UTC)

OUT_PATH = Path(__file__).with_name("dividend_backtest_results.json")


@dataclass
class Point:
    month: str
    close: float
    ttm_div: float
    ttm_yield: float
    norm_div: float


def to_epoch(dt: datetime) -> int:
    return int(dt.timestamp())


def fetch_yahoo_monthly(ticker: str, period1: int, period2: int) -> Dict:
    params = {
        "period1": str(period1),
        "period2": str(period2),
        "interval": "1mo",
        "events": "div|split",
        "includePrePost": "false",
    }
    url = (
        f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?"
        + urllib.parse.urlencode(params)
    )
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        raw = resp.read().decode("utf-8")
    return json.loads(raw)


def month_key_from_epoch(ts: int) -> str:
    return datetime.fromtimestamp(ts, tz=UTC).strftime("%Y-%m")


def parse_series(payload: Dict) -> Dict[str, Dict[str, float]]:
    result = payload.get("chart", {}).get("result", [])
    if not result:
        raise ValueError("Yahoo payload has no result")

    node = result[0]
    timestamps = node.get("timestamp", [])
    closes = node.get("indicators", {}).get("quote", [{}])[0].get("close", [])

    rows: Dict[str, Dict[str, float]] = {}
    for ts, close in zip(timestamps, closes):
        if close is None:
            continue
        mk = month_key_from_epoch(ts)
        rows.setdefault(mk, {})["close"] = float(close)

    dividends = (
        node.get("events", {}).get("dividends", {})
        if node.get("events")
        else {}
    )
    div_map = defaultdict(float)
    for item in dividends.values():
        ts = item.get("date")
        amount = item.get("amount")
        if ts is None or amount is None:
            continue
        mk = month_key_from_epoch(int(ts))
        div_map[mk] += float(amount)

    for mk, amount in div_map.items():
        rows.setdefault(mk, {})["div"] = amount

    for mk in list(rows.keys()):
        rows[mk].setdefault("div", 0.0)

    return rows


def sorted_months(rows: Dict[str, Dict[str, float]]) -> List[str]:
    return sorted(rows.keys())


def build_points(rows: Dict[str, Dict[str, float]], months: List[str]) -> List[Point]:
    points: List[Point] = []
    for i, m in enumerate(months):
        if "close" not in rows[m]:
            continue
        ttm_div = 0.0
        for j in range(max(0, i - 11), i + 1):
            mj = months[j]
            ttm_div += rows[mj].get("div", 0.0)
        close = rows[m]["close"]
        ttm_yield = (ttm_div / close) if close > 0 else 0.0
        points.append(
            Point(month=m, close=close, ttm_div=ttm_div, ttm_yield=ttm_yield, norm_div=0.0)
        )

    if points and points[0].close > 0:
        base_close = points[0].close
        for p in points:
            p.norm_div = p.ttm_div / base_close
    return points


def aligned_points(points_by_ticker: Dict[str, List[Point]]) -> Tuple[List[str], Dict[str, List[Point]]]:
    month_sets = []
    for ticker in TICKERS:
        month_sets.append({p.month for p in points_by_ticker[ticker]})
    common_months = sorted(set.intersection(*month_sets))

    aligned: Dict[str, List[Point]] = {}
    for ticker in TICKERS:
        mp = {p.month: p for p in points_by_ticker[ticker]}
        aligned[ticker] = [mp[m] for m in common_months]

    # Keep months where every ticker has a full 12m TTM window from this common range.
    # This effectively drops warm-up early months where TTM is still ramping.
    if len(common_months) > 12:
        common_months = common_months[12:]
        for ticker in TICKERS:
            aligned[ticker] = aligned[ticker][12:]

    return common_months, aligned


def annualized_growth(start_val: float, end_val: float, years: float) -> float:
    if start_val <= 0 or end_val <= 0 or years <= 0:
        return 0.0
    return (end_val / start_val) ** (1 / years) - 1


def rolling_growth_from_values(values: List[float], months_back: int = 12) -> List[float]:
    out = []
    for i in range(months_back, len(values)):
        prev = values[i - months_back]
        cur = values[i]
        if prev <= 0 or cur <= 0:
            continue
        g = annualized_growth(prev, cur, months_back / 12)
        out.append(g)
    return out


def blend_points(months: List[str], aligned: Dict[str, List[Point]], dgro_w: float) -> List[Point]:
    divo_w = 1 - dgro_w
    out: List[Point] = []
    for i, m in enumerate(months):
        dgro = aligned["DGRO"][i]
        divo = aligned["DIVO"][i]

        # Monthly rebalanced basket yield approximation.
        ttm_yield = dgro_w * dgro.ttm_yield + divo_w * divo.ttm_yield
        # Dividend growth uses on-cost normalized dividend cashflow.
        norm_div = dgro_w * dgro.norm_div + divo_w * divo.norm_div

        out.append(
            Point(
                month=m,
                close=1.0,
                ttm_div=norm_div,
                ttm_yield=ttm_yield,
                norm_div=norm_div,
            )
        )
    return out


def summarize_points(points: List[Point]) -> Dict:
    if not points:
        return {}
    yields = [p.ttm_yield for p in points]
    norm_divs = [p.norm_div for p in points]

    growth_1y = rolling_growth_from_values(norm_divs, 12)
    growth_3y = rolling_growth_from_values(norm_divs, 36) if len(points) >= 37 else []

    months_span = len(points) - 1
    years_span = months_span / 12 if months_span > 0 else 0
    cagr_full = annualized_growth(norm_divs[0], norm_divs[-1], years_span)

    return {
        "latest_yield": points[-1].ttm_yield,
        "avg_yield": mean(yields),
        "median_yield": median(yields),
        "min_yield": min(yields),
        "max_yield": max(yields),
        "latest_ttm_div": points[-1].ttm_div,
        "latest_norm_div": points[-1].norm_div,
        "div_growth_cagr_full": cagr_full,
        "avg_growth_1y": mean(growth_1y) if growth_1y else 0.0,
        "median_growth_1y": median(growth_1y) if growth_1y else 0.0,
        "avg_growth_3y": mean(growth_3y) if growth_3y else 0.0,
        "median_growth_3y": median(growth_3y) if growth_3y else 0.0,
    }


def main() -> None:
    now = datetime.now(tz=UTC)
    p1 = to_epoch(START_DATE)
    p2 = to_epoch(now)

    raw_rows = {}
    for ticker in TICKERS:
        payload = fetch_yahoo_monthly(ticker, p1, p2)
        rows = parse_series(payload)
        raw_rows[ticker] = rows
        time.sleep(0.3)

    points_by_ticker = {}
    for ticker in TICKERS:
        months = sorted_months(raw_rows[ticker])
        points_by_ticker[ticker] = build_points(raw_rows[ticker], months)

    months, aligned = aligned_points(points_by_ticker)

    summaries = {ticker: summarize_points(aligned[ticker]) for ticker in TICKERS}

    default_blend = blend_points(months, aligned, BLEND_DEFAULT_DGRO_WEIGHT)
    default_summary = summarize_points(default_blend)

    weight_scenarios = []
    for w in WEIGHT_GRID:
        bp = blend_points(months, aligned, w)
        sm = summarize_points(bp)
        weight_scenarios.append(
            {
                "dgro_weight": w,
                "divo_weight": 1 - w,
                "latest_yield": sm.get("latest_yield", 0.0),
                "div_growth_cagr_full": sm.get("div_growth_cagr_full", 0.0),
                "avg_yield": sm.get("avg_yield", 0.0),
                "avg_growth_1y": sm.get("avg_growth_1y", 0.0),
            }
        )

    # Monthly series for the default blend vs SCHD.
    series = []
    for i, m in enumerate(months):
        series.append(
            {
                "month": m,
                "blend_yield": default_blend[i].ttm_yield,
                "schd_yield": aligned["SCHD"][i].ttm_yield,
                "blend_ttm_div": default_blend[i].norm_div,
                "schd_ttm_div": aligned["SCHD"][i].norm_div,
            }
        )

    result = {
        "generated_at": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source": "Yahoo Finance chart API",
        "period": {
            "start": months[0] if months else None,
            "end": months[-1] if months else None,
            "months": len(months),
        },
        "tickers": TICKERS,
        "individual": summaries,
        "blend_default": {
            "dgro_weight": BLEND_DEFAULT_DGRO_WEIGHT,
            "divo_weight": 1 - BLEND_DEFAULT_DGRO_WEIGHT,
            **default_summary,
        },
        "weight_scenarios": weight_scenarios,
        "series": series,
        "notes": {
            "yield_definition": "TTM dividends / month-end close",
            "growth_definition": "Annualized growth of TTM dividend cashflow per initial $1 invested",
            "limitations": [
                "ETF distribution policy changes can distort short windows",
                "Data vendor adjustments may revise historical dividends",
                "Tax and FX effects are not included",
            ],
        },
    }

    OUT_PATH.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {OUT_PATH}")
    print(f"Period: {result['period']['start']} -> {result['period']['end']} ({result['period']['months']} months)")


if __name__ == "__main__":
    main()
