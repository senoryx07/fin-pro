import { useEffect, useState } from "react";

import FundamentalsPanel from "../components/FundamentalsPanel";
import PeersPanel from "../components/PeersPanel";
import PriceChart from "../components/PriceChart";
import QuoteStrip from "../components/QuoteStrip";
import TechnicalsPanel from "../components/TechnicalsPanel";
import ValuationPanel from "../components/ValuationPanel";

import {
  loadCompany,
  searchCompanies,
} from "../services/dataService";

import type {
  CompanyData,
  CompanySummary,
} from "../types/data";

import {
  formatCrore,
  formatPercent,
  formatPrice,
  trendClass,
} from "../utils/format";
import { navigate } from "../utils/router";


const researchTabs = [
  "Overview",
  "Fundamentals",
  "Valuation",
  "Technicals",
  "Peers",
  "Business",
  "Management",
  "News",
  "Filings",
];

const liveTabs = new Set([
  "Overview",
  "Fundamentals",
  "Valuation",
  "Technicals",
  "Peers",
]);


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


      {!query && (
        <div className="empty-research">
          <div className="empty-icon">◎</div>
          <h2>No company selected</h2>
          <p>
            Search for a company to open its complete
            research workspace.
          </p>
        </div>
      )}
    </>
  );
}


function CompanyWorkspace({
  ticker,
  tab,
}: {
  ticker: string;
  tab: string;
}) {
  const [state, setState] = useState<{
    ticker: string;
    data: CompanyData | null;
    error: string;
  } | null>(null);


  useEffect(() => {
    let cancelled = false;

    loadCompany(ticker)
      .then((data) => {
        if (!cancelled) {
          setState({ ticker, data, error: "" });
        }
      })
      .catch(() => {
        if (!cancelled) {
          setState({
            ticker,
            data: null,
            error: `No data found for ${ticker}.`,
          });
        }
      });

    return () => {
      cancelled = true;
    };
  }, [ticker]);


  const current = state?.ticker === ticker ? state : null;

  const companyName = current?.data?.company.name;

  useEffect(() => {
    document.title = companyName
      ? `${companyName} (${ticker}) · Fin Pro`
      : "Fin Pro · Indian Stock Research";
  }, [companyName, ticker]);

  if (!current) {
    return <div className="market-loading">LOADING {ticker}</div>;
  }

  if (!current.data) {
    return (
      <>
        <div className="research-error">{current.error}</div>
        <a className="change-company-button" href="#/research">
          ← Search companies
        </a>
      </>
    );
  }

  const { company, prices, technicals, fundamentals, valuation, peers } =
    current.data;

  const activeTab =
    researchTabs.find((t) => t.toLowerCase() === tab) ?? "Overview";

  const hasFinancials = fundamentals != null;

  const noFinancials = (
    <div className="empty-research module-pending">
      <div className="empty-icon">▥</div>
      <h2>Financial results not loaded yet</h2>
      <p>
        Quarterly results for {company.security.ticker} have not
        been imported. Run the financial loader for this ticker
        and re-export the site data.
      </p>
    </div>
  );

  const priceSection = (
    <>
      {technicals.sessions > 0 && (
        <QuoteStrip snapshot={technicals} />
      )}

      <div className="chart-card">
        <div className="section-label">PRICE HISTORY</div>
        <PriceChart points={prices} />
      </div>
    </>
  );


  return (
    <>
      <div className="company-header">
        <div className="company-header-top">
          <div>
            <div className="eyebrow">COMPANY RESEARCH</div>
            <h1>{company.name}</h1>

            <div className="company-meta">
              <span>
                {company.security.exchange}:{" "}
                {company.security.ticker ?? "—"}
              </span>
              <span className="meta-separator">•</span>
              <span>{company.sector}</span>
              <span className="meta-separator">•</span>
              <span>{company.industry}</span>
            </div>
          </div>

          <a className="change-company-button" href="#/research">
            ← Change Company
          </a>
        </div>
      </div>


      <div className="company-tabs">
        {researchTabs.map((name) => (
          <a
            key={name}
            href={`#/research/${encodeURIComponent(
              ticker
            )}/${name.toLowerCase()}`}
            className={`company-tab ${
              name === activeTab ? "active" : ""
            } ${liveTabs.has(name) ? "" : "pending"}`}
          >
            {name}
          </a>
        ))}
      </div>


      {activeTab === "Overview" && (
        <>
          {priceSection}

          <div className="company-overview">
            <div className="overview-main">
              <div className="section-label">
                BUSINESS OVERVIEW
              </div>
              <h2>Understanding the company</h2>
              <p>{company.description}</p>

              <div className="overview-grid">
                <div className="overview-stat">
                  <span>MARKET CAP</span>
                  <strong>
                    {formatCrore(valuation?.market_cap)}
                  </strong>
                </div>
                <div className="overview-stat">
                  <span>P/E (TTM)</span>
                  <strong>
                    {valuation?.pe_ratio != null
                      ? `${valuation.pe_ratio.toFixed(1)}x`
                      : "—"}
                  </strong>
                </div>
                <div className="overview-stat">
                  <span>TTM REVENUE</span>
                  <strong>
                    {formatCrore(fundamentals?.ttm_revenue)}
                  </strong>
                </div>
                <div className="overview-stat">
                  <span>TTM NET PROFIT</span>
                  <strong>
                    {formatCrore(fundamentals?.ttm_net_profit)}
                  </strong>
                </div>
              </div>
            </div>

            <div className="overview-side">
              <div className="section-label">LISTING</div>

              <div className="research-status-line">
                <span>Ticker</span>
                <strong>{company.security.ticker}</strong>
              </div>
              <div className="research-status-line">
                <span>ISIN</span>
                <strong>{company.security.isin ?? "—"}</strong>
              </div>
              <div className="research-status-line">
                <span>Series</span>
                <strong>{company.security.series ?? "—"}</strong>
              </div>
              <div className="research-status-line">
                <span>Price history</span>
                <strong>{technicals.sessions} sessions</strong>
              </div>
              <div className="research-status-line">
                <span>Financials</span>
                <strong>
                  {hasFinancials
                    ? `${fundamentals.quarters.length} quarters`
                    : "Not loaded"}
                </strong>
              </div>
            </div>
          </div>
        </>
      )}


      {activeTab === "Fundamentals" &&
        (hasFinancials ? (
          <FundamentalsPanel fundamentals={fundamentals} />
        ) : (
          noFinancials
        ))}


      {activeTab === "Valuation" &&
        (valuation ? (
          <ValuationPanel valuation={valuation} />
        ) : (
          noFinancials
        ))}


      {activeTab === "Technicals" && (
        <>
          {priceSection}
          {technicals.sessions > 0 && (
            <TechnicalsPanel snapshot={technicals} />
          )}
        </>
      )}


      {activeTab === "Peers" &&
        (peers ? (
          <PeersPanel peers={peers} ticker={ticker} />
        ) : (
          <div className="empty-research module-pending">
            <div className="empty-icon">⇄</div>
            <h2>No peer group yet</h2>
            <p>
              {company.name} is not in NSE's classified index
              lists, so there is no peer group for it yet.
            </p>
          </div>
        ))}


      {!liveTabs.has(activeTab) && (
        <div className="empty-research module-pending">
          <div className="empty-icon">◌</div>
          <h2>{activeTab} module in development</h2>
          <p>
            This research module is planned but not built
            yet.
          </p>
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
