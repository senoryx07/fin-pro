export interface PricePoint {
  trade_date: string;
  open: number | null;
  high: number | null;
  low: number | null;
  close: number;
  volume: number | null;
  sma_20: number | null;
  bollinger_upper: number | null;
  bollinger_lower: number | null;
}

export interface PriceSeries {
  ticker: string;
  exchange: string;
  points: PricePoint[];
}

export interface MovingAverage {
  period: number;
  sma: number | null;
  ema: number | null;
  price_above_sma: boolean | null;
}

export interface IndicatorAvailability {
  name: string;
  required_sessions: number;
  available: boolean;
}

export interface TechnicalSnapshot {
  ticker: string;
  sessions: number;
  first_date: string | null;
  as_of: string | null;

  last_close: number | null;
  previous_close: number | null;
  change: number | null;
  change_percent: number | null;

  day_high: number | null;
  day_low: number | null;
  volume: number | null;

  period_high: number | null;
  period_low: number | null;
  average_volume_20: number | null;

  returns: Record<string, number | null>;
  volatility: number | null;

  rsi_14: number | null;
  macd: number | null;
  macd_signal: number | null;
  macd_histogram: number | null;

  bollinger_upper: number | null;
  bollinger_middle: number | null;
  bollinger_lower: number | null;

  moving_averages: MovingAverage[];
  availability: IndicatorAvailability[];
}
