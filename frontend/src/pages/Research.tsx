import { useEffect, useState } from "react";

import {
  getCompany,
  searchCompanies,
} from "../services/companyService";

import {
  getPrices,
  getTechnicals,
} from "../services/marketService";

import PriceChart from "../components/PriceChart";
import QuoteStrip from "../components/QuoteStrip";
import TechnicalsPanel from "../components/TechnicalsPanel";

import type { Company } from "../types/company";
import type {
  PricePoint,
  TechnicalSnapshot,
} from "../types/market";


const researchTabs = [
  "Overview",
  "Business",
  "Management",
  "Industry",
  "Fundamentals",
  "Valuation",
  "Technicals",
  "Peers",
  "News",
  "Filings",
];

const liveTabs = new Set([
  "Overview",
  "Technicals",
]);


function Research() {
  const [query, setQuery] = useState("");

  const [results, setResults] = useState<
    Company[]
  >([]);

  const [selectedCompany, setSelectedCompany] =
    useState<Company | null>(null);

  const [loading, setLoading] =
    useState(false);

  const [error, setError] =
    useState("");

  const [activeTab, setActiveTab] =
    useState("Overview");

  const [market, setMarket] = useState<{
    ticker: string;
    prices: PricePoint[];
    technicals: TechnicalSnapshot | null;
    error: string;
  } | null>(null);


  const selectedTicker =
    selectedCompany?.security.ticker ?? null;

  // Only use market data that belongs to the selected company.
  const currentMarket =
    market && market.ticker === selectedTicker
      ? market
      : null;

  const prices = currentMarket?.prices ?? [];

  const technicals =
    currentMarket?.technicals ?? null;

  const marketError = currentMarket?.error ?? "";

  const marketLoading =
    selectedTicker !== null && currentMarket === null;


  useEffect(() => {
    if (!selectedTicker) {
      return;
    }

    let cancelled = false;

    Promise.all([
      getPrices(selectedTicker),
      getTechnicals(selectedTicker),
    ])
      .then(([series, snapshot]) => {
        if (!cancelled) {
          setMarket({
            ticker: selectedTicker,
            prices: series.points,
            technicals: snapshot,
            error: "",
          });
        }
      })
      .catch(() => {
        if (!cancelled) {
          setMarket({
            ticker: selectedTicker,
            prices: [],
            technicals: null,
            error: "Unable to load market data.",
          });
        }
      });

    return () => {
      cancelled = true;
    };
  }, [selectedTicker]);


  useEffect(() => {
    const trimmedQuery = query.trim();

    if (!trimmedQuery) {
      setResults([]);
      setError("");
      return;
    }

    const timeout = setTimeout(
      async () => {
        try {
          setLoading(true);
          setError("");

          const companies =
            await searchCompanies(
              trimmedQuery
            );

          setResults(companies);
        } catch {
          setResults([]);

          setError(
            "Unable to connect to the Fin Pro backend."
          );
        } finally {
          setLoading(false);
        }
      },
      300
    );

    return () =>
      clearTimeout(timeout);
  }, [query]);


  const handleSelectCompany = async (
    ticker: string
  ) => {
    try {
      setLoading(true);
      setError("");

      const company =
        await getCompany(ticker);

      setSelectedCompany(company);

      setActiveTab("Overview");

      setQuery(company.name);

      setResults([]);
    } catch {
      setError(
        "Unable to load company information."
      );
    } finally {
      setLoading(false);
    }
  };


  const marketSection = (
    <>
      {marketLoading && (
        <div className="market-loading">
          LOADING MARKET DATA
        </div>
      )}

      {marketError && (
        <div className="research-error">
          {marketError}
        </div>
      )}

      {technicals && technicals.sessions > 0 && (
        <QuoteStrip snapshot={technicals} />
      )}

      {!marketLoading && !marketError && (
        <div className="chart-card">
          <div className="section-label">
            PRICE HISTORY
          </div>
          <PriceChart points={prices} />
        </div>
      )}
    </>
  );


  return (
    <section className="research-page">

      {!selectedCompany ? (

        <>
          <div className="page-heading">
            <div>

              <div className="eyebrow">
                RESEARCH
              </div>

              <h1>
                Company Research
              </h1>

              <p>
                Search for a company to begin a
                structured financial analysis.
              </p>

            </div>
          </div>


          <div className="research-search-panel search-panel-active">

            <div className="large-search-icon">
              ⌕
            </div>

            <div className="search-panel-content">

              <div className="search-panel-label">
                COMPANY SEARCH
              </div>

              <input
                autoFocus
                type="text"
                value={query}
                onChange={(event) =>
                  setQuery(
                    event.target.value
                  )
                }
                placeholder="Enter company name or ticker..."
              />

              <div className="search-panel-hint">
                Try Reliance, TCS, Infosys,
                HDFC Bank or Asian Paints
              </div>

            </div>

            {loading && (
              <div className="search-loading">
                SEARCHING
              </div>
            )}

          </div>


          {error && (
            <div className="research-error">
              {error}
            </div>
          )}


          {results.length > 0 && (

            <div className="company-results">

              <div className="results-header">

                <span>
                  SEARCH RESULTS
                </span>

                <span>
                  {results.length} FOUND
                </span>

              </div>


              {results.map(
                (company) => (

                  <button
                    key={
                      company.security.ticker ??
                      company.name
                    }
                    className="company-result"
                    onClick={() =>
                      company.security.ticker &&
                      handleSelectCompany(
                        company.security.ticker
                      )
                    }
                  >

                    <div className="company-result-main">

                      <div className="company-result-name">
                        {company.name}
                      </div>

                      <div className="company-result-description">
                        {company.description}
                      </div>

                    </div>


                    <div className="company-result-meta">

                      <strong>
                        {
                          company.security
                            .ticker ?? "—"
                        }
                      </strong>

                      <span>
                        {
                          company.security
                            .exchange
                        }
                      </span>

                      <span>
                        {company.sector}
                      </span>

                    </div>

                  </button>

                )
              )}

            </div>

          )}


          {!query && (

            <div className="empty-research">

              <div className="empty-icon">
                ◎
              </div>

              <h2>
                No company selected
              </h2>

              <p>
                Search for a company to open
                its complete research workspace.
              </p>

            </div>

          )}

        </>

      ) : (

        <>

          <div className="company-header">

            <div className="company-header-top">

              <div>

                <div className="eyebrow">
                  COMPANY RESEARCH
                </div>

                <h1>
                  {selectedCompany.name}
                </h1>


                <div className="company-meta">

                  <span>
                    {
                      selectedCompany
                        .security
                        .exchange
                    }
                    :{" "}
                    {
                      selectedCompany
                        .security
                        .ticker ?? "—"
                    }
                  </span>

                  <span className="meta-separator">
                    •
                  </span>

                  <span>
                    {selectedCompany.sector}
                  </span>

                  <span className="meta-separator">
                    •
                  </span>

                  <span>
                    {selectedCompany.industry}
                  </span>

                </div>

              </div>


              <button
                className="change-company-button"
                onClick={() => {

                  setSelectedCompany(
                    null
                  );

                  setQuery("");

                }}
              >
                ← Change Company
              </button>

            </div>

          </div>


          <div className="company-tabs">

            {researchTabs.map(
              (tab) => (

                <button
                  key={tab}
                  className={`company-tab ${
                    tab === activeTab
                      ? "active"
                      : ""
                  } ${
                    liveTabs.has(tab)
                      ? ""
                      : "pending"
                  }`}
                  onClick={() =>
                    setActiveTab(tab)
                  }
                >
                  {tab}
                </button>

              )
            )}

          </div>


          {activeTab === "Technicals" && (
            <>
              {marketSection}

              {technicals && technicals.sessions > 0 && (
                <TechnicalsPanel
                  snapshot={technicals}
                />
              )}
            </>
          )}


          {!liveTabs.has(activeTab) && (
            <div className="empty-research module-pending">

              <div className="empty-icon">
                ◌
              </div>

              <h2>
                {activeTab} module in development
              </h2>

              <p>
                This research module is planned
                but not built yet. Overview and
                Technicals are live.
              </p>

            </div>
          )}


          {activeTab === "Overview" && (
          <>
          {marketSection}

          <div className="company-overview">

            <div className="overview-main">

              <div className="section-label">
                BUSINESS OVERVIEW
              </div>

              <h2>
                Understanding the company
              </h2>

              <p>
                {selectedCompany.description}
              </p>


              <div className="overview-grid">

                <div className="overview-stat">

                  <span>
                    EXCHANGE
                  </span>

                  <strong>
                    {
                      selectedCompany
                        .security
                        .exchange
                    }
                  </strong>

                </div>


                <div className="overview-stat">

                  <span>
                    TICKER
                  </span>

                  <strong>
                    {
                      selectedCompany
                        .security
                        .ticker ?? "—"
                    }
                  </strong>

                </div>


                <div className="overview-stat">

                  <span>
                    SECTOR
                  </span>

                  <strong>
                    {selectedCompany.sector}
                  </strong>

                </div>


                <div className="overview-stat">

                  <span>
                    INDUSTRY
                  </span>

                  <strong>
                    {selectedCompany.industry}
                  </strong>

                </div>

              </div>

            </div>


            <div className="overview-side">

              <div className="section-label">
                RESEARCH STATUS
              </div>


              <div className="research-status">

                <span className="status-dot"></span>

                <div>

                  <strong>
                    Company loaded
                  </strong>

                  <p>
                    Research workspace
                    initialized.
                  </p>

                </div>

              </div>


              <div className="research-status-line">

                <span>
                  Data source
                </span>

                <strong>
                  Fin Pro API
                </strong>

              </div>


              <div className="research-status-line">

                <span>
                  Exchange
                </span>

                <strong>
                  {
                    selectedCompany
                      .security
                      .exchange
                  }
                </strong>

              </div>


              <div className="research-status-line">

                <span>
                  Research modules
                </span>

                <strong>
                  {liveTabs.size} of{" "}
                  {researchTabs.length} live
                </strong>

              </div>


              <div className="research-status-line">

                <span>
                  Price history
                </span>

                <strong>
                  {technicals
                    ? `${technicals.sessions} sessions`
                    : "—"}
                </strong>

              </div>

            </div>

          </div>
          </>
          )}

        </>

      )}

    </section>
  );
}


export default Research;