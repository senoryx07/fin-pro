import type { Company } from "../types/company";
import type {
  CompanyData,
  CompanySummary,
  SiteIndex,
} from "../types/data";
import type {
  PricePoint,
  TechnicalSnapshot,
} from "../types/market";


// Resolves against the deployed base path (e.g. /Fin-Pro/ on GitHub Pages).
const DATA_URL = `${import.meta.env.BASE_URL}data`;


let indexPromise: Promise<SiteIndex> | null = null;

const companyCache = new Map<
  string,
  Promise<CompanyData>
>();


async function fetchJson<T>(url: string): Promise<T> {
  const response = await fetch(url);

  if (!response.ok) {
    throw new Error(`Request failed: ${response.status}`);
  }

  return response.json();
}


export function loadIndex(): Promise<SiteIndex> {
  if (!indexPromise) {
    indexPromise = fetchJson<SiteIndex>(
      `${DATA_URL}/index.json`
    ).catch((error) => {
      indexPromise = null;
      throw error;
    });
  }

  return indexPromise;
}


export async function searchCompanies(
  query: string,
  limit = 25
): Promise<CompanySummary[]> {
  const needle = query.trim().toLowerCase();

  if (!needle) {
    return [];
  }

  const { companies } = await loadIndex();

  const scored: { company: CompanySummary; score: number }[] = [];

  for (const company of companies) {
    const ticker = company.ticker.toLowerCase();
    const name = company.name.toLowerCase();

    let score = 0;

    if (ticker === needle) score = 100;
    else if (ticker.startsWith(needle)) score = 80;
    else if (name.startsWith(needle)) score = 70;
    else if (name.includes(needle)) score = 50;
    else if (ticker.includes(needle)) score = 40;
    else if (
      company.industry.toLowerCase().includes(needle) ||
      company.sector.toLowerCase().includes(needle)
    )
      score = 10;

    if (score) {
      scored.push({ company, score });
    }
  }

  // The index is sorted by market cap, and sort() is stable, so larger
  // companies win ties.
  scored.sort((a, b) => b.score - a.score);

  return scored.slice(0, limit).map((s) => s.company);
}


interface RawCompanyData {
  company: Company;
  prices: {
    date: string[];
    open: (number | null)[];
    high: (number | null)[];
    low: (number | null)[];
    close: number[];
    volume: (number | null)[];
    sma_20: (number | null)[];
    bollinger_upper: (number | null)[];
    bollinger_lower: (number | null)[];
  };
  adjustments: CompanyData["adjustments"];
  technicals: TechnicalSnapshot;
  fundamentals: CompanyData["fundamentals"];
  valuation: CompanyData["valuation"];
  peers: CompanyData["peers"];
  corporate: CompanyData["corporate"];
}


function toPricePoints(
  prices: RawCompanyData["prices"]
): PricePoint[] {
  return prices.date.map((date, i) => ({
    trade_date: date,
    open: prices.open[i],
    high: prices.high[i],
    low: prices.low[i],
    close: prices.close[i],
    volume: prices.volume[i],
    sma_20: prices.sma_20[i],
    bollinger_upper: prices.bollinger_upper[i],
    bollinger_lower: prices.bollinger_lower[i],
  }));
}


export function loadCompany(
  ticker: string
): Promise<CompanyData> {
  const key = ticker.toUpperCase();

  let promise = companyCache.get(key);

  if (!promise) {
    promise = fetchJson<RawCompanyData>(
      `${DATA_URL}/companies/${encodeURIComponent(key)}.json`
    )
      .then((raw) => ({
        ...raw,
        prices: toPricePoints(raw.prices),
      }))
      .catch((error) => {
        companyCache.delete(key);
        throw error;
      });

    companyCache.set(key, promise);
  }

  return promise;
}
