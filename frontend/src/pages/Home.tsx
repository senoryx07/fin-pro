import { useEffect, useState } from "react";

import { loadIndex, searchCompanies } from "../services/dataService";
import type { CompanySummary, SiteIndex } from "../types/data";
import {
  formatCrore,
  formatDate,
  formatPercent,
  formatPrice,
  trendClass,
} from "../utils/format";
import { navigate, researchLink } from "../utils/router";


function CompanyList({
  title,
  companies,
}: {
  title: string;
  companies: CompanySummary[];
}) {
  return (
    <div className="chart-card home-list">
      <div className="section-label">{title}</div>

      {companies.map((c) => (
        <a
          key={c.ticker}
          className="home-list-row"
          href={researchLink(c.ticker)}
        >
          <div>
            <strong>{c.name}</strong>
            <span>
              {c.ticker} · {formatCrore(c.market_cap)}
            </span>
          </div>
          <div>
            <strong>₹{formatPrice(c.last_close)}</strong>
            <span className={trendClass(c.change_percent)}>
              {formatPercent(c.change_percent)}
            </span>
          </div>
        </a>
      ))}
    </div>
  );
}


function Home() {
  const [index, setIndex] = useState<SiteIndex | null>(null);
  const [query, setQuery] = useState("");


  useEffect(() => {
    loadIndex()
      .then(setIndex)
      .catch(() => setIndex(null));
  }, []);


  const openFirstMatch = async () => {
    const [first] = await searchCompanies(query, 1);

    if (first) {
      navigate("research", first.ticker);
    } else {
      navigate("research");
    }
  };


  const largest = index?.companies.slice(0, 8) ?? [];

  // Movers among the 200 most-traded stocks, so illiquid small caps
  // don't dominate.
  const liquid = [...(index?.companies ?? [])]
    .filter((c) => c.change_percent != null)
    .sort(
      (a, b) => (b.avg_traded_value ?? 0) - (a.avg_traded_value ?? 0)
    )
    .slice(0, 200);

  const gainers = [...liquid]
    .sort((a, b) => (b.change_percent ?? 0) - (a.change_percent ?? 0))
    .slice(0, 5);

  const losers = [...liquid]
    .sort((a, b) => (a.change_percent ?? 0) - (b.change_percent ?? 0))
    .slice(0, 5);


  return (
    <section className="home-page">
      <div className="hero-section">
        <div className="eyebrow">FINANCIAL RESEARCH TERMINAL</div>

        <h1>
          Understand the business
          <br />
          behind the numbers.
        </h1>

        <p className="hero-description">
          Prices, quarterly results, valuation and technicals for
          every NSE-listed company, in one place.
        </p>

        <form
          className="hero-search"
          onSubmit={(event) => {
            event.preventDefault();
            openFirstMatch();
          }}
        >
          <span className="hero-search-icon">⌕</span>

          <input
            type="text"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Search a company, ticker or industry..."
          />

          <span className="hero-search-hint">ENTER</span>
        </form>
      </div>


      {index && (
        <>
          <div className="section-heading">
            <div>
              <h2>Market snapshot</h2>
              <p>
                NSE end-of-day data as of{" "}
                {formatDate(index.latest_trade_date)}.
              </p>
            </div>
          </div>

          <div className="home-grid">
            <CompanyList
              title="LARGEST COMPANIES"
              companies={largest}
            />
            <CompanyList title="TOP GAINERS" companies={gainers} />
            <CompanyList title="TOP LOSERS" companies={losers} />
          </div>
        </>
      )}


      <div className="home-footer-note">
        <span className="status-dot"></span>
        <span>
          Data from NSE bhavcopy and quarterly results filings.
          Not investment advice.
        </span>
      </div>
    </section>
  );
}


export default Home;
