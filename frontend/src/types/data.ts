import type { Company } from "./company";
import type {
  PricePoint,
  TechnicalSnapshot,
} from "./market";


export interface CompanySummary {
  ticker: string;
  name: string;
  sector: string;
  industry: string;
  last_close: number | null;
  change_percent: number | null;
  market_cap: number | null;
  pe_ratio: number | null;
  return_1y: number | null;
  ttm_revenue: number | null;
  ttm_net_margin: number | null;
  revenue_growth: number | null;
  profit_growth: number | null;
  avg_traded_value: number | null;
  has_financials: boolean;
}

export interface SiteIndex {
  generated_at: string;
  latest_trade_date: string | null;
  companies: CompanySummary[];
}

export interface QuarterlyResult {
  period_end: string;
  revenue: number | null;
  other_income: number | null;
  expenses: number | null;
  operating_profit: number | null;
  operating_margin: number | null;
  finance_costs: number | null;
  depreciation: number | null;
  profit_before_tax: number | null;
  tax: number | null;
  net_profit_owners: number | null;
  net_margin: number | null;
  eps_basic: number | null;
  adjusted_eps: number | null;
  revenue_growth_yoy: number | null;
  profit_growth_yoy: number | null;
}

export interface AnnualResult {
  fiscal_year: string;
  period_end: string;
  revenue: number | null;
  net_profit_owners: number | null;
  net_margin: number | null;
  adjusted_eps: number | null;
  revenue_growth: number | null;
  profit_growth: number | null;
}

export interface Fundamentals {
  ticker: string;
  basis: string | null;
  available_bases: string[];
  is_bank: boolean;
  shares_outstanding: number | null;
  latest_period: string | null;
  last_filed: string | null;
  ttm_revenue: number | null;
  ttm_net_profit: number | null;
  ttm_eps: number | null;
  ttm_net_margin: number | null;
  quarters: QuarterlyResult[];
  annual: AnnualResult[];
}

export interface Valuation {
  ticker: string;
  basis: string | null;
  price: number | null;
  price_date: string | null;
  shares_outstanding: number | null;
  market_cap: number | null;
  ttm_eps: number | null;
  pe_ratio: number | null;
  earnings_yield: number | null;
  price_to_sales: number | null;
  pe_history: { date: string[]; pe: number[] };
  pe_median: number | null;
  pe_low: number | null;
  pe_high: number | null;
}

export interface PriceAdjustment {
  trade_date: string;
  ratio: number;
}

export interface CompanyData {
  company: Company;
  prices: PricePoint[];
  adjustments: PriceAdjustment[];
  technicals: TechnicalSnapshot;
  fundamentals: Fundamentals | null;
  valuation: Valuation | null;
  peers: PeerGroup | null;
  corporate: CorporateInfo | null;
}

export interface ShareholdingPeriod {
  date: string;
  promoter: number | null;
  public: number | null;
  employee_trusts: number | null;
}

export interface CorporateInfo {
  announcements: {
    date: string | null;
    subject: string;
    text: string;
    url: string | null;
  }[];
  actions: { ex_date: string; purpose: string }[];
  meetings: { date: string; purpose: string }[];
  shareholding: ShareholdingPeriod[];
}

export interface PeerGroup {
  group: string;
  group_size: number;
  companies: CompanySummary[];
}
