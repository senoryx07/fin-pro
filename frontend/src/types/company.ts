export interface Security {
  ticker: string | null;
  exchange: string;
  isin: string | null;
  security_type: string;
  series: string | null;
  exchange_code: string | null;
  status: string;
}

export interface Company {
  name: string;
  sector: string;
  industry: string;
  description: string;
  security: Security;
}

export interface CompanySearchResponse {
  query: string;
  count: number;
  results: Company[];
}