const priceFormatter = new Intl.NumberFormat("en-IN", {
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
});

const compactFormatter = new Intl.NumberFormat("en-IN", {
  notation: "compact",
  maximumFractionDigits: 2,
});


export function formatPrice(
  value: number | null | undefined
): string {
  return value == null
    ? "—"
    : priceFormatter.format(value);
}


export function formatCompact(
  value: number | null | undefined
): string {
  return value == null
    ? "—"
    : compactFormatter.format(value);
}


export function formatPercent(
  value: number | null | undefined,
  signed = true
): string {
  if (value == null) {
    return "—";
  }

  const percent = (value * 100).toFixed(2);

  return signed && value > 0
    ? `+${percent}%`
    : `${percent}%`;
}


export function formatDate(
  value: string | null | undefined
): string {
  if (!value) {
    return "—";
  }

  return new Date(`${value}T00:00:00`).toLocaleDateString(
    "en-IN",
    { day: "2-digit", month: "short", year: "numeric" }
  );
}


export function trendClass(
  value: number | null | undefined
): string {
  if (value == null || value === 0) {
    return "";
  }

  return value > 0 ? "positive" : "negative";
}
