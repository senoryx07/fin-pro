import { API_BASE_URL } from "./companyService";
import type {
  PriceSeries,
  TechnicalSnapshot,
} from "../types/market";


export async function getPrices(
  ticker: string
): Promise<PriceSeries> {
  const response = await fetch(
    `${API_BASE_URL}/api/companies/${encodeURIComponent(
      ticker
    )}/prices`
  );

  if (!response.ok) {
    throw new Error(
      "Unable to load price history."
    );
  }

  return response.json();
}


export async function getTechnicals(
  ticker: string
): Promise<TechnicalSnapshot> {
  const response = await fetch(
    `${API_BASE_URL}/api/companies/${encodeURIComponent(
      ticker
    )}/technicals`
  );

  if (!response.ok) {
    throw new Error(
      "Unable to load technicals."
    );
  }

  return response.json();
}
