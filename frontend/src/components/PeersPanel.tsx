import type { CompanySummary, PeerGroup } from "../types/data";
import {
  formatCrore,
  formatPercent,
  formatRatio,
  trendClass,
} from "../utils/format";
import { researchLink } from "../utils/router";


interface PeersPanelProps {
  peers: PeerGroup;
  ticker: string;
}

type Column = {
  label: string;
  value: (c: CompanySummary) => number | null;
  format: (v: number | null) => string;
  tone?: boolean;
};


const columns: Column[] = [
  { label: "Market cap", value: (c) => c.market_cap, format: formatCrore },
  { label: "P/E", value: (c) => c.pe_ratio, format: (v) => formatRatio(v) },
  { label: "TTM revenue", value: (c) => c.ttm_revenue, format: formatCrore },
  {
    label: "Net margin",
    value: (c) => c.ttm_net_margin,
    format: (v) => formatPercent(v, false),
  },
  {
    label: "Revenue growth",
    value: (c) => c.revenue_growth,
    format: (v) => formatPercent(v),
    tone: true,
  },
  {
    label: "Profit growth",
    value: (c) => c.profit_growth,
    format: (v) => formatPercent(v),
    tone: true,
  },
  {
    label: "1Y return",
    value: (c) => c.return_1y,
    format: (v) => formatPercent(v),
    tone: true,
  },
];


function median(values: (number | null)[]): number | null {
  const sorted = values
    .filter((v): v is number => v != null)
    .sort((a, b) => a - b);

  if (!sorted.length) return null;

  const middle = Math.floor(sorted.length / 2);

  return sorted.length % 2
    ? sorted[middle]
    : (sorted[middle - 1] + sorted[middle]) / 2;
}


function PeersPanel({ peers, ticker }: PeersPanelProps) {
  const companies = peers.companies;


  return (
    <div className="fundamentals">
      <div className="chart-card">
        <div className="section-label">
          PEERS · {peers.group.toUpperCase()}
        </div>

        <p className="coverage-text">
          The {companies.length} largest of {peers.group_size}{" "}
          companies classified as {peers.group}. Growth figures
          compare the latest quarter with the same quarter a year
          earlier.
        </p>

        <div className="tech-table-wrap">
          <table className="tech-table results-table peers-table">
            <thead>
              <tr>
                <th>Company</th>
                {columns.map((column) => (
                  <th key={column.label}>{column.label}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {companies.map((c) => (
                <tr
                  key={c.ticker}
                  className={c.ticker === ticker ? "current-row" : ""}
                >
                  <td>
                    <a
                      className="markets-company"
                      href={researchLink(c.ticker)}
                    >
                      <strong>{c.name}</strong>
                      <span>{c.ticker}</span>
                    </a>
                  </td>
                  {columns.map((column) => {
                    const value = column.value(c);

                    return (
                      <td
                        key={column.label}
                        className={column.tone ? trendClass(value) : ""}
                      >
                        {column.format(value)}
                      </td>
                    );
                  })}
                </tr>
              ))}

              <tr className="strong-row">
                <td>Median</td>
                {columns.map((column) => (
                  <td key={column.label}>
                    {column.format(median(companies.map(column.value)))}
                  </td>
                ))}
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <p className="coverage-text source-note">
        Classification from NSE index constituent lists. Companies
        without loaded quarterly results show blanks for financial
        columns.
      </p>
    </div>
  );
}


export default PeersPanel;
