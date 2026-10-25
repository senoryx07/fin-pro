import type { TechnicalSnapshot } from "../types/market";
import {
  formatDate,
  formatPercent,
  formatPrice,
  trendClass,
} from "../utils/format";


interface TechnicalsPanelProps {
  snapshot: TechnicalSnapshot;
}


function rsiReading(value: number | null) {
  if (value == null) {
    return { label: "Insufficient data", tone: "" };
  }

  if (value >= 70) {
    return { label: "Overbought", tone: "negative" };
  }

  if (value <= 30) {
    return { label: "Oversold", tone: "positive" };
  }

  return { label: "Neutral", tone: "" };
}


function NeedsData({
  snapshot,
  name,
}: {
  snapshot: TechnicalSnapshot;
  name: string;
}) {
  const required =
    snapshot.availability.find((a) => a.name === name)
      ?.required_sessions ?? 0;

  return (
    <p className="needs-data">
      Needs {required} sessions of history ·{" "}
      {snapshot.sessions} stored
    </p>
  );
}


function TechnicalsPanel({
  snapshot,
}: TechnicalsPanelProps) {
  const rsi = rsiReading(snapshot.rsi_14);

  const lastClose = snapshot.last_close;

  const percentB =
    lastClose != null &&
    snapshot.bollinger_upper != null &&
    snapshot.bollinger_lower != null &&
    snapshot.bollinger_upper !== snapshot.bollinger_lower
      ? (lastClose - snapshot.bollinger_lower) /
        (snapshot.bollinger_upper - snapshot.bollinger_lower)
      : null;

  const missing = snapshot.availability.filter(
    (a) => !a.available
  );


  return (
    <div className="technicals-grid">

      <div className="tech-card">

        <div className="section-label">MOMENTUM</div>

        <h3>RSI (14)</h3>

        <div className="tech-headline">
          <strong>
            {snapshot.rsi_14 == null
              ? "—"
              : snapshot.rsi_14.toFixed(1)}
          </strong>
          <span className={rsi.tone}>{rsi.label}</span>
        </div>

        {snapshot.rsi_14 != null ? (
          <div className="rsi-meter">
            <div className="rsi-zone oversold" />
            <div className="rsi-zone neutral" />
            <div className="rsi-zone overbought" />
            <span
              className="rsi-marker"
              style={{ left: `${snapshot.rsi_14}%` }}
            />
          </div>
        ) : (
          <NeedsData snapshot={snapshot} name="RSI 14" />
        )}

        <div className="rsi-scale">
          <span>0</span>
          <span>30</span>
          <span>70</span>
          <span>100</span>
        </div>

      </div>


      <div className="tech-card">

        <div className="section-label">TREND</div>

        <h3>MACD (12, 26, 9)</h3>

        {snapshot.macd_histogram != null ? (
          <>
            <div className="tech-headline">
              <strong
                className={trendClass(
                  snapshot.macd_histogram
                )}
              >
                {snapshot.macd_histogram.toFixed(2)}
              </strong>
              <span
                className={trendClass(
                  snapshot.macd_histogram
                )}
              >
                {snapshot.macd_histogram > 0
                  ? "Bullish momentum"
                  : "Bearish momentum"}
              </span>
            </div>

            <div className="tech-rows">
              <div>
                <span>MACD line</span>
                <strong>{snapshot.macd?.toFixed(2)}</strong>
              </div>
              <div>
                <span>Signal line</span>
                <strong>
                  {snapshot.macd_signal?.toFixed(2)}
                </strong>
              </div>
            </div>
          </>
        ) : (
          <>
            <div className="tech-headline">
              <strong>—</strong>
            </div>
            <NeedsData
              snapshot={snapshot}
              name="MACD 12/26/9"
            />
          </>
        )}

      </div>


      <div className="tech-card">

        <div className="section-label">VOLATILITY</div>

        <h3>Bollinger Bands (20, 2)</h3>

        {percentB != null ? (
          <>
            <div className="tech-headline">
              <strong>{(percentB * 100).toFixed(0)}%</strong>
              <span>
                {percentB > 1
                  ? "Above upper band"
                  : percentB < 0
                    ? "Below lower band"
                    : "Position within band"}
              </span>
            </div>

            <div className="tech-rows">
              <div>
                <span>Upper</span>
                <strong>
                  {formatPrice(snapshot.bollinger_upper)}
                </strong>
              </div>
              <div>
                <span>Middle (SMA 20)</span>
                <strong>
                  {formatPrice(snapshot.bollinger_middle)}
                </strong>
              </div>
              <div>
                <span>Lower</span>
                <strong>
                  {formatPrice(snapshot.bollinger_lower)}
                </strong>
              </div>
            </div>
          </>
        ) : (
          <NeedsData
            snapshot={snapshot}
            name="SMA 20 / Bollinger"
          />
        )}

      </div>


      <div className="tech-card tech-card-wide">

        <div className="section-label">MOVING AVERAGES</div>

        <div className="tech-table-wrap">
          <table className="tech-table">
            <thead>
              <tr>
                <th>Period</th>
                <th>SMA</th>
                <th>EMA</th>
                <th>Price vs SMA</th>
              </tr>
            </thead>
            <tbody>
              {snapshot.moving_averages.map((ma) => (
                <tr key={ma.period}>
                  <td>{ma.period}-day</td>
                  <td>{formatPrice(ma.sma)}</td>
                  <td>{formatPrice(ma.ema)}</td>
                  <td>
                    {ma.price_above_sma == null ? (
                      <span className="muted">
                        Needs {ma.period} sessions
                      </span>
                    ) : (
                      <span
                        className={
                          ma.price_above_sma
                            ? "positive"
                            : "negative"
                        }
                      >
                        {ma.price_above_sma
                          ? "▲ Above"
                          : "▼ Below"}{" "}
                        {lastClose != null && ma.sma
                          ? formatPercent(
                              lastClose / ma.sma - 1
                            )
                          : ""}
                      </span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

      </div>


      <div className="tech-card">

        <div className="section-label">RETURNS &amp; RISK</div>

        <div className="tech-rows">
          {Object.entries(snapshot.returns).map(
            ([label, value]) => (
              <div key={label}>
                <span>{label} return</span>
                <strong className={trendClass(value)}>
                  {formatPercent(value)}
                </strong>
              </div>
            )
          )}
          <div>
            <span>Volatility (ann.)</span>
            <strong>
              {formatPercent(snapshot.volatility, false)}
            </strong>
          </div>
        </div>

      </div>


      <div className="tech-card tech-card-full">

        <div className="section-label">DATA COVERAGE</div>

        <p className="coverage-text">
          {snapshot.sessions} trading sessions stored,{" "}
          {formatDate(snapshot.first_date)} to{" "}
          {formatDate(snapshot.as_of)}.
          {missing.length > 0 &&
            ` ${missing
              .map((m) => m.name)
              .join(", ")} will appear once more history is loaded (run the NSE backfill).`}
        </p>

        <div className="coverage-chips">
          {snapshot.availability.map((a) => (
            <span
              key={a.name}
              className={
                a.available ? "chip ready" : "chip"
              }
            >
              {a.available ? "●" : "○"} {a.name}
            </span>
          ))}
        </div>

      </div>

    </div>
  );
}


export default TechnicalsPanel;
