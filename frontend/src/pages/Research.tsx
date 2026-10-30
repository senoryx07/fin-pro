import { useEffect, useState } from "react";

import CompanyWorkspace from "./CompanyWorkspace";

import { loadIndex, searchCompanies } from "../services/dataService";

import type { CompanySummary } from "../types/data";

import {
  formatCrore,
  formatPercent,
  formatPrice,
  trendClass,
} from "../utils/format";
import { navigate } from "../utils/router";


interface ResearchProps {
  ticker?: string;
  tab?: string;
}


function CompanySearch() {
  const [query, setQuery] = useState("");

  const [results, setResults] = useState<
    CompanySummary[]
  >([]);

  const [error, setError] = useState("");

  const [popular, setPopular] = useState<CompanySummary[]>([]);


  useEffect(() => {
    loadIndex()
      .then((index) => setPopular(index.companies.slice(0, 12)))
      .catch(() => setPopular([]));
  }, []);


  useEffect(() => {
    let cancelled = false;

    // Search runs in the browser against the static index, so a short
    // debounce is enough.
    const timeout = setTimeout(() => {
      searchCompanies(query)
        .then((companies) => {
          if (!cancelled) {
            setResults(companies);
            setError("");
          }
        })
        .catch(() => {
          if (!cancelled) {
            setError("Unable to load the company list.");
          }
        });
    }, 120);

    return () => {
      cancelled = true;
      clearTimeout(timeout);
    };
  }, [query]);


  return (
    <>
      <div className="page-heading">
        <div>
          <div className="eyebrow">RESEARCH</div>
          <h1>Company Research</h1>
          <p>
            Search for a company to begin a structured
            financial analysis.
          </p>
        </div>
      </div>


      <div className="research-search-panel search-panel-active">

        <div className="large-search-icon">⌕</div>

        <div className="search-panel-content">

          <div className="search-panel-label">
            COMPANY SEARCH
          </div>

          <input
            autoFocus
            type="text"
            value={query}
            onChange={(event) =>
              setQuery(event.target.value)
            }
            onKeyDown={(event) => {
              if (event.key === "Enter" && results[0]) {
                navigate("research", results[0].ticker);
              }
            }}
            placeholder="Enter company name or ticker..."
          />

          <div className="search-panel-hint">
            Try Reliance, TCS, Infosys, HDFC Bank or
            Asian Paints
          </div>

        </div>

      </div>


      {error && (
        <div className="research-error">{error}</div>
      )}


      {results.length > 0 && (
        <div className="company-results">

          <div className="results-header">
            <span>SEARCH RESULTS</span>
            <span>{results.length} SHOWN</span>
          </div>

          {results.map((company) => (
            <a
              key={company.ticker}
              className="company-result"
              href={`#/research/${encodeURIComponent(company.ticker)}`}
            >
              <div className="company-result-main">
                <div className="company-result-name">
                  {company.name}
                </div>
                <div className="company-result-description">
                  {company.sector} · {company.industry}
                </div>
              </div>

              <div className="company-result-meta">
                <strong>{company.ticker}</strong>
                <span>₹{formatPrice(company.last_close)}</span>
                <span className={trendClass(company.change_percent)}>
                  {formatPercent(company.change_percent)}
                </span>
                {company.market_cap != null && (
                  <span>{formatCrore(company.market_cap)}</span>
                )}
              </div>
            </a>
          ))}

        </div>
      )}


      {!query && popular.length > 0 && (
        <div className="popular">
          <div className="section-label">POPULAR COMPANIES</div>

          <div className="popular-grid">
            {popular.map((company) => (
              <a
                key={company.ticker}
                className="popular-card"
                href={`#/research/${encodeURIComponent(company.ticker)}`}
              >
                <strong>{company.name}</strong>
                <span>
                  {company.ticker}
                  <em className={trendClass(company.change_percent)}>
                    {formatPercent(company.change_percent)}
                  </em>
                </span>
              </a>
            ))}
          </div>
        </div>
      )}
    </>
  );
}


function Research({ ticker, tab }: ResearchProps) {
  return (
    <section className="research-page">
      {ticker ? (
        <CompanyWorkspace
          ticker={ticker.toUpperCase()}
          tab={(tab ?? "overview").toLowerCase()}
        />
      ) : (
        <CompanySearch />
      )}
    </section>
  );
}


export default Research;
