import { useEffect, useState } from "react";
import type { ReactNode } from "react";

import AnnouncementsPanel from "../components/AnnouncementsPanel";
import FundamentalsPanel from "../components/FundamentalsPanel";
import PeersPanel from "../components/PeersPanel";
import PriceChart from "../components/PriceChart";
import QuoteStrip from "../components/QuoteStrip";
import ShareholdingPanel from "../components/ShareholdingPanel";
import TechnicalsPanel from "../components/TechnicalsPanel";
import ValuationPanel from "../components/ValuationPanel";

import { loadCompany } from "../services/dataService";
import type { CompanyData } from "../types/data";
import {
  formatCrore,
  formatDate,
  formatPercent,
  formatPrice,
  formatRatio,
  trendClass,
} from "../utils/format";


const researchTabs = [
  "Overview",
  "Fundamentals",
  "Valuation",
  "Technicals",
  "Peers",
  "Shareholding",
  "Announcements",
];


function EmptyState({
  icon,
  title,
  children,
}: {
  icon: string;
  title: string;
  children: ReactNode;
}) {
  return (
    <div className="empty-research module-pending">
      <div className="empty-icon">{icon}</div>
      <h2>{title}</h2>
      <p>{children}</p>
    </div>
  );
}


function LoadingState({ ticker }: { ticker: string }) {
  return (
    <div className="skeleton" aria-busy="true" aria-label={`Loading ${ticker}`}>
      <div className="skeleton-line wide" />
      <div className="skeleton-line" />
      <div className="skeleton-block" />
      <div className="skeleton-block tall" />
    </div>
  );
}


/** A plain-language summary built from the data, used when no profile exists. */
function generatedSummary(data: CompanyData): string {
  const { company, valuation, fundamentals, corporate, technicals } = data;
  const parts: string[] = [];

  const classified =
    company.sector && company.sector !== "Unclassified"
      ? ` in the ${company.sector} sector`
      : "";

  parts.push(
    `${company.name} is listed on the NSE as ${company.security.ticker}${classified}.`
  );

  if (valuation?.market_cap != null) {
    parts.push(
      `It has a market capitalisation of ₹${formatCrore(valuation.market_cap)}` +
        (valuation.pe_ratio != null
          ? ` and trades at ${valuation.pe_ratio.toFixed(1)}x trailing earnings.`
          : ".")
    );
  }

  if (fundamentals?.ttm_revenue != null) {
    parts.push(
      `Over the last four quarters it reported revenue of ₹${formatCrore(
        fundamentals.ttm_revenue
      )}` +
        (fundamentals.ttm_net_margin != null
          ? ` at a ${formatPercent(fundamentals.ttm_net_margin, false)} net margin.`
          : ".")
    );
  }

  const holding = corporate?.shareholding.at(-1);

  if (holding?.promoter != null) {
    parts.push(
      holding.promoter > 0
        ? `Promoters hold ${holding.promoter.toFixed(1)}% of the company.`
        : "It has no identified promoter group; shares are held entirely by the public."
    );
  }

  const yearReturn = technicals.returns["1Y"];

  if (yearReturn != null) {
    parts.push(
      `The stock is ${yearReturn >= 0 ? "up" : "down"} ${formatPercent(
        Math.abs(yearReturn),
        false
      )} over the past year.`
    );
  }

  return parts.join(" ");
}


function Overview({
  data,
  ticker,
  priceSection,
}: {
  data: CompanyData;
  ticker: string;
  priceSection: ReactNode;
}) {
  const { company, valuation, fundamentals, corporate, technicals } = data;
  const holding = corporate?.shareholding.at(-1);
  const recent = corporate?.announcements.slice(0, 3) ?? [];

  const metrics = [
    ["MARKET CAP", formatCrore(valuation?.market_cap)],
    ["P/E (TTM)", formatRatio(valuation?.pe_ratio)],
    ["TTM REVENUE", formatCrore(fundamentals?.ttm_revenue)],
    ["TTM NET PROFIT", formatCrore(fundamentals?.ttm_net_profit)],
    ["NET MARGIN", formatPercent(fundamentals?.ttm_net_margin, false)],
    ["1Y RETURN", formatPercent(technicals.returns["1Y"])],
    ["PROMOTER HOLDING", holding?.promoter != null ? `${holding.promoter.toFixed(2)}%` : "—"],
    [
      "52W RANGE",
      technicals.period_low != null
        ? `${formatPrice(technicals.period_low)} – ${formatPrice(technicals.period_high)}`
        : "—",
    ],
  ];


  return (
    <>
      {priceSection}

      <div className="company-overview">
        <div className="overview-main">
          <div className="section-label">ABOUT</div>
          <h2>Company snapshot</h2>
          <p>{company.description ?? generatedSummary(data)}</p>

          <div className="overview-grid">
            {metrics.map(([label, value]) => (
              <div className="overview-stat" key={label}>
                <span>{label}</span>
                <strong
                  className={
                    label === "1Y RETURN"
                      ? trendClass(technicals.returns["1Y"])
                      : ""
                  }
                >
                  {value}
                </strong>
              </div>
            ))}
          </div>
        </div>

        <div className="overview-side">
          <div className="section-label">LATEST ANNOUNCEMENTS</div>

          {recent.length === 0 ? (
            <p className="coverage-text">No recent announcements loaded.</p>
          ) : (
            <ul className="meeting-list">
              {recent.map((a, i) => (
                <li key={`${a.date}-${i}`}>
                  <time>{formatDate(a.date)}</time>
                  <p>{a.subject}</p>
                </li>
              ))}
            </ul>
          )}

          {recent.length > 0 && (
            <a
              className="side-link"
              href={`#/research/${encodeURIComponent(ticker)}/announcements`}
            >
              All announcements →
            </a>
          )}

          <div className="research-status-line">
            <span>ISIN</span>
            <strong>{company.security.isin ?? "—"}</strong>
          </div>
          <div className="research-status-line">
            <span>Series</span>
            <strong>{company.security.series ?? "—"}</strong>
          </div>
          <div className="research-status-line">
            <span>Price data</span>
            <strong>{technicals.sessions} sessions</strong>
          </div>
        </div>
      </div>
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
  } | null>(null);


  useEffect(() => {
    let cancelled = false;

    loadCompany(ticker)
      .then((data) => {
        if (!cancelled) setState({ ticker, data });
      })
      .catch(() => {
        if (!cancelled) setState({ ticker, data: null });
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
    return <LoadingState ticker={ticker} />;
  }

  if (!current.data) {
    return (
      <EmptyState icon="?" title={`We couldn't find ${ticker}`}>
        Check the ticker, or <a href="#/research">search for the company</a>{" "}
        by name.
      </EmptyState>
    );
  }

  const data = current.data;
  const { company, prices, technicals, fundamentals, valuation, peers, corporate } =
    data;

  const activeTab =
    researchTabs.find((t) => t.toLowerCase() === tab) ?? "Overview";

  const noResults = (
    <EmptyState icon="▥" title="No quarterly results yet">
      Results are currently available for the most actively traded
      companies. {company.name} will be added as coverage expands.
    </EmptyState>
  );

  const priceSection = (
    <>
      {technicals.sessions > 0 && <QuoteStrip snapshot={technicals} />}

      <div className="chart-card">
        <div className="section-label">PRICE HISTORY</div>
        <PriceChart points={prices} />
      </div>
    </>
  );

  const classification = [company.sector, company.industry].filter(
    (value, i, all) =>
      value && value !== "Unclassified" && all.indexOf(value) === i
  );


  return (
    <>
      <div className="company-header">
        <div className="company-header-top">
          <div>
            <div className="eyebrow">COMPANY RESEARCH</div>
            <h1>{company.name}</h1>

            <div className="company-meta">
              <span>NSE: {company.security.ticker ?? "—"}</span>
              {classification.map((value) => (
                <span key={value}>
                  <span className="meta-separator">•</span> {value}
                </span>
              ))}
            </div>
          </div>

          <a className="change-company-button" href="#/research">
            ← Change company
          </a>
        </div>
      </div>


      <nav className="company-tabs" aria-label="Research sections">
        {researchTabs.map((name) => (
          <a
            key={name}
            href={`#/research/${encodeURIComponent(ticker)}/${name.toLowerCase()}`}
            className={`company-tab ${name === activeTab ? "active" : ""}`}
            aria-current={name === activeTab ? "page" : undefined}
          >
            {name}
          </a>
        ))}
      </nav>


      {activeTab === "Overview" && (
        <Overview data={data} ticker={ticker} priceSection={priceSection} />
      )}

      {activeTab === "Fundamentals" &&
        (fundamentals ? (
          <FundamentalsPanel fundamentals={fundamentals} />
        ) : (
          noResults
        ))}

      {activeTab === "Valuation" &&
        (valuation ? <ValuationPanel valuation={valuation} /> : noResults)}

      {activeTab === "Technicals" && (
        <>
          {priceSection}
          {technicals.sessions > 0 && <TechnicalsPanel snapshot={technicals} />}
        </>
      )}

      {activeTab === "Peers" &&
        (peers ? (
          <PeersPanel peers={peers} ticker={ticker} />
        ) : (
          <EmptyState icon="⇄" title="No peer group yet">
            {company.name} isn't part of NSE's classified index lists yet,
            so there's no reliable peer group to compare it with.
          </EmptyState>
        ))}

      {activeTab === "Shareholding" &&
        (corporate && corporate.shareholding.length > 0 ? (
          <ShareholdingPanel shareholding={corporate.shareholding} />
        ) : (
          <EmptyState icon="◔" title="No shareholding data yet">
            Shareholding patterns are currently available for the most
            actively traded companies.
          </EmptyState>
        ))}

      {activeTab === "Announcements" &&
        (corporate ? (
          <AnnouncementsPanel corporate={corporate} />
        ) : (
          <EmptyState icon="✉" title="No announcements loaded yet">
            Announcements are currently available for the most actively
            traded companies.
          </EmptyState>
        ))}
    </>
  );
}


export default CompanyWorkspace;
