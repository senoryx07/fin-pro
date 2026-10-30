import type { Valuation } from "../types/data";
import {
  formatCrore,
  formatDate,
  formatPercent,
  formatPrice,
  formatRatio,
} from "../utils/format";


interface ValuationPanelProps {
  valuation: Valuation;
}


const WIDTH = 800;
const HEIGHT = 220;
const PAD = { top: 12, right: 52, bottom: 22, left: 8 };


function PEChart({ valuation }: ValuationPanelProps) {
  const { date, pe } = valuation.pe_history;

  if (pe.length < 2) {
    return (
      <div className="chart-empty">
        Not enough history for a P/E chart yet.
      </div>
    );
  }

  const min = Math.min(...pe) * 0.95;
  const max = Math.max(...pe) * 1.05;

  const x = (i: number) =>
    PAD.left +
    (i / (pe.length - 1)) * (WIDTH - PAD.left - PAD.right);

  const y = (v: number) =>
    PAD.top +
    ((max - v) / (max - min)) * (HEIGHT - PAD.top - PAD.bottom);

  const path = pe
    .map((v, i) => `${i ? "L" : "M"}${x(i).toFixed(1)},${y(v).toFixed(1)}`)
    .join("");

  const guides = [
    { label: "High", value: valuation.pe_high },
    { label: "Median", value: valuation.pe_median },
    { label: "Low", value: valuation.pe_low },
  ].filter((g): g is { label: string; value: number } => g.value != null);

  const labelEvery = Math.ceil(pe.length / 6);


  return (
    <svg
      className="pe-chart"
      viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
      role="img"
      aria-label="Price to earnings history"
    >
      {guides.map((g) => (
        <g key={g.label}>
          <line
            x1={PAD.left}
            x2={WIDTH - PAD.right}
            y1={y(g.value)}
            y2={y(g.value)}
            className={
              g.label === "Median" ? "chart-sma" : "chart-grid"
            }
          />
          <text
            x={WIDTH - PAD.right + 6}
            y={y(g.value) + 3}
            className="chart-axis"
          >
            {g.value.toFixed(1)}x
          </text>
        </g>
      ))}

      <path
        d={path}
        fill="none"
        stroke="#7a8cff"
        strokeWidth="1.6"
      />

      <circle
        cx={x(pe.length - 1)}
        cy={y(pe[pe.length - 1])}
        r="3.5"
        fill="#7a8cff"
      />

      {date.map((d, i) =>
        i % labelEvery === 0 ? (
          <text
            key={d}
            x={x(i)}
            y={HEIGHT - 5}
            className="chart-axis"
            textAnchor={i === 0 ? "start" : "middle"}
          >
            {new Date(`${d}T00:00:00`).toLocaleDateString("en-IN", {
              month: "short",
              year: "2-digit",
            })}
          </text>
        ) : null
      )}
    </svg>
  );
}


function ValuationPanel({ valuation }: ValuationPanelProps) {
  const { pe } = valuation.pe_history;
  const current = valuation.pe_ratio;

  const percentile =
    current != null && pe.length
      ? pe.filter((v) => v <= current).length / pe.length
      : null;

  const verdict =
    percentile == null
      ? null
      : percentile >= 0.8
        ? "near the top of its range"
        : percentile <= 0.2
          ? "near the bottom of its range"
          : "within its usual range";

  const stats = [
    ["MARKET CAP", formatCrore(valuation.market_cap)],
    ["P/E (TTM)", formatRatio(current)],
    ["EARNINGS YIELD", formatPercent(valuation.earnings_yield, false)],
    ["PRICE / SALES", formatRatio(valuation.price_to_sales)],
    ["TTM EPS", `₹${formatPrice(valuation.ttm_eps)}`],
    ["PRICE", `₹${formatPrice(valuation.price)}`],
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
        <div className="section-label">P/E HISTORY (TTM)</div>

        {verdict && current != null && (
          <p className="coverage-text">
            At {current.toFixed(1)}x, the stock trades{" "}
            <strong>{verdict}</strong>: higher than{" "}
            {Math.round((percentile ?? 0) * 100)}% of sessions in
            this window (median{" "}
            {formatRatio(valuation.pe_median)}).
          </p>
        )}

        {current == null && (
          <p className="coverage-text">
            P/E is not meaningful while trailing earnings are
            negative.
          </p>
        )}

        <PEChart valuation={valuation} />
      </div>


      <p className="coverage-text source-note">
        Price as of {formatDate(valuation.price_date)}, adjusted
        for splits and bonuses. Market cap uses the share count
        from the latest filing. P/E history covers the price
        history loaded so far.
      </p>

    </div>
  );
}


export default ValuationPanel;
