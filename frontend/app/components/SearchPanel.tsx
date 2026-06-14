"use client";

import { useState } from "react";
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

  const geocode = async (address: string): Promise<[number, number] | null> => {
    console.log("Geocodificando:", address);
    try {
      const url = `http://127.0.0.1:8000/geocode?q=${encodeURIComponent(address)}&lang=${i18n.language}`;
      console.log("URL:", url);
      const res = await fetch(url);
      console.log("Status:", res.status);
      const data = await res.json();
      console.log("Data:", data);
      if (data.error) return null;
      return [data.lat, data.lng];
    } catch (e) {
      console.error("Error geocode:", e);
      return null;
    }
  };

  const calcularRuta = async () => {
    console.log("mapRef.current:", mapRef.current);
    if (!origin || !destination) return;
    if (!mapRef.current) {
      alert("El mapa aún no está listo, espera un momento");
      return;
    }
    setLoading(true);

    const from = await geocode(origin);
    const to = await geocode(destination);

    console.log("from:", from, "to:", to);

    if (!from || !to) {
      alert(t("useKeywords"));
      setLoading(false);
      return;
    }

    const L = (await import("leaflet")).default;

    if (routingRef.current) mapRef.current.removeControl(routingRef.current);

    const routing = (L as any).Routing.control({
      waypoints: [L.latLng(from[0], from[1]), L.latLng(to[0], to[1])],
      routeWhileDragging: false,
      showAlternatives: true,
      lineOptions: {
        styles: [{ color: "#6366f1", weight: 5, opacity: 0.85 }],
      },
      altLineOptions: {
        styles: [{ color: "#cbd5e1", weight: 4, opacity: 0.6 }],
      },
      createMarker: (i: number, wp: any) => {
        return L.marker(wp.latLng, {
          icon: L.divIcon({
            className: "",
            html: `<div style="background:${i === 0 ? "#6366f1" : "#ef4444"};width:13px;height:13px;border-radius:50%;border:2px solid white;box-shadow:0 1px 4px rgba(0,0,0,0.3)"></div>`,
            iconSize: [13, 13],
            iconAnchor: [6, 6],
          }),
        });
      },
      collapsible: true,
      show: false,
    }).addTo(mapRef.current);

    routingRef.current = routing;
    setLoading(false);
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
        disabled={loading || !origin || !destination}
        style={{
          width: "100%",
          background: loading ? "#94a3b8" : "#6366f1",
          color: "white",
          border: "none",
          borderRadius: "8px",
          padding: "10px",
          fontSize: "13px",
          fontWeight: 500,
          cursor: loading ? "not-allowed" : "pointer",
          transition: "background 0.2s",
        }}
      >
        {loading ? t("calculating") : `🚫 ${t("calculate")}`}
      </button>
    </div>
  );
}
