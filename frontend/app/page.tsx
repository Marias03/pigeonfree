"use client";

import dynamic from "next/dynamic";
import { useState, useRef, useEffect } from "react";
import { useTranslation } from "react-i18next";
import SplashScreen from "./components/SplashScreen";
import LanguageSwitcher from "./components/LanguageSwitcher";
import SearchPanel from "./components/SearchPanel";
import ReportButton from "./components/ReportButton";
import RouteAlert from "./components/RouteAlert";

const Map = dynamic<{ mapRef: React.RefObject<any> }>(
  () => import("./components/Map"),
  {
    ssr: false,
    loading: () => (
      <div
        style={{
          height: "100%",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          background: "#f8fafc",
        }}
      >
        <p style={{ color: "#64748b" }}>Cargando mapa...</p>
      </div>
    ),
  },
);

const ZONAS_LISTA = [
  { nombre: "Kremlin de Kazán", nivel: "alto" },
  { nombre: "Estación Central", nivel: "alto" },
  { nombre: "Plaza de la Libertad", nivel: "alto" },
  { nombre: "Bauman Street", nivel: "medio" },
  { nombre: "Mercado Central", nivel: "medio" },
];

const COLOR_NIVEL: Record<string, string> = {
  alto: "#ef4444",
  medio: "#f97316",
  bajo: "#22c55e",
};

const BG_NIVEL: Record<string, string> = {
  alto: "#fef2f2",
  medio: "#fff7ed",
  bajo: "#f0fdf4",
};

export default function Home() {
  const [showSplash, setShowSplash] = useState(true);
  const { t } = useTranslation("common");
  const mapRef = useRef<any>(null);
  const routingRef = useRef<any>(null);
  const [zonas, setZonas] = useState<any[]>([]);
  const [rutaActiva, setRutaActiva] = useState(false);
  const [routeWaypoints, setRouteWaypoints] = useState<
    { lat: number; lng: number }[]
  >([]);

  useEffect(() => {
    fetch("http://127.0.0.1:8000/zones")
      .then((r) => r.json())
      .then((d) => setZonas(d.zones || []))
      .catch(() => {});
  }, []);

  return (
    <main
      style={{
        height: "100dvh",
        width: "100vw",
        display: "flex",
        overflow: "hidden",
        minWidth: "320px",
      }}
    >
      {showSplash && <SplashScreen onFinish={() => setShowSplash(false)} />}

      <aside
        style={{
          width: "300px",
          flexShrink: 0,
          background: "white",
          borderRight: "1px solid #e2e8f0",
          display: "flex",
          flexDirection: "column",
          overflow: "hidden",
        }}
      >
        {/* Header */}
        <div
          style={{
            padding: "12px 16px",
            borderBottom: "1px solid #f1f5f9",
            display: "flex",
            alignItems: "center",
            gap: "8px",
            position: "relative",
            overflow: "hidden",
            minHeight: "52px",
            flexShrink: 0,
          }}
        >
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: "8px",
              flexShrink: 0,
              zIndex: 1,
            }}
          >
            <span style={{ fontSize: "18px" }}>🚫</span>
            <span
              style={{
                fontSize: "15px",
                fontWeight: 500,
                color: "#1e293b",
                whiteSpace: "nowrap",
              }}
            >
              {t("appName")}
            </span>
          </div>

          <div
            style={{
              flex: 1,
              position: "relative",
              overflow: "hidden",
              height: "52px",
              minWidth: 0,
            }}
          >
            <svg
              style={{
                position: "absolute",
                top: "50%",
                marginTop: "-17px",
                left: "-5%",
                animation: "slowFly 6s linear infinite",
                pointerEvents: "none",
              }}
              width="50"
              height="35"
              viewBox="0 0 50 35"
            >
              <g
                style={{
                  animation: "flap 0.4s ease-in-out infinite alternate",
                  transformOrigin: "25px 20px",
                }}
              >
                <path
                  d="M25 20 Q10 5 2 12 Q12 15 25 20Z"
                  fill="#6366f1"
                  opacity="0.9"
                />
              </g>
              <g
                style={{
                  animation: "flap 0.4s ease-in-out infinite alternate-reverse",
                  transformOrigin: "25px 20px",
                }}
              >
                <path
                  d="M25 20 Q40 5 48 12 Q38 15 25 20Z"
                  fill="#818cf8"
                  opacity="0.9"
                />
              </g>
              <ellipse cx="25" cy="22" rx="9" ry="5" fill="#4f46e5" />
              <circle cx="33" cy="19" r="4" fill="#4f46e5" />
              <circle cx="35" cy="18" r="1" fill="white" />
              <path d="M36 20 L40 21 L36 22Z" fill="#f97316" />
            </svg>
          </div>

          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: "5px",
              flexShrink: 0,
              zIndex: 1,
            }}
          >
            <div
              style={{
                width: "6px",
                height: "6px",
                borderRadius: "50%",
                background: "#6366f1",
                boxShadow: "0 0 4px #6366f1",
                animation: "blink 1.5s ease-in-out infinite",
              }}
            />
          </div>
        </div>

        {/* Idioma */}
        <div
          style={{
            padding: "8px 16px",
            borderBottom: "1px solid #f1f5f9",
            flexShrink: 0,
          }}
        >
          <LanguageSwitcher />
        </div>

        {/* Búsqueda */}
        <SearchPanel
          t={t}
          mapRef={mapRef}
          routingRef={routingRef}
          onRutaCalculada={(waypoints) => {
            setRouteWaypoints(waypoints);
            setRutaActiva(true);
          }}
          onRutaCancelada={() => {
            setRutaActiva(false);
            setRouteWaypoints([]);
          }}
        />

        <ReportButton mapRef={mapRef} />

        {/* Leyenda */}
        <div
          style={{
            padding: "12px 16px",
            borderBottom: "1px solid #f1f5f9",
            flexShrink: 0,
          }}
        >
          <p
            style={{
              margin: "0 0 8px",
              fontSize: "10px",
              color: "#94a3b8",
              textTransform: "uppercase",
              letterSpacing: "0.06em",
            }}
          >
            {t("riskZones")}
          </p>
          {[
            { key: "highRisk", color: "#ef4444" },
            { key: "mediumRisk", color: "#f97316" },
            { key: "safeZone", color: "#22c55e" },
          ].map((item) => (
            <div
              key={item.key}
              style={{
                display: "flex",
                alignItems: "center",
                gap: "8px",
                marginBottom: "5px",
              }}
            >
              <div
                style={{
                  width: "9px",
                  height: "9px",
                  borderRadius: "50%",
                  background: item.color,
                  flexShrink: 0,
                }}
              />
              <span style={{ fontSize: "12px", color: "#64748b" }}>
                {t(item.key)}
              </span>
            </div>
          ))}
        </div>

        {/* Lista de zonas */}
        <div style={{ flex: 1, overflowY: "auto", padding: "8px 16px" }}>
          {ZONAS_LISTA.map((zona, i) => (
            <div
              key={i}
              style={{
                display: "flex",
                alignItems: "center",
                gap: "8px",
                padding: "8px 0",
                borderBottom: "0.5px solid #f1f5f9",
              }}
            >
              <div
                style={{
                  width: "8px",
                  height: "8px",
                  borderRadius: "50%",
                  background: COLOR_NIVEL[zona.nivel],
                  flexShrink: 0,
                }}
              />
              <span style={{ fontSize: "12px", color: "#1e293b", flex: 1 }}>
                {zona.nombre}
              </span>
              <span
                style={{
                  fontSize: "10px",
                  padding: "2px 8px",
                  borderRadius: "10px",
                  background: BG_NIVEL[zona.nivel],
                  color: COLOR_NIVEL[zona.nivel],
                  fontWeight: 500,
                }}
              >
                {t(
                  zona.nivel === "alto"
                    ? "high"
                    : zona.nivel === "medio"
                      ? "medium"
                      : "low",
                )}
              </span>
            </div>
          ))}
        </div>
      </aside>

      {/* Mapa */}
      <div style={{ flex: 1, minWidth: 0, position: "relative" }}>
        <Map mapRef={mapRef} />
      </div>

      {/* Alertas en tiempo real */}
      <RouteAlert
        zonas={zonas}
        rutaActiva={rutaActiva}
        routeWaypoints={routeWaypoints}
      />
    </main>
  );
}
