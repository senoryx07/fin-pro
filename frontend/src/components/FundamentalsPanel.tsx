import type {
  AnnualResult,
  Fundamentals,
  QuarterlyResult,
} from "../types/data";
import {
  formatCrore,
  formatDate,
  formatPercent,
  formatPrice,
  trendClass,
} from "../utils/format";


interface FundamentalsPanelProps {
  fundamentals: Fundamentals;
}

type Row<T> = {
  label: string;
  value: (item: T) => number | null;
  format: (value: number | null) => string;
  tone?: boolean;
  strong?: boolean;
};


const quarterLabel = (periodEnd: string) =>
  new Date(`${periodEnd}T00:00:00`).toLocaleDateString(
    "en-IN",
    { month: "short", year: "2-digit" }
  );


function ResultsTable<T>({
  columns,
  header,
  rows,
}: {
  columns: T[];
  header: (item: T) => string;
  rows: Row<T>[];
}) {
  return (
    <div className="tech-table-wrap">
      <table className="tech-table results-table">
        <thead>
          <tr>
            <th />
            {columns.map((item, i) => (
              <th key={i}>{header(item)}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr
              key={row.label}
              className={row.strong ? "strong-row" : ""}
            >
              <td>{row.label}</td>
              {columns.map((item, i) => {
                const value = row.value(item);

                return (
                  <td
                    key={i}
                    className={
                      row.tone ? trendClass(value) : ""
                    }
                  >
                    {row.format(value)}
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}


function TrendBars({
  quarters,
}: {
  quarters: QuarterlyResult[];
}) {
  const max = Math.max(
    1,
    ...quarters.map((q) => q.revenue ?? 0)
  );

  return (
    <div className="trend-bars">
      {quarters.map((q) => {
        const revenue = q.revenue ?? 0;
        const profit = q.net_profit_owners ?? 0;

        return (
          <div
            className="trend-bar"
            key={q.period_end}
            title={`${quarterLabel(q.period_end)}: revenue ${formatCrore(
              q.revenue
            )}, profit ${formatCrore(q.net_profit_owners)}`}
          >
            <div className="trend-bar-stack">
              <span
                className="bar-revenue"
                style={{ height: `${(revenue / max) * 100}%` }}
              />
              <span
                className={
                  profit >= 0 ? "bar-profit" : "bar-loss"
                }
                style={{
                  height: `${(Math.abs(profit) / max) * 100}%`,
                }}
              />
            </div>
            <span className="trend-bar-label">
              {quarterLabel(q.period_end)}
            </span>
          </div>
        );
      })}
    </div>
  );
}


function FundamentalsPanel({
  fundamentals,
}: FundamentalsPanelProps) {
  const recent = fundamentals.quarters.slice(-12);
  const latest = recent[recent.length - 1];
  const annual = fundamentals.annual.slice(-8);
  const bank = fundamentals.is_bank;

  const quarterRows: Row<QuarterlyResult>[] = [
    {
      label: bank ? "Interest earned" : "Revenue",
      value: (q) => q.revenue,
      format: formatCrore,
      strong: true,
    },
    {
      label: "YoY growth",
      value: (q) => q.revenue_growth_yoy,
      format: (v) => formatPercent(v),
      tone: true,
    },
    {
      label: "Other income",
      value: (q) => q.other_income,
      format: formatCrore,
    },
    {
      label: "Expenses",
      value: (q) => q.expenses,
      format: formatCrore,
    },
    ...(bank
      ? []
      : [
          {
            label: "Operating profit",
            value: (q: QuarterlyResult) => q.operating_profit,
            format: formatCrore,
          },
          {
            label: "OPM",
            value: (q: QuarterlyResult) => q.operating_margin,
            format: (v: number | null) => formatPercent(v, false),
          },
        ]),
    {
      label: bank ? "Interest expended" : "Finance costs",
      value: (q) => q.finance_costs,
      format: formatCrore,
    },
    {
      label: "Profit before tax",
      value: (q) => q.profit_before_tax,
      format: formatCrore,
    },
    {
      label: "Tax",
      value: (q) => q.tax,
      format: formatCrore,
    },
    {
      label: "Net profit",
      value: (q) => q.net_profit_owners,
      format: formatCrore,
      strong: true,
    },
    {
      label: "YoY growth",
      value: (q) => q.profit_growth_yoy,
      format: (v) => formatPercent(v),
      tone: true,
    },
    {
      label: "Net margin",
      value: (q) => q.net_margin,
      format: (v) => formatPercent(v, false),
    },
    {
      label: "EPS (adjusted, ₹)",
      value: (q) => q.adjusted_eps,
      format: formatPrice,
    },
  ];

  const annualRows: Row<AnnualResult>[] = [
    {
      label: bank ? "Interest earned" : "Revenue",
      value: (a) => a.revenue,
      format: formatCrore,
      strong: true,
    },
    {
      label: "Growth",
      value: (a) => a.revenue_growth,
      format: (v) => formatPercent(v),
      tone: true,
    },
    {
      label: "Net profit",
      value: (a) => a.net_profit_owners,
      format: formatCrore,
      strong: true,
    },
    {
      label: "Growth",
      value: (a) => a.profit_growth,
      format: (v) => formatPercent(v),
      tone: true,
    },
    {
      label: "Net margin",
      value: (a) => a.net_margin,
      format: (v) => formatPercent(v, false),
    },
    {
      label: "EPS (adjusted, ₹)",
      value: (a) => a.adjusted_eps,
      format: formatPrice,
    },
  ];

  const stats = [
    ["TTM REVENUE", formatCrore(fundamentals.ttm_revenue)],
    ["TTM NET PROFIT", formatCrore(fundamentals.ttm_net_profit)],
    ["TTM EPS", `₹${formatPrice(fundamentals.ttm_eps)}`],
    ["TTM NET MARGIN", formatPercent(fundamentals.ttm_net_margin, false)],
    [
      "LATEST REVENUE GROWTH",
      formatPercent(latest?.revenue_growth_yoy),
    ],
    [
      "LATEST PROFIT GROWTH",
      formatPercent(latest?.profit_growth_yoy),
    ],
  ];


  return (
    <div className="fundamentals">

      <div className="quote-strip">
        <div className="quote-stats">
          {stats.map(([label, value]) => (
            <div key={label}>
              <span>{label}</span>
              <strong>{value}</strong>
            </div>
          ))}
        </div>
      </div>


      <div className="chart-card">
        <div className="section-label">
          QUARTERLY REVENUE &amp; NET PROFIT
        </div>
        <div className="chart-legend trend-legend">
          <span><i className="legend-revenue" />Revenue</span>
          <span><i className="legend-profit" />Net profit</span>
        </div>
        <TrendBars quarters={recent} />
      </div>


      <div className="chart-card">
        <div className="section-label">
          QUARTERLY RESULTS · {fundamentals.basis?.toUpperCase()}
        </div>
        <ResultsTable
          columns={recent}
          header={(q) => quarterLabel(q.period_end)}
          rows={quarterRows}
        />
      </div>


      {annual.length > 0 && (
        <div className="chart-card">
          <div className="section-label">
            ANNUAL RESULTS (SUM OF QUARTERS)
          </div>
          <ResultsTable
            columns={annual}
            header={(a) => a.fiscal_year}
            rows={annualRows}
          />
        </div>
      )}


      <p className="coverage-text source-note">
        Source: NSE quarterly results filings (XBRL),{" "}
        {fundamentals.basis} figures. Latest quarter{" "}
        {formatDate(fundamentals.latest_period)}. EPS is
        restated on today's share count so it stays
        comparable across bonuses and splits.
      </p>

    </div>
  );
}


export default FundamentalsPanel;
