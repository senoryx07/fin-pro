import { useEffect, useMemo, useState } from "react";

import { loadIndex } from "../services/dataService";
import type { CompanySummary, SiteIndex } from "../types/data";
import {
  formatCrore,
  formatDate,
  formatPercent,
  formatPrice,
  formatRatio,
  trendClass,
} from "../utils/format";
import { researchLink } from "../utils/router";


type SortKey = "market_cap" | "change_percent" | "pe_ratio" | "name";

const PAGE_SIZE = 50;

const columns: { key: SortKey; label: string }[] = [
  { key: "name", label: "Company" },
  { key: "change_percent", label: "Change" },
  { key: "market_cap", label: "Market cap" },
  { key: "pe_ratio", label: "P/E" },
];


function sortRows(
  rows: CompanySummary[],
  key: SortKey,
  descending: boolean
): CompanySummary[] {
  const direction = descending ? -1 : 1;

  return [...rows].sort((a, b) => {
    if (key === "name") {
      return a.name.localeCompare(b.name) * direction;
    }

    const av = a[key];
    const bv = b[key];

    // Missing values sort last in either direction.
    if (av == null && bv == null) return 0;
    if (av == null) return 1;
    if (bv == null) return -1;

    return (av - bv) * direction;
  });
}


function Markets() {
  const [index, setIndex] = useState<SiteIndex | null>(null);
  const [error, setError] = useState("");
  const [filter, setFilter] = useState("");
  const [sector, setSector] = useState("All");
  const [sort, setSort] = useState<SortKey>("market_cap");
  const [descending, setDescending] = useState(true);
  const [shown, setShown] = useState(PAGE_SIZE);


  useEffect(() => {
    loadIndex()
      .then(setIndex)
      .catch(() => setError("Unable to load market data."));
  }, []);


  const sectors = useMemo(() => {
    if (!index) return [];

    const names = [...new Set(index.companies.map((c) => c.sector))];

    return ["All", ...names.sort((a, b) => a.localeCompare(b))];
  }, [index]);


  const rows = useMemo(() => {
    if (!index) return [];

    const needle = filter.trim().toLowerCase();

    const filtered = index.companies.filter(
      (c) =>
        (sector === "All" || c.sector === sector) &&
        (!needle ||
          c.name.toLowerCase().includes(needle) ||
          c.ticker.toLowerCase().includes(needle))
    );

    return sortRows(filtered, sort, descending);
  }, [index, filter, sector, sort, descending]);


  const toggleSort = (key: SortKey) => {
    if (key === sort) {
      setDescending(!descending);
    } else {
      setSort(key);
      setDescending(key !== "name");
    }
  };


  return (
    <section className="research-page">

      <div className="page-heading">
        <div>
          <div className="eyebrow">MARKETS</div>
          <h1>NSE Equities</h1>
          <p>
            {index
              ? `${index.companies.length.toLocaleString(
                  "en-IN"
                )} companies · prices as of ${formatDate(
                  index.latest_trade_date
                )}`
              : "Loading market data..."}
          </p>
        </div>
      </div>


      {error && <div className="research-error">{error}</div>}


      <div className="markets-filters">
        <input
          type="text"
          value={filter}
          onChange={(e) => {
            setFilter(e.target.value);
            setShown(PAGE_SIZE);
          }}
          placeholder="Filter by name or ticker..."
        />

        <select
          value={sector}
          onChange={(e) => {
            setSector(e.target.value);
            setShown(PAGE_SIZE);
          }}
        >
          {sectors.map((s) => (
            <option key={s}>{s}</option>
          ))}
        </select>
      </div>


      <div className="chart-card">
        <div className="tech-table-wrap">
          <table className="tech-table markets-table">
            <thead>
              <tr>
                {columns.map((column) => (
                  <th key={column.key}>
                    <button
                      className="sort-button"
                      onClick={() => toggleSort(column.key)}
                    >
                      {column.label}
                      {sort === column.key
                        ? descending
                          ? " ↓"
                          : " ↑"
                        : ""}
                    </button>
                  </th>
                ))}
                <th>Price</th>
              </tr>
            </thead>
            <tbody>
              {rows.slice(0, shown).map((c) => (
                <tr key={c.ticker}>
                  <td>
                    <a
                      className="markets-company"
                      href={researchLink(c.ticker)}
                    >
                      <strong>{c.name}</strong>
                      <span>
                        {c.ticker} · {c.sector}
                      </span>
                    </a>
                  </td>
                  <td className={trendClass(c.change_percent)}>
                    {formatPercent(c.change_percent)}
                  </td>
                  <td>{formatCrore(c.market_cap)}</td>
                  <td>{formatRatio(c.pe_ratio)}</td>
                  <td>₹{formatPrice(c.last_close)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {shown < rows.length && (
          <button
            className="show-more"
            onClick={() => setShown(shown + PAGE_SIZE)}
          >
            Show more ({rows.length - shown} remaining)
          </button>
        )}
      </div>

    </section>
  );
}


export default Markets;
