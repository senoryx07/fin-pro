import type { TechnicalSnapshot } from "../types/market";
import {
  formatCompact,
  formatDate,
  formatPercent,
  formatPrice,
  trendClass,
} from "../utils/format";


interface QuoteStripProps {
  snapshot: TechnicalSnapshot;
}


function QuoteStrip({ snapshot }: QuoteStripProps) {
  const tone = trendClass(snapshot.change);

  const stats = [
    ["DAY RANGE", `${formatPrice(snapshot.day_low)} – ${formatPrice(snapshot.day_high)}`],
    ["PERIOD RANGE", `${formatPrice(snapshot.period_low)} – ${formatPrice(snapshot.period_high)}`],
    ["VOLUME", formatCompact(snapshot.volume)],
    ["AVG VOL (20D)", formatCompact(snapshot.average_volume_20)],
  ];


  return (
    <div className="quote-strip">

      <div className="quote-price">
        <span className="section-label">
          LAST CLOSE · {formatDate(snapshot.as_of)}
        </span>

        <div>
          <strong>₹{formatPrice(snapshot.last_close)}</strong>

          <span className={`quote-change ${tone}`}>
            {snapshot.change != null && snapshot.change > 0
              ? "+"
              : ""}
            {formatPrice(snapshot.change)} (
            {formatPercent(snapshot.change_percent)})
          </span>
        </div>
      </div>

      <div className="quote-stats">
        {stats.map(([label, value]) => (
          <div key={label}>
            <span>{label}</span>
            <strong>{value}</strong>
          </div>
        ))}
      </div>

    </div>
  );
}


export default QuoteStrip;
