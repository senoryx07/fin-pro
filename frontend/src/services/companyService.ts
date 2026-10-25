import type { Company } from "../types/company";

export const API_BASE_URL = "http://127.0.0.1:8000";


export async function searchCompanies(
  query: string
): Promise<Company[]> {
  const trimmedQuery = query.trim();

  if (!trimmedQuery) {
    return [];
  }

  const response = await fetch(
    `${API_BASE_URL}/api/companies/search?q=${encodeURIComponent(
      trimmedQuery
    )}`
  );

  if (!response.ok) {
    throw new Error(
      "Unable to search companies."
    );
  }

  const data: Company[] =
    await response.json();

  return data;
}


export async function getCompany(
  ticker: string
): Promise<Company> {
  const response = await fetch(
    `${API_BASE_URL}/api/companies/${encodeURIComponent(
      ticker
    )}`
  );

  if (!response.ok) {
    throw new Error(
      "Unable to load company."
    );
  }

  const data: Company =
    await response.json();

  return data;
}