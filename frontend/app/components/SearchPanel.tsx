"use client";

import { useState, useEffect } from "react";
import { useTranslation } from "react-i18next";

interface Props {
  t: (key: string) => string;
  mapRef: React.RefObject<any>;
  routingRef: React.RefObject<any>;
}

export default function SearchPanel({ t, mapRef, routingRef }: Props) {
  const { i18n } = useTranslation();
  const [origin, setOrigin] = useState("");
  const [destination, setDestination] = useState("");
  const [loading, setLoading] = useState(false);
  const [mapReady, setMapReady] = useState(false);
  const [riesgo, setRiesgo] = useState<{
    zonas: number;
    nivel: string;
    distancia: number;
    duracion: number;
    probabilidad: number;
  } | null>(null);

  useEffect(() => {
    const handler = () => setMapReady(true);
    window.addEventListener("mapReady", handler);
    return () => window.removeEventListener("mapReady", handler);
  }, []);

  const geocode = async (address: string): Promise<[number, number] | null> => {
    try {
      const url = `http://127.0.0.1:8000/geocode?q=${encodeURIComponent(address)}&lang=${i18n.language}`;
      const res = await fetch(url);
      const data = await res.json();
      if (data.error) return null;
      return [data.lat, data.lng];
    } catch (e) {
      console.error("Error geocode:", e);
      return null;
    }
  };

  const calcularRuta = async () => {
    if (!origin || !destination) return;
    if (!mapRef.current) {
      alert("El mapa aún no está listo");
      return;
    }
    setLoading(true);
    setRiesgo(null);

    const from = await geocode(origin);
    const to = await geocode(destination);

    if (!from || !to) {
      alert(t("useKeywords"));
      setLoading(false);
      return;
    }

    const L = (await import("leaflet")).default;

    if (routingRef.current) {
      if (routingRef.current.remove) {
        routingRef.current.remove();
      } else {
        mapRef.current.removeLayer(routingRef.current);
      }
      routingRef.current = null;
    }

    try {
      const res = await fetch(
        `http://127.0.0.1:8000/route?from_lat=${from[0]}&from_lng=${from[1]}&to_lat=${to[0]}&to_lng=${to[1]}`,
      );
      const data = await res.json();

      if (data.error) {
        alert("No se pudo calcular la ruta");
        setLoading(false);
        return;
      }

      const waypoints = data.waypoints.map((wp: { lat: number; lng: number }) =>
        L.latLng(wp.lat, wp.lng),
      );

      const polyline = L.polyline(waypoints, {
        color: "#6366f1",
        weight: 5,
        opacity: 0.85,
      }).addTo(mapRef.current);

      mapRef.current.fitBounds(polyline.getBounds(), { padding: [40, 40] });

      const markerOrigin = L.marker([from[0], from[1]], {
        icon: L.divIcon({
          className: "",
          html: `<div style="background:#6366f1;width:13px;height:13px;border-radius:50%;border:2px solid white;box-shadow:0 1px 4px rgba(0,0,0,0.3)"></div>`,
          iconSize: [13, 13],
          iconAnchor: [6, 6],
        }),
      }).addTo(mapRef.current);

      const markerDest = L.marker([to[0], to[1]], {
        icon: L.divIcon({
          className: "",
          html: `<div style="background:#ef4444;width:13px;height:13px;border-radius:50%;border:2px solid white;box-shadow:0 1px 4px rgba(0,0,0,0.3)"></div>`,
          iconSize: [13, 13],
          iconAnchor: [6, 6],
        }),
      }).addTo(mapRef.current);

      routingRef.current = {
        polyline,
        markerOrigin,
        markerDest,
        remove: () => {
          mapRef.current?.removeLayer(polyline);
          mapRef.current?.removeLayer(markerOrigin);
          mapRef.current?.removeLayer(markerDest);
        },
      };

      const distanciaKm = (data.distancia_m / 1000).toFixed(1);
      const duracionMin = Math.round(data.duracion_s / 60);
      const prob = data.probabilidad_media || 0;

      setRiesgo({
        zonas: data.zonas_cruzadas || 0,
        nivel: data.nivel_riesgo,
        distancia: parseFloat(distanciaKm),
        duracion: duracionMin,
        probabilidad: prob,
      });
    } catch (e) {
      console.error("Error calculando ruta:", e);
      alert("Error calculando ruta");
    }

    setLoading(false);
  };

  const colorNivel = (nivel: string) => {
    if (nivel === "alto")
      return { bg: "#fef2f2", border: "#fca5a5", text: "#dc2626" };
    if (nivel === "medio")
      return { bg: "#fff7ed", border: "#fed7aa", text: "#ea580c" };
    return { bg: "#f0fdf4", border: "#bbf7d0", text: "#16a34a" };
  };

  return (
    <div
      style={{
        padding: "12px 16px",
        borderBottom: "1px solid #f1f5f9",
        flexShrink: 0,
      }}
    >
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: "8px",
          marginBottom: "8px",
        }}
      >
        <div
          style={{
            width: "8px",
            height: "8px",
            borderRadius: "50%",
            background: "#6366f1",
            flexShrink: 0,
            boxShadow: "0 0 4px #6366f1",
          }}
        />
        <input
          type="text"
          placeholder={`${t("origin")} — ${t("originPlaceholder")}`}
          value={origin}
          onChange={(e) => setOrigin(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && calcularRuta()}
          style={{
            flex: 1,
            border: "1px solid #e2e8f0",
            borderRadius: "8px",
            padding: "8px 10px",
            fontSize: "13px",
            outline: "none",
          }}
        />
      </div>

      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: "8px",
          marginBottom: "10px",
        }}
      >
        <div
          style={{
            width: "8px",
            height: "8px",
            borderRadius: "50%",
            background: "#ef4444",
            flexShrink: 0,
            boxShadow: "0 0 4px #ef4444",
          }}
        />
        <input
          type="text"
          placeholder={`${t("destination")} — ${t("destinationPlaceholder")}`}
          value={destination}
          onChange={(e) => setDestination(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && calcularRuta()}
          style={{
            flex: 1,
            border: "1px solid #e2e8f0",
            borderRadius: "8px",
            padding: "8px 10px",
            fontSize: "13px",
            outline: "none",
          }}
        />
      </div>

      <button
        onClick={calcularRuta}
        disabled={loading || !origin || !destination || !mapReady}
        style={{
          width: "100%",
          background: loading ? "#94a3b8" : !mapReady ? "#cbd5e1" : "#6366f1",
          color: "white",
          border: "none",
          borderRadius: "8px",
          padding: "10px",
          fontSize: "13px",
          fontWeight: 500,
          cursor: loading || !mapReady ? "not-allowed" : "pointer",
          transition: "background 0.2s",
        }}
      >
        {loading
          ? t("calculating")
          : !mapReady
            ? "Cargando mapa..."
            : `🚫 ${t("calculate")}`}
      </button>

      {riesgo &&
        (() => {
          const c = colorNivel(riesgo.nivel);
          const porcentaje = Math.round(riesgo.probabilidad * 100);
          return (
            <div
              style={{
                marginTop: "10px",
                padding: "10px 12px",
                borderRadius: "8px",
                background: c.bg,
                border: `1px solid ${c.border}`,
              }}
            >
              <div
                style={{
                  fontSize: "12px",
                  color: "#64748b",
                  marginBottom: "4px",
                }}
              >
                🚶 {riesgo.distancia} km · {riesgo.duracion} min a pie
              </div>
              <div
                style={{
                  fontSize: "11px",
                  color: "#94a3b8",
                  marginBottom: "4px",
                }}
              >
                Probabilidad de palomas en ruta
              </div>
              <div
                style={{
                  background: "#e2e8f0",
                  borderRadius: "4px",
                  overflow: "hidden",
                  height: "6px",
                  marginBottom: "4px",
                }}
              >
                <div
                  style={{
                    background: c.text,
                    height: "100%",
                    width: `${porcentaje}%`,
                    transition: "width 0.3s",
                  }}
                />
              </div>
              <div style={{ color: c.text, fontWeight: 500, fontSize: "12px" }}>
                {porcentaje}% —{" "}
                {riesgo.nivel === "alto"
                  ? "⚠️ Alto riesgo"
                  : riesgo.nivel === "medio"
                    ? "⚡ Riesgo medio"
                    : "✅ Ruta segura"}
              </div>
            </div>
          );
        })()}
    </div>
  );
}
