import type { ShareholdingPeriod } from "../types/data";
import { formatDate } from "../utils/format";


interface ShareholdingPanelProps {
  shareholding: ShareholdingPeriod[];
}


const quarterLabel = (value: string) =>
  new Date(`${value}T00:00:00`).toLocaleDateString("en-IN", {
    month: "short",
    year: "2-digit",
  });


function change(current: number | null, previous: number | null) {
  if (current == null || previous == null) return null;

  return current - previous;
}


function ChangeValue({ value }: { value: number | null }) {
  if (value == null) return <strong>—</strong>;

  const tone = Math.abs(value) < 0.005 ? "" : value > 0 ? "positive" : "negative";

  return (
    <strong className={tone}>
      {value > 0 ? "+" : ""}
      {value.toFixed(2)} pts
    </strong>
  );
}


function ShareholdingPanel({ shareholding }: ShareholdingPanelProps) {
  const latest = shareholding[shareholding.length - 1];
  const previous = shareholding[shareholding.length - 2] ?? null;
  const yearAgo = shareholding[shareholding.length - 5] ?? null;


  return (
    <div className="fundamentals">

      <div className="quote-strip">
        <div className="quote-stats">
          <div>
            <span>PROMOTERS</span>
            <strong>{latest.promoter?.toFixed(2) ?? "—"}%</strong>
          </div>
          <div>
            <span>PUBLIC</span>
            <strong>{latest.public?.toFixed(2) ?? "—"}%</strong>
          </div>
          <div>
            <span>CHANGE QOQ</span>
            <ChangeValue
              value={change(latest.promoter, previous?.promoter ?? null)}
            />
          </div>
          <div>
            <span>CHANGE YOY</span>
            <ChangeValue
              value={change(latest.promoter, yearAgo?.promoter ?? null)}
            />
          </div>
          <div>
            <span>AS OF</span>
            <strong>{formatDate(latest.date)}</strong>
          </div>
        </div>
      </div>


      <div className="chart-card">
        <div className="section-label">OWNERSHIP BY QUARTER</div>

        <div className="chart-legend trend-legend">
          <span><i className="legend-promoter" />Promoters</span>
          <span><i className="legend-public" />Public</span>
          <span><i className="legend-trust" />Employee trusts</span>
        </div>

        <div className="holding-rows">
          {[...shareholding].reverse().map((period) => (
            <div className="holding-row" key={period.date}>
              <span className="holding-date">
                {quarterLabel(period.date)}
              </span>

              <div
                className="holding-bar"
                role="img"
                aria-label={`Promoters ${period.promoter ?? 0}%, public ${
                  period.public ?? 0
                }%`}
              >
                <span
                  className="seg-promoter"
                  style={{ width: `${period.promoter ?? 0}%` }}
                />
                <span
                  className="seg-public"
                  style={{ width: `${period.public ?? 0}%` }}
                />
                <span
                  className="seg-trust"
                  style={{ width: `${period.employee_trusts ?? 0}%` }}
                />
              </div>

              <span className="holding-value">
                {period.promoter?.toFixed(2) ?? "—"}%
              </span>
            </div>
          ))}
        </div>
      </div>


      <p className="coverage-text source-note">
        Quarterly shareholding pattern filed with NSE. "Public"
        includes institutions (FIIs, mutual funds, insurers) and
        retail investors.
      </p>

    </div>
  );
}


export default ShareholdingPanel;
