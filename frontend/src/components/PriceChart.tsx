import { useEffect, useMemo, useRef, useState } from "react";
import type { PointerEvent } from "react";

import type { PricePoint } from "../types/market";
import {
  formatCompact,
  formatDate,
  formatPrice,
} from "../utils/format";


const RANGES = [
  { label: "1M", sessions: 21 },
  { label: "3M", sessions: 63 },
  { label: "6M", sessions: 126 },
  { label: "1Y", sessions: 252 },
  { label: "ALL", sessions: Infinity },
];

const HEIGHT = 300;
const VOLUME_HEIGHT = 52;
const PADDING = { top: 14, right: 64, bottom: 24, left: 8 };


interface PriceChartProps {
  points: PricePoint[];
}


function PriceChart({ points }: PriceChartProps) {
  const containerRef = useRef<HTMLDivElement>(null);

  const [width, setWidth] = useState(800);

  const [range, setRange] = useState("ALL");

  const [hoverIndex, setHoverIndex] =
    useState<number | null>(null);


  useEffect(() => {
    const element = containerRef.current;

    if (!element) {
      return;
    }

    const observer = new ResizeObserver(([entry]) => {
      setWidth(Math.max(280, entry.contentRect.width));
    });

    observer.observe(element);

    return () => observer.disconnect();
  }, []);


  const visible = useMemo(() => {
    const sessions =
      RANGES.find((r) => r.label === range)?.sessions ??
      Infinity;

    return Number.isFinite(sessions)
      ? points.slice(-sessions)
      : points;
  }, [points, range]);


  const geometry = useMemo(() => {
    const plotWidth =
      width - PADDING.left - PADDING.right;

    const priceBottom =
      HEIGHT - PADDING.bottom - VOLUME_HEIGHT - 10;

    const values = visible.flatMap((p) =>
      [
        p.low ?? p.close,
        p.high ?? p.close,
        p.bollinger_upper,
        p.bollinger_lower,
      ].filter((v): v is number => v != null)
    );

    let min = Math.min(...values);
    let max = Math.max(...values);

    if (min === max) {
      min -= 1;
      max += 1;
    }

    const margin = (max - min) * 0.06;
    min -= margin;
    max += margin;

    const maxVolume = Math.max(
      1,
      ...visible.map((p) => p.volume ?? 0)
    );

    const step =
      visible.length > 1
        ? plotWidth / (visible.length - 1)
        : 0;

    const x = (index: number) =>
      PADDING.left +
      (visible.length > 1 ? index * step : plotWidth / 2);

    const y = (value: number) =>
      PADDING.top +
      ((max - value) / (max - min)) *
        (priceBottom - PADDING.top);

    const line = (
      pick: (p: PricePoint) => number | null
    ) => {
      let path = "";
      let drawing = false;

      visible.forEach((p, index) => {
        const value = pick(p);

        if (value == null) {
          drawing = false;
          return;
        }

        path += `${drawing ? "L" : "M"}${x(index).toFixed(
          1
        )},${y(value).toFixed(1)}`;
        drawing = true;
      });

      return path;
    };

    const banded = visible
      .map((p, index) => ({ p, index }))
      .filter(
        ({ p }) =>
          p.bollinger_upper != null &&
          p.bollinger_lower != null
      );

    const band = banded.length
      ? [
          ...banded.map(
            ({ p, index }) =>
              `${x(index)},${y(p.bollinger_upper!)}`
          ),
          ...banded
            .reverse()
            .map(
              ({ p, index }) =>
                `${x(index)},${y(p.bollinger_lower!)}`
            ),
        ].join(" ")
      : "";

    const closePath = line((p) => p.close);

    const area = visible.length
      ? `${closePath}L${x(visible.length - 1)},${priceBottom}L${x(
          0
        )},${priceBottom}Z`
      : "";

    const ticks = Array.from({ length: 5 }, (_, i) =>
      min + ((max - min) * (i + 0.5)) / 5
    );

    const barWidth = Math.max(
      1,
      Math.min(10, step * 0.6 || 6)
    );

    return {
      x,
      y,
      step,
      plotWidth,
      priceBottom,
      maxVolume,
      ticks,
      band,
      area,
      closePath,
      smaPath: line((p) => p.sma_20),
      barWidth,
    };
  }, [visible, width]);


  if (!points.length) {
    return (
      <div className="chart-empty">
        No price history stored for this security yet.
      </div>
    );
  }


  const first = visible[0];
  const last = visible[visible.length - 1];
  const rising = last.close >= first.close;
  const tone = rising ? "#3ecf8e" : "#f0616d";

  const hovered =
    hoverIndex != null ? visible[hoverIndex] : null;

  const handlePointer = (
    event: PointerEvent<SVGRectElement>
  ) => {
    const bounds =
      event.currentTarget.getBoundingClientRect();

    const offset = event.clientX - bounds.left;

    const index =
      visible.length > 1
        ? Math.round(offset / geometry.step)
        : 0;

    setHoverIndex(
      Math.min(visible.length - 1, Math.max(0, index))
    );
  };

  const volumeTop =
    HEIGHT - PADDING.bottom - VOLUME_HEIGHT;

  const labelEvery = Math.max(
    1,
    Math.ceil(visible.length / Math.max(2, width / 110))
  );


  return (
    <div className="price-chart">

      <div className="chart-toolbar">

        <div className="chart-legend">
          <span>
            <i style={{ background: tone }} />
            Close
          </span>
          <span>
            <i className="legend-sma" />
            SMA 20
          </span>
          <span>
            <i className="legend-band" />
            Bollinger (20, 2)
          </span>
        </div>

        <div className="chart-ranges">
          {RANGES.map((r) => (
            <button
              key={r.label}
              className={
                r.label === range ? "active" : ""
              }
              onClick={() => setRange(r.label)}
            >
              {r.label}
            </button>
          ))}
        </div>

      </div>


      <div
        className="chart-canvas"
        ref={containerRef}
      >

        <svg
          width={width}
          height={HEIGHT}
          role="img"
          aria-label={`Price chart, ${visible.length} sessions`}
        >

          <defs>
            <linearGradient
              id="price-area"
              x1="0"
              x2="0"
              y1="0"
              y2="1"
            >
              <stop
                offset="0%"
                stopColor={tone}
                stopOpacity="0.22"
              />
              <stop
                offset="100%"
                stopColor={tone}
                stopOpacity="0"
              />
            </linearGradient>
          </defs>


          {geometry.ticks.map((tick) => (
            <g key={tick}>
              <line
                x1={PADDING.left}
                x2={width - PADDING.right}
                y1={geometry.y(tick)}
                y2={geometry.y(tick)}
                className="chart-grid"
              />
              <text
                x={width - PADDING.right + 8}
                y={geometry.y(tick) + 3}
                className="chart-axis"
              >
                {formatPrice(tick)}
              </text>
            </g>
          ))}


          {geometry.band && (
            <polygon
              points={geometry.band}
              className="chart-band"
            />
          )}

          <path
            d={geometry.area}
            fill="url(#price-area)"
          />

          <path
            d={geometry.smaPath}
            className="chart-sma"
          />

          <path
            // Re-keyed per range so the draw-in animation replays.
            key={`close-${range}`}
            className="chart-line-draw"
            pathLength={1}
            d={geometry.closePath}
            fill="none"
            stroke={tone}
            strokeWidth="1.6"
            strokeLinejoin="round"
          />


          {visible.map((p, index) => {
            const barHeight =
              ((p.volume ?? 0) / geometry.maxVolume) *
              VOLUME_HEIGHT;

            const up =
              index === 0 ||
              p.close >= visible[index - 1].close;

            return (
              <rect
                key={p.trade_date}
                x={geometry.x(index) - geometry.barWidth / 2}
                y={volumeTop + VOLUME_HEIGHT - barHeight}
                width={geometry.barWidth}
                height={barHeight}
                className={
                  up ? "volume-up" : "volume-down"
                }
              />
            );
          })}


          {visible.map((p, index) =>
            index % labelEvery === 0 ? (
              <text
                key={`label-${p.trade_date}`}
                x={geometry.x(index)}
                y={HEIGHT - 6}
                className="chart-axis"
                textAnchor={
                  index === 0 ? "start" : "middle"
                }
              >
                {new Date(
                  `${p.trade_date}T00:00:00`
                ).toLocaleDateString("en-IN", {
                  day: "2-digit",
                  month: "short",
                })}
              </text>
            ) : null
          )}


          {hovered && hoverIndex != null && (
            <g>
              <line
                x1={geometry.x(hoverIndex)}
                x2={geometry.x(hoverIndex)}
                y1={PADDING.top}
                y2={volumeTop + VOLUME_HEIGHT}
                className="chart-crosshair"
              />
              <circle
                cx={geometry.x(hoverIndex)}
                cy={geometry.y(hovered.close)}
                r="3.5"
                fill={tone}
                stroke="#0b0d10"
                strokeWidth="2"
              />
            </g>
          )}


          <rect
            x={PADDING.left}
            y={0}
            width={geometry.plotWidth}
            height={HEIGHT}
            fill="transparent"
            onPointerMove={handlePointer}
            onPointerDown={handlePointer}
            onPointerLeave={() => setHoverIndex(null)}
          />

        </svg>


        {hovered && hoverIndex != null && (
          <div
            className="chart-tooltip"
            style={{
              left: Math.min(
                width - 170,
                Math.max(0, geometry.x(hoverIndex) - 80)
              ),
            }}
          >
            <strong>
              {formatDate(hovered.trade_date)}
            </strong>
            <span>
              O {formatPrice(hovered.open)} · H{" "}
              {formatPrice(hovered.high)}
            </span>
            <span>
              L {formatPrice(hovered.low)} · C{" "}
              {formatPrice(hovered.close)}
            </span>
            <span>
              Vol {formatCompact(hovered.volume)}
            </span>
          </div>
        )}

      </div>

    </div>
  );
}


export default PriceChart;
