import React, { useEffect, useState, useRef, useCallback } from "react";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler,
} from "chart.js";
import { Line } from "react-chartjs-2";
import axios from "axios";

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler,
);

const API = process.env.REACT_APP_API_URL || "http://localhost:8000";

// ─── Styles ───────────────────────────────────────────────────────────────────
const S = {
  root: {
    minHeight: "100vh",
    background: "#080c14",
    color: "#c9d1d9",
    fontFamily: "'DM Mono', 'Courier New', monospace",
    padding: 0,
    margin: 0,
  },
  header: {
    background: "linear-gradient(180deg, #0d1117 0%, #080c14 100%)",
    borderBottom: "1px solid #1c2a3a",
    padding: "16px 32px",
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    position: "sticky",
    top: 0,
    zIndex: 100,
  },
  logo: {
    fontSize: "20px",
    fontWeight: "700",
    color: "#e6b450",
    letterSpacing: "2px",
    fontFamily: "'Sora', sans-serif",
  },
  badge: {
    background: "#1c2a3a",
    border: "1px solid #2a3f55",
    borderRadius: "4px",
    padding: "3px 10px",
    fontSize: "11px",
    color: "#7d9ab5",
    letterSpacing: "1px",
  },
  clock: { fontSize: "13px", color: "#7d9ab5", letterSpacing: "1px" },
  refreshBtn: {
    background: "transparent",
    border: "1px solid #2a3f55",
    borderRadius: "4px",
    color: "#7d9ab5",
    padding: "6px 14px",
    fontSize: "12px",
    cursor: "pointer",
    letterSpacing: "1px",
    transition: "all 0.2s",
  },
  main: { padding: "24px 32px", maxWidth: "1600px", margin: "0 auto" },
  sectionLabel: {
    fontSize: "10px",
    letterSpacing: "3px",
    color: "#4a6278",
    textTransform: "uppercase",
    marginBottom: "12px",
    marginTop: "28px",
  },
  kpiGrid: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
    gap: "12px",
    marginBottom: "8px",
  },
  kpiCard: {
    background: "#0d1117",
    border: "1px solid #1c2a3a",
    borderRadius: "8px",
    padding: "20px",
    position: "relative",
    overflow: "hidden",
  },
  kpiLabel: {
    fontSize: "10px",
    letterSpacing: "2px",
    color: "#4a6278",
    textTransform: "uppercase",
    marginBottom: "8px",
  },
  kpiValue: {
    fontSize: "26px",
    fontWeight: "700",
    color: "#e6edf3",
    letterSpacing: "-0.5px",
    lineHeight: 1,
  },
  kpiSub: { fontSize: "12px", marginTop: "6px", color: "#7d9ab5" },
  kpiAccent: {
    position: "absolute",
    bottom: 0,
    left: 0,
    right: 0,
    height: "2px",
  },
  chartsRow: { display: "grid", gridTemplateColumns: "2fr 1fr", gap: "12px" },
  card: {
    background: "#0d1117",
    border: "1px solid #1c2a3a",
    borderRadius: "8px",
    padding: "20px",
  },
  cardTitle: {
    fontSize: "11px",
    letterSpacing: "2px",
    color: "#7d9ab5",
    textTransform: "uppercase",
    marginBottom: "16px",
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
  },
  tabBtn: {
    background: "transparent",
    border: "1px solid #2a3f55",
    borderRadius: "4px",
    color: "#7d9ab5",
    padding: "5px 12px",
    fontSize: "11px",
    cursor: "pointer",
    marginLeft: "6px",
    transition: "all 0.15s",
    letterSpacing: "1px",
  },
  tabBtnActive: {
    background: "#1c2a3a",
    border: "1px solid #e6b450",
    color: "#e6b450",
  },
  symbolBtn: {
    background: "transparent",
    border: "1px solid #2a3f55",
    borderRadius: "4px",
    color: "#7d9ab5",
    padding: "4px 10px",
    fontSize: "11px",
    cursor: "pointer",
    marginLeft: "6px",
    transition: "all 0.15s",
  },
  symbolBtnActive: {
    background: "#1c2a3a",
    border: "1px solid #e6b450",
    color: "#e6b450",
  },
  table: { width: "100%", borderCollapse: "collapse", fontSize: "13px" },
  th: {
    textAlign: "left",
    padding: "8px 12px",
    fontSize: "10px",
    letterSpacing: "2px",
    color: "#4a6278",
    textTransform: "uppercase",
    borderBottom: "1px solid #1c2a3a",
  },
  td: {
    padding: "10px 12px",
    borderBottom: "1px solid #0d1520",
    color: "#c9d1d9",
  },
  bottomRow: { display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px" },
  aiBox: {
    background: "#0d1117",
    border: "1px solid #1c2a3a",
    borderRadius: "8px",
    padding: "20px",
  },
  aiText: {
    fontSize: "13px",
    lineHeight: "1.8",
    color: "#8b949e",
    marginBottom: "16px",
  },
  insightItem: {
    display: "flex",
    gap: "10px",
    marginBottom: "10px",
    alignItems: "flex-start",
  },
  insightDot: {
    width: "6px",
    height: "6px",
    borderRadius: "50%",
    background: "#e6b450",
    marginTop: "7px",
    flexShrink: 0,
  },
  loader: {
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    height: "120px",
    color: "#4a6278",
    fontSize: "12px",
    letterSpacing: "2px",
  },
  statusDot: {
    width: "8px",
    height: "8px",
    borderRadius: "50%",
    display: "inline-block",
    marginRight: "6px",
  },
};

// ─── Helpers ──────────────────────────────────────────────────────────────────
const fmt = (n, d = 2) =>
  n != null
    ? Number(n).toLocaleString("en-US", {
        minimumFractionDigits: d,
        maximumFractionDigits: d,
      })
    : "—";
const fmtPrice = (n) =>
  n != null
    ? "$" +
      Number(n).toLocaleString("en-US", {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
      })
    : "—";
const changeColor = (v) => {
  const n = parseFloat(v);
  if (n > 0) return "#3fb950";
  if (n < 0) return "#f85149";
  return "#7d9ab5";
};
const sentimentColor = (s) => {
  if (s === "Bullish") return { color: "#3fb950", bg: "#0f2a1a" };
  if (s === "Bearish") return { color: "#f85149", bg: "#2a0f0f" };
  return { color: "#e6b450", bg: "#2a1f0f" };
};
const warsawTime = (iso) =>
  new Date(iso).toLocaleString("pl-PL", {
    timeZone: "Europe/Warsaw",
    day: "2-digit",
    month: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });

// ─── Clock ────────────────────────────────────────────────────────────────────
function Clock() {
  const [time, setTime] = useState(new Date());
  useEffect(() => {
    const t = setInterval(() => setTime(new Date()), 1000);
    return () => clearInterval(t);
  }, []);
  return (
    <span style={S.clock}>
      {time.toLocaleTimeString("pl-PL", {
        timeZone: "Europe/Warsaw",
        hour12: false,
      })}{" "}
      <span style={{ color: "#4a6278" }}>WAW</span>
    </span>
  );
}

// ─── Skeleton Components ───────────────────────────────────────────────────────
function SkeletonKpiCard() {
  return (
    <div style={S.kpiCard}>
      <div style={{ ...S.kpiLabel, opacity: 0.3 }}>LOADING</div>
      <div
        style={{
          ...S.kpiValue,
          opacity: 0.3,
          backgroundColor: "#1c2a3a",
          borderRadius: "4px",
          width: "80%",
          height: "32px",
        }}
      >
        &nbsp;
      </div>
      <div
        style={{
          ...S.kpiSub,
          opacity: 0.3,
          backgroundColor: "#1c2a3a",
          borderRadius: "4px",
          width: "60%",
          height: "16px",
          marginTop: "8px",
        }}
      >
        &nbsp;
      </div>
      <div style={{ ...S.kpiAccent, background: "#2a3f55" }} />
    </div>
  );
}

function SkeletonChart() {
  return (
    <div style={S.card}>
      <div style={S.cardTitle}>
        <span
          style={{
            opacity: 0.3,
            backgroundColor: "#1c2a3a",
            width: "150px",
            height: "14px",
            display: "inline-block",
            borderRadius: "4px",
          }}
        >
          &nbsp;
        </span>
        <span
          style={{
            opacity: 0.3,
            backgroundColor: "#1c2a3a",
            width: "80px",
            height: "12px",
            display: "inline-block",
            borderRadius: "4px",
          }}
        >
          &nbsp;
        </span>
      </div>
      <div
        style={{
          height: "210px",
          background: "#0d1117",
          borderRadius: "8px",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        <div
          style={{
            width: "90%",
            height: "80%",
            background:
              "linear-gradient(90deg, #1c2a3a 25%, #2a3f55 50%, #1c2a3a 75%)",
            backgroundSize: "200% 100%",
            animation: "shimmer 1.5s infinite",
            borderRadius: "4px",
          }}
        />
      </div>
    </div>
  );
}

function SkeletonTable() {
  return (
    <div style={{ ...S.card, padding: "16px 0" }}>
      <div style={{ ...S.cardTitle, padding: "0 16px", marginBottom: "8px" }}>
        <span
          style={{
            opacity: 0.3,
            backgroundColor: "#1c2a3a",
            width: "120px",
            height: "14px",
            display: "inline-block",
            borderRadius: "4px",
          }}
        >
          &nbsp;
        </span>
      </div>
      {[1, 2, 3, 4, 5, 6].map((i) => (
        <div
          key={i}
          style={{
            padding: "10px 16px",
            borderBottom: "1px solid #0d1520",
            display: "flex",
            justifyContent: "space-between",
          }}
        >
          <span
            style={{
              opacity: 0.3,
              backgroundColor: "#1c2a3a",
              width: "60px",
              height: "16px",
              borderRadius: "4px",
            }}
          >
            &nbsp;
          </span>
          <span
            style={{
              opacity: 0.3,
              backgroundColor: "#1c2a3a",
              width: "80px",
              height: "16px",
              borderRadius: "4px",
            }}
          >
            &nbsp;
          </span>
          <span
            style={{
              opacity: 0.3,
              backgroundColor: "#1c2a3a",
              width: "50px",
              height: "16px",
              borderRadius: "4px",
            }}
          >
            &nbsp;
          </span>
        </div>
      ))}
    </div>
  );
}

function SkeletonAIPanel() {
  return (
    <div style={S.aiBox}>
      <div style={S.cardTitle}>
        <span
          style={{
            opacity: 0.3,
            backgroundColor: "#1c2a3a",
            width: "180px",
            height: "14px",
            display: "inline-block",
            borderRadius: "4px",
          }}
        >
          &nbsp;
        </span>
        <span
          style={{
            opacity: 0.3,
            backgroundColor: "#1c2a3a",
            width: "100px",
            height: "12px",
            display: "inline-block",
            borderRadius: "4px",
          }}
        >
          &nbsp;
        </span>
      </div>
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "1fr 1fr 1fr",
          gap: "20px",
        }}
      >
        {[1, 2, 3].map((i) => (
          <div key={i}>
            <div
              style={{
                opacity: 0.3,
                backgroundColor: "#1c2a3a",
                width: "80px",
                height: "12px",
                marginBottom: "12px",
                borderRadius: "4px",
              }}
            >
              &nbsp;
            </div>
            {[1, 2, 3].map((j) => (
              <div
                key={j}
                style={{ display: "flex", gap: "10px", marginBottom: "10px" }}
              >
                <div
                  style={{
                    width: "6px",
                    height: "6px",
                    background: "#2a3f55",
                    borderRadius: "50%",
                  }}
                />
                <div
                  style={{
                    opacity: 0.3,
                    backgroundColor: "#1c2a3a",
                    width: "90%",
                    height: "40px",
                    borderRadius: "4px",
                  }}
                >
                  &nbsp;
                </div>
              </div>
            ))}
          </div>
        ))}
      </div>
    </div>
  );
}

// ─── KPI Card ─────────────────────────────────────────────────────────────────
function KpiCard({ label, value, sub, accentColor }) {
  return (
    <div style={S.kpiCard}>
      <div style={S.kpiLabel}>{label}</div>
      <div style={S.kpiValue}>{value}</div>
      {sub && <div style={S.kpiSub}>{sub}</div>}
      <div style={{ ...S.kpiAccent, background: accentColor || "#e6b450" }} />
    </div>
  );
}

// ─── SOURCE PANELS ────────────────────────────────────────────────────────────

// Binance panel — line chart
function BinancePanel({ trend, symbol, setSymbol }) {
  const chartRef = useRef(null);
  const chartValues = trend?.data?.map((d) => d.value) || [];
  const chartLabels =
    trend?.data?.map((d) =>
      new Date(d.timestamp).toLocaleTimeString("pl-PL", {
        hour: "2-digit",
        minute: "2-digit",
        timeZone: "Europe/Warsaw",
      }),
    ) || [];
  const chartColor =
    chartValues.length > 1
      ? chartValues[chartValues.length - 1] >= chartValues[0]
        ? "#3fb950"
        : "#f85149"
      : "#e6b450";

  const chartData = {
    labels: chartLabels,
    datasets: [
      {
        label: symbol,
        data: chartValues,
        borderColor: chartColor,
        backgroundColor: chartColor + "18",
        borderWidth: 2,
        pointRadius: 0,
        pointHoverRadius: 4,
        fill: true,
        tension: 0.4,
      },
    ],
  };
  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { display: false },
      tooltip: {
        backgroundColor: "#0d1117",
        borderColor: "#2a3f55",
        borderWidth: 1,
        titleColor: "#7d9ab5",
        bodyColor: "#e6edf3",
        callbacks: { label: (ctx) => " $" + fmt(ctx.parsed.y) },
      },
    },
    scales: {
      x: {
        grid: { color: "#0d1520" },
        ticks: {
          color: "#4a6278",
          font: { size: 10, family: "DM Mono" },
          maxTicksLimit: 8,
        },
      },
      y: {
        grid: { color: "#0d1520" },
        ticks: {
          color: "#4a6278",
          font: { size: 10, family: "DM Mono" },
          callback: (v) => "$" + v.toLocaleString(),
        },
      },
    },
  };

  return (
    <>
      {/* Symbol switcher */}
      <div
        style={{
          marginBottom: "12px",
          display: "flex",
          gap: "6px",
          flexWrap: "wrap",
        }}
      >
        {["BTC", "ETH", "BNB", "SOL", "XRP", "DOGE", "ADA"].map((s) => (
          <button
            key={s}
            style={{
              ...S.symbolBtn,
              ...(symbol === s ? S.symbolBtnActive : {}),
            }}
            onClick={() => setSymbol(s)}
          >
            {s}
          </button>
        ))}
      </div>
      {/* AI trend note */}
      {trend?.ai_analysis && (
        <div
          style={{
            fontSize: "11px",
            color: "#4a6278",
            marginBottom: "12px",
            padding: "8px 12px",
            background: "#080c14",
            borderRadius: "4px",
            borderLeft: `2px solid ${chartColor}`,
            lineHeight: "1.6",
          }}
        >
          🤖 {trend.ai_analysis}
        </div>
      )}
      {/* Chart */}
      <div style={{ height: "210px" }}>
        {chartValues.length > 0 ? (
          <Line ref={chartRef} data={chartData} options={chartOptions} />
        ) : (
          <div style={S.loader}>NO DATA YET — COLLECTING...</div>
        )}
      </div>
    </>
  );
}

// OpenMeteo panel — weather data visualization
function WeatherPanel({ weather }) {
  if (!weather)
    return (
      <div style={S.loader}>NO WEATHER DATA — configure OpenMeteo in n8n</div>
    );

  const temp = parseFloat(weather.temperature);
  const humidity = parseInt(weather.humidity);
  // Temp color scale: cold=blue, mild=green, hot=red
  const tempColor = temp < 5 ? "#58a6ff" : temp < 20 ? "#3fb950" : "#f85149";
  // Gauge bar width (scale -20 to 40 degrees)
  const tempPct = Math.min(100, Math.max(0, ((temp + 20) / 60) * 100));
  const humidityPct = Math.min(100, Math.max(0, humidity));

  return (
    <div style={{ padding: "8px 0" }}>
      {/* City + condition */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "flex-start",
          marginBottom: "24px",
        }}
      >
        <div>
          <div
            style={{
              fontSize: "32px",
              fontWeight: "700",
              color: tempColor,
              letterSpacing: "-1px",
              lineHeight: 1,
            }}
          >
            {fmt(temp, 1)}°C
          </div>
          <div
            style={{
              fontSize: "13px",
              color: "#7d9ab5",
              marginTop: "6px",
              textTransform: "capitalize",
            }}
          >
            {weather.weather_condition}
          </div>
        </div>
        <div style={{ textAlign: "right" }}>
          <div
            style={{
              fontSize: "10px",
              letterSpacing: "2px",
              color: "#4a6278",
              marginBottom: "4px",
            }}
          >
            LOCATION
          </div>
          <div
            style={{ fontSize: "16px", color: "#e6edf3", fontWeight: "600" }}
          >
            {weather.city}
          </div>
          <div style={{ fontSize: "11px", color: "#4a6278", marginTop: "4px" }}>
            Warsaw, PL
          </div>
        </div>
      </div>

      {/* Temperature gauge */}
      <div style={{ marginBottom: "20px" }}>
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            fontSize: "10px",
            color: "#4a6278",
            letterSpacing: "2px",
            marginBottom: "6px",
          }}
        >
          <span>TEMPERATURE</span>
          <span style={{ color: tempColor }}>{fmt(temp, 1)}°C</span>
        </div>
        <div
          style={{
            background: "#1c2a3a",
            borderRadius: "2px",
            height: "4px",
            overflow: "hidden",
          }}
        >
          <div
            style={{
              width: `${tempPct}%`,
              height: "100%",
              background: `linear-gradient(90deg, #58a6ff, ${tempColor})`,
              borderRadius: "2px",
              transition: "width 0.8s ease",
            }}
          />
        </div>
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            fontSize: "9px",
            color: "#4a6278",
            marginTop: "4px",
          }}
        >
          <span>−20°C</span>
          <span>+40°C</span>
        </div>
      </div>

      {/* Humidity gauge */}
      <div style={{ marginBottom: "20px" }}>
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            fontSize: "10px",
            color: "#4a6278",
            letterSpacing: "2px",
            marginBottom: "6px",
          }}
        >
          <span>HUMIDITY</span>
          <span style={{ color: "#58a6ff" }}>{humidity}%</span>
        </div>
        <div
          style={{
            background: "#1c2a3a",
            borderRadius: "2px",
            height: "4px",
            overflow: "hidden",
          }}
        >
          <div
            style={{
              width: `${humidityPct}%`,
              height: "100%",
              background: "linear-gradient(90deg, #1c2a3a, #58a6ff)",
              borderRadius: "2px",
              transition: "width 0.8s ease",
            }}
          />
        </div>
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            fontSize: "9px",
            color: "#4a6278",
            marginTop: "4px",
          }}
        >
          <span>0%</span>
          <span>100%</span>
        </div>
      </div>

      {/* Stats row */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "1fr 1fr 1fr",
          gap: "12px",
          marginTop: "16px",
        }}
      >
        {[
          { label: "FEELS LIKE", value: `${fmt(temp - 2, 1)}°C` },
          { label: "HUMIDITY", value: `${humidity}%` },
          {
            label: "CONDITIONS",
            value: weather.weather_condition?.split(" ")[0] || "—",
          },
        ].map(({ label, value }) => (
          <div
            key={label}
            style={{
              background: "#080c14",
              border: "1px solid #1c2a3a",
              borderRadius: "6px",
              padding: "12px",
              textAlign: "center",
            }}
          >
            <div
              style={{
                fontSize: "9px",
                letterSpacing: "1px",
                color: "#4a6278",
                marginBottom: "6px",
              }}
            >
              {label}
            </div>
            <div
              style={{ fontSize: "14px", fontWeight: "600", color: "#e6edf3" }}
            >
              {value}
            </div>
          </div>
        ))}
      </div>

      <div
        style={{
          marginTop: "16px",
          fontSize: "10px",
          color: "#4a6278",
          letterSpacing: "1px",
        }}
      >
        ⟳ Updated via OpenMeteo · Warsaw monitoring station
      </div>
    </div>
  );
}

// BBC News panel — news feed as data visualization
function NewsPanel({ news }) {
  if (!news || news.length === 0)
    return <div style={S.loader}>NO NEWS — configure BBC News in n8n</div>;

  // Assign a simple sentiment color based on keywords in title
  const getSentimentFromTitle = (title) => {
    const t = (title || "").toLowerCase();
    const positive = [
      "rise",
      "gain",
      "rally",
      "surge",
      "growth",
      "bullish",
      "record",
      "high",
      "up",
      "profit",
    ];
    const negative = [
      "fall",
      "drop",
      "crash",
      "loss",
      "fear",
      "bearish",
      "low",
      "decline",
      "debt",
      "crisis",
    ];
    if (positive.some((w) => t.includes(w)))
      return { label: "POS", color: "#3fb950", bg: "#0f2a1a" };
    if (negative.some((w) => t.includes(w)))
      return { label: "NEG", color: "#f85149", bg: "#2a0f0f" };
    return { label: "NEU", color: "#e6b450", bg: "#2a1f0f" };
  };

  return (
    <div style={{ overflowY: "auto", maxHeight: "340px", paddingRight: "4px" }}>
      <div
        style={{
          fontSize: "10px",
          color: "#4a6278",
          letterSpacing: "2px",
          marginBottom: "12px",
        }}
      >
        {news.length} ARTICLES · BUSINESS HEADLINES · AUTO SENTIMENT
      </div>
      {news.map((n, i) => {
        const sent = getSentimentFromTitle(n.title);
        return (
          <div
            key={i}
            style={{
              padding: "12px 0",
              borderBottom: "1px solid #0d1520",
              display: "flex",
              gap: "12px",
              alignItems: "flex-start",
            }}
          >
            {/* Index */}
            <div
              style={{
                fontSize: "10px",
                color: "#4a6278",
                minWidth: "20px",
                paddingTop: "2px",
              }}
            >
              {String(i + 1).padStart(2, "0")}
            </div>
            {/* Content */}
            <div style={{ flex: 1 }}>
              <div
                style={{
                  fontSize: "13px",
                  lineHeight: "1.5",
                  marginBottom: "6px",
                }}
              >
                <a
                  href={n.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  style={{
                    color: "#c9d1d9",
                    textDecoration: "none",
                    borderBottom: "1px dotted #4a6278",
                  }}
                  onMouseEnter={(e) => (e.target.style.color = "#e6b450")}
                  onMouseLeave={(e) => (e.target.style.color = "#c9d1d9")}
                >
                  {n.title}
                </a>
              </div>
              <div
                style={{ display: "flex", gap: "10px", alignItems: "center" }}
              >
                <span style={{ fontSize: "10px", color: "#58a6ff" }}>
                  {n.source}
                </span>
                {n.published_at && (
                  <span style={{ fontSize: "10px", color: "#4a6278" }}>
                    {warsawTime(n.published_at)}
                  </span>
                )}
                <span
                  style={{
                    fontSize: "10px",
                    fontWeight: "700",
                    color: sent.color,
                    background: sent.bg,
                    padding: "1px 6px",
                    borderRadius: "3px",
                    letterSpacing: "1px",
                  }}
                >
                  {sent.label}
                </span>
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}

// ─── Source switcher KPI card ─────────────────────────────────────────────────
function SourceSwitcherCard({ activeSource, setActiveSource }) {
  const sources = [
    {
      id: "binance",
      label: "BINANCE",
      color: "#e6b450",
      desc: "Crypto prices",
    },
    { id: "weather", label: "WEATHER", color: "#58a6ff", desc: "OpenMeteo" },
    { id: "news", label: "NEWS", color: "#3fb950", desc: "BBC News" },
  ];
  const active = sources.find((s) => s.id === activeSource);

  return (
    <div style={{ ...S.kpiCard, cursor: "default" }}>
      <div style={S.kpiLabel}>Data Sources</div>
      <div style={{ display: "flex", gap: "6px", marginBottom: "8px" }}>
        {sources.map((s) => (
          <button
            key={s.id}
            onClick={() => setActiveSource(s.id)}
            style={{
              background:
                activeSource === s.id ? s.color + "22" : "transparent",
              border: `1px solid ${activeSource === s.id ? s.color : "#2a3f55"}`,
              borderRadius: "4px",
              color: activeSource === s.id ? s.color : "#7d9ab5",
              padding: "4px 10px",
              fontSize: "10px",
              cursor: "pointer",
              letterSpacing: "1px",
              fontFamily: "'DM Mono', monospace",
              fontWeight: activeSource === s.id ? "700" : "400",
              transition: "all 0.15s",
            }}
          >
            {s.label}
          </button>
        ))}
      </div>
      <div style={{ fontSize: "11px", color: "#7d9ab5" }}>
        Viewing: <span style={{ color: active?.color }}>{active?.desc}</span>
      </div>
      <div style={{ ...S.kpiAccent, background: active?.color }} />
    </div>
  );
}

// ─── Main App ─────────────────────────────────────────────────────────────────
export default function App() {
  const [overview, setOverview] = useState(null);
  const [trend, setTrend] = useState(null);
  const [aiSummary, setAiSummary] = useState(null);
  const [symbol, setSymbol] = useState("BTC");
  const [activeSource, setActiveSource] = useState("binance");
  const [loadingCrypto, setLoadingCrypto] = useState(true);
  const [loadingNews, setLoadingNews] = useState(true);
  const [loadingWeather, setLoadingWeather] = useState(true);
  const [aiLoading, setAiLoading] = useState(false);
  const [lastUpdate, setLastUpdate] = useState(null);

  const fetchOverview = useCallback(async () => {
    try {
      const r = await axios.get(`${API}/api/dashboard/overview`);
      setOverview(r.data);
      setLastUpdate(new Date());

      // Ustaw stany ładowania dla poszczególnych sekcji na podstawie otrzymanych danych
      if (r.data.crypto?.prices?.length > 0) setLoadingCrypto(false);
      if (r.data.news?.length > 0) setLoadingNews(false);
      if (r.data.weather) setLoadingWeather(false);
    } catch (e) {
      console.error(e);
      // W przypadku błędu i tak wyłącz ładowanie po pewnym czasie
      setTimeout(() => {
        setLoadingCrypto(false);
        setLoadingNews(false);
        setLoadingWeather(false);
      }, 5000);
    }
  }, []);

  const fetchTrend = useCallback(async (sym) => {
    try {
      const r = await axios.get(
        `${API}/api/charts/crypto-trend?symbol=${sym}&days=1`,
      );
      setTrend(r.data);
    } catch (e) {
      console.error(e);
    }
  }, []);

  const fetchAI = useCallback(async () => {
    setAiLoading(true);
    try {
      const r = await axios.get(`${API}/api/ai/daily-summary`);
      setAiSummary(r.data);
    } catch (e) {
      console.error(e);
    } finally {
      setAiLoading(false);
    }
  }, []);

  useEffect(() => {
    Promise.all([fetchOverview(), fetchTrend(symbol), fetchAI()]);
  }, []);

  useEffect(() => {
    const t = setInterval(() => {
      fetchOverview();
      fetchTrend(symbol);
    }, 60000);
    return () => clearInterval(t);
  }, [fetchOverview, fetchTrend, symbol]);
  useEffect(() => {
    fetchTrend(symbol);
  }, [symbol, fetchTrend]);

  const prices = overview?.crypto?.prices || [];
  const sentiment = overview?.crypto?.market_sentiment || "Neutral";
  const sentColor = sentimentColor(sentiment);
  const btc = prices.find((p) => p.symbol === "BTC");
  const eth = prices.find((p) => p.symbol === "ETH");
  const weather = overview?.weather;
  const news = overview?.news || [];

  // Panel title and subtitle per source
  const panelMeta = {
    binance: { title: `${symbol}/USD · 24H CHART`, sub: "Binance Public API" },
    weather: {
      title: "WEATHER · WARSAW MONITORING",
      sub: "OpenMeteo",
    },
    news: {
      title: "MARKET NEWS FEED · AUTO SENTIMENT",
      sub: "BBC News",
    },
  };
  const meta = panelMeta[activeSource];

  return (
    <>
      <link
        href="https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Sora:wght@600;700&display=swap"
        rel="stylesheet"
      />
      <style
        dangerouslySetInnerHTML={{
          __html: `
    @keyframes shimmer {
      0% { background-position: -200% 0; }
      100% { background-position: 200% 0; }
    }
  `,
        }}
      />
      <div style={S.root}>
        {/* ── Header ── */}
        <header style={S.header}>
          <div style={{ display: "flex", alignItems: "center", gap: "16px" }}>
            <div style={S.logo}>BI TERMINAL</div>
            <span style={S.badge}>LIVE</span>
            <span
              style={{
                ...sentColor,
                padding: "2px 10px",
                borderRadius: "4px",
                fontSize: "11px",
                fontWeight: "700",
                letterSpacing: "1px",
                background: sentColor.bg,
                color: sentColor.color,
              }}
            >
              {sentiment.toUpperCase()}
            </span>
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: "16px" }}>
            {lastUpdate && (
              <span style={{ ...S.clock, fontSize: "11px" }}>
                Updated{" "}
                {lastUpdate.toLocaleTimeString("pl-PL", {
                  timeZone: "Europe/Warsaw",
                  hour12: false,
                })}
              </span>
            )}
            <Clock />
            <button
              style={S.refreshBtn}
              onClick={() => {
                fetchOverview();
                fetchTrend(symbol);
              }}
              onMouseEnter={(e) => {
                e.target.style.color = "#e6b450";
                e.target.style.borderColor = "#e6b450";
              }}
              onMouseLeave={(e) => {
                e.target.style.color = "#7d9ab5";
                e.target.style.borderColor = "#2a3f55";
              }}
            >
              ↻ REFRESH
            </button>
          </div>
        </header>

        <main style={S.main}>
          {/* ── KPI Row ── */}
          <div style={S.sectionLabel}>Market Overview</div>
          <div style={S.kpiGrid}>
            {loadingCrypto ? (
              <>
                <SkeletonKpiCard />
                <SkeletonKpiCard />
                <SkeletonKpiCard />
                <SkeletonKpiCard />
                <SkeletonKpiCard />
              </>
            ) : (
              <>
                <KpiCard
                  label="Bitcoin (BTC)"
                  value={fmtPrice(btc?.price_usd)}
                  sub={
                    btc ? (
                      <span
                        style={{ color: changeColor(btc.price_change_24h) }}
                      >
                        {btc.price_change_24h > 0 ? "▲" : "▼"}{" "}
                        {fmt(Math.abs(btc.price_change_24h))}% (24h)
                      </span>
                    ) : null
                  }
                  accentColor={
                    btc?.price_change_24h >= 0 ? "#3fb950" : "#f85149"
                  }
                />
                <KpiCard
                  label="Ethereum (ETH)"
                  value={fmtPrice(eth?.price_usd)}
                  sub={
                    eth ? (
                      <span
                        style={{ color: changeColor(eth.price_change_24h) }}
                      >
                        {eth.price_change_24h > 0 ? "▲" : "▼"}{" "}
                        {fmt(Math.abs(eth.price_change_24h))}% (24h)
                      </span>
                    ) : null
                  }
                  accentColor={
                    eth?.price_change_24h >= 0 ? "#3fb950" : "#f85149"
                  }
                />
                <KpiCard
                  label="Market Sentiment"
                  value={sentiment}
                  sub={`${prices.length} assets tracked`}
                  accentColor={sentColor.color}
                />
                {weather ? (
                  <KpiCard
                    label={`Weather · ${weather.city}`}
                    value={`${fmt(weather.temperature, 1)}°C`}
                    sub={weather.weather_condition}
                    accentColor="#58a6ff"
                  />
                ) : loadingWeather ? (
                  <SkeletonKpiCard />
                ) : null}
                <SourceSwitcherCard
                  activeSource={activeSource}
                  setActiveSource={setActiveSource}
                />
              </>
            )}
          </div>

          {/* ── Main panel + Table ── */}
          <div style={S.sectionLabel}>
            {activeSource === "binance"
              ? "Price Chart & Top Assets"
              : activeSource === "weather"
                ? "Weather Data & Top Assets"
                : "News Feed & Top Assets"}
          </div>
          <div style={S.chartsRow}>
            {/* Left: dynamic source panel */}
            {(activeSource === "binance" && loadingCrypto) ||
            (activeSource === "weather" && loadingWeather) ||
            (activeSource === "news" && loadingNews) ? (
              <SkeletonChart />
            ) : (
              <div style={S.card}>
                <div style={S.cardTitle}>
                  <span>{meta.title}</span>
                  <span
                    style={{
                      fontSize: "10px",
                      color: "#4a6278",
                      letterSpacing: "1px",
                    }}
                  >
                    {meta.sub}
                  </span>
                </div>
                {activeSource === "binance" && (
                  <BinancePanel
                    trend={trend}
                    symbol={symbol}
                    setSymbol={setSymbol}
                  />
                )}
                {activeSource === "weather" && (
                  <WeatherPanel weather={weather} />
                )}
                {activeSource === "news" && <NewsPanel news={news} />}
              </div>
            )}

            {/* Right: Top 10 table — always visible */}
            {loadingCrypto ? (
              <SkeletonTable />
            ) : (
              <div
                style={{
                  ...S.card,
                  padding: "16px 0",
                  overflowY: "auto",
                  maxHeight: "420px",
                }}
              >
                <div
                  style={{
                    ...S.cardTitle,
                    padding: "0 16px",
                    marginBottom: "8px",
                  }}
                >
                  Top Assets
                </div>
                <table style={S.table}>
                  <thead>
                    <tr>
                      <th style={S.th}>Symbol</th>
                      <th style={{ ...S.th, textAlign: "right" }}>Price</th>
                      <th style={{ ...S.th, textAlign: "right" }}>24h %</th>
                    </tr>
                  </thead>
                  <tbody>
                    {prices.map((p, i) => (
                      <tr
                        key={p.symbol}
                        style={{ cursor: "pointer" }}
                        onClick={() => {
                          setSymbol(p.symbol);
                          setActiveSource("binance");
                        }}
                        onMouseEnter={(e) =>
                          (e.currentTarget.style.background = "#0d1520")
                        }
                        onMouseLeave={(e) =>
                          (e.currentTarget.style.background = "transparent")
                        }
                      >
                        <td style={S.td}>
                          <span
                            style={{
                              color: "#4a6278",
                              fontSize: "10px",
                              marginRight: "8px",
                            }}
                          >
                            {String(i + 1).padStart(2, "0")}
                          </span>
                          <span style={{ color: "#e6edf3", fontWeight: "500" }}>
                            {p.symbol}
                          </span>
                        </td>
                        <td style={{ ...S.td, textAlign: "right" }}>
                          {fmtPrice(p.price_usd)}
                        </td>
                        <td
                          style={{
                            ...S.td,
                            textAlign: "right",
                            color: changeColor(p.price_change_24h),
                            fontWeight: "600",
                          }}
                        >
                          {p.price_change_24h > 0 ? "+" : ""}
                          {fmt(p.price_change_24h)}%
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                <div
                  style={{
                    padding: "12px 16px",
                    fontSize: "10px",
                    color: "#4a6278",
                    letterSpacing: "1px",
                  }}
                >
                  ↑ Click any row to view chart
                </div>
              </div>
            )}
          </div>

          {/* ── AI Insights ── */}
          <div style={S.sectionLabel}>AI Intelligence · Llama 3.3 via Groq</div>
          {aiLoading ? (
            <SkeletonAIPanel />
          ) : aiSummary ? (
            <div style={S.aiBox}>
              <div style={S.cardTitle}>
                <span>Daily Market Briefing</span>
                <button
                  style={S.symbolBtn}
                  onClick={fetchAI}
                  disabled={aiLoading}
                  onMouseEnter={(e) => {
                    e.target.style.color = "#e6b450";
                    e.target.style.borderColor = "#e6b450";
                  }}
                  onMouseLeave={(e) => {
                    e.target.style.color = "#7d9ab5";
                    e.target.style.borderColor = "#2a3f55";
                  }}
                >
                  {aiLoading ? "GENERATING..." : "↻ REGENERATE"}
                </button>
              </div>
              <div
                style={{
                  display: "grid",
                  gridTemplateColumns: "1fr 1fr 1fr",
                  gap: "20px",
                }}
              >
                {/* Summary */}
                <div>
                  <div
                    style={{
                      fontSize: "10px",
                      letterSpacing: "2px",
                      color: "#4a6278",
                      marginBottom: "10px",
                    }}
                  >
                    SUMMARY
                  </div>
                  <p style={{ ...S.aiText, marginBottom: 0 }}>
                    {aiSummary.summary}
                  </p>
                </div>
                {/* Insights */}
                <div>
                  <div
                    style={{
                      fontSize: "10px",
                      letterSpacing: "2px",
                      color: "#4a6278",
                      marginBottom: "10px",
                    }}
                  >
                    KEY INSIGHTS
                  </div>
                  {aiSummary.insights?.map((ins, i) => (
                    <div key={i} style={S.insightItem}>
                      <div style={S.insightDot} />
                      <span
                        style={{
                          fontSize: "12px",
                          color: "#8b949e",
                          lineHeight: "1.6",
                        }}
                      >
                        {ins}
                      </span>
                    </div>
                  ))}
                </div>
                {/* Recommendations */}
                <div>
                  <div
                    style={{
                      fontSize: "10px",
                      letterSpacing: "2px",
                      color: "#4a6278",
                      marginBottom: "10px",
                    }}
                  >
                    RECOMMENDATIONS
                  </div>
                  {aiSummary.recommendations?.map((rec, i) => (
                    <div key={i} style={S.insightItem}>
                      <div style={{ ...S.insightDot, background: "#58a6ff" }} />
                      <span
                        style={{
                          fontSize: "12px",
                          color: "#8b949e",
                          lineHeight: "1.6",
                        }}
                      >
                        {rec}
                      </span>
                    </div>
                  ))}
                  {aiSummary.generated_at && (
                    <div
                      style={{
                        marginTop: "16px",
                        fontSize: "10px",
                        color: "#4a6278",
                      }}
                    >
                      Generated {warsawTime(aiSummary.generated_at)}
                    </div>
                  )}
                </div>
              </div>
            </div>
          ) : (
            <div style={S.loader}>NO AI DATA</div>
          )}

          {/* ── Footer ── */}
          <div
            style={{
              marginTop: "32px",
              paddingTop: "16px",
              borderTop: "1px solid #1c2a3a",
              display: "flex",
              justifyContent: "space-between",
              fontSize: "10px",
              color: "#4a6278",
              letterSpacing: "1px",
            }}
          >
            <span>AI-POWERED BI DASHBOARD · TOMASZ SZOPA</span>
            <span>
              <span style={{ ...S.statusDot, background: "#3fb950" }} />
              FASTAPI · N8N · POSTGRESQL · GROQ/LLAMA 3.3
            </span>
          </div>
        </main>
      </div>
    </>
  );
}
