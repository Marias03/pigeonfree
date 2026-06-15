"use client";

import { useEffect, useRef, useState } from "react";

interface Zona {
  lat: number;
  lng: number;
  nivel: string;
  probabilidad: number;
}

interface Props {
  zonas: Zona[];
  rutaActiva: boolean;
  routeWaypoints: { lat: number; lng: number }[];
}

function distanciaMetros(
  lat1: number,
  lng1: number,
  lat2: number,
  lng2: number,
): number {
  const R = 6371000;
  const dlat = ((lat2 - lat1) * Math.PI) / 180;
  const dlng = ((lng2 - lng1) * Math.PI) / 180;
  const a =
    Math.sin(dlat / 2) ** 2 +
    Math.cos((lat1 * Math.PI) / 180) *
      Math.cos((lat2 * Math.PI) / 180) *
      Math.sin(dlng / 2) ** 2;
  return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
}

function zonaEnRuta(
  zona: Zona,
  waypoints: { lat: number; lng: number }[],
  radioMetros = 50,
): boolean {
  return waypoints.some(
    (wp) => distanciaMetros(zona.lat, zona.lng, wp.lat, wp.lng) < radioMetros,
  );
}

function zonaDelante(
  zona: Zona,
  userLat: number,
  userLng: number,
  waypoints: { lat: number; lng: number }[],
): boolean {
  // Encontrar el waypoint más cercano al usuario
  let minDist = Infinity;
  let userIdx = 0;
  waypoints.forEach((wp, i) => {
    const d = distanciaMetros(userLat, userLng, wp.lat, wp.lng);
    if (d < minDist) {
      minDist = d;
      userIdx = i;
    }
  });

  // Encontrar el waypoint más cercano a la zona
  let zonaIdx = 0;
  let minZonaDist = Infinity;
  waypoints.forEach((wp, i) => {
    const d = distanciaMetros(zona.lat, zona.lng, wp.lat, wp.lng);
    if (d < minZonaDist) {
      minZonaDist = d;
      zonaIdx = i;
    }
  });

  return zonaIdx > userIdx;
}

export default function RouteAlert({
  zonas,
  rutaActiva,
  routeWaypoints,
}: Props) {
  const [alerta, setAlerta] = useState<{
    mensaje: string;
    nivel: string;
    distancia: number;
  } | null>(null);
  const [userPos, setUserPos] = useState<{ lat: number; lng: number } | null>(
    null,
  );
  const zonasNotificadas = useRef<Set<string>>(new Set());
  const watchId = useRef<number | null>(null);

  useEffect(() => {
    if (!rutaActiva || routeWaypoints.length === 0) {
      if (watchId.current !== null) {
        navigator.geolocation.clearWatch(watchId.current);
        watchId.current = null;
      }
      setAlerta(null);
      zonasNotificadas.current.clear();
      return;
    }

    if (!navigator.geolocation) return;

    watchId.current = navigator.geolocation.watchPosition(
      (pos) => {
        const { latitude, longitude } = pos.coords;
        setUserPos({ lat: latitude, lng: longitude });

        for (const zona of zonas) {
          if (zona.probabilidad < 0.6) continue;

          const zonaKey = `${zona.lat.toFixed(4)}_${zona.lng.toFixed(4)}`;
          if (zonasNotificadas.current.has(zonaKey)) continue;

          const distancia = distanciaMetros(
            latitude,
            longitude,
            zona.lat,
            zona.lng,
          );
          if (distancia > 300) continue;

          if (!zonaEnRuta(zona, routeWaypoints)) continue;
          if (!zonaDelante(zona, latitude, longitude, routeWaypoints)) continue;

          const minutos = Math.round(distancia / 80);
          const mensaje =
            minutos <= 1
              ? "⚠️ Zona de palomas a menos de 1 minuto"
              : `⚠️ Alta presencia de palomas a ${minutos} minutos`;

          setAlerta({
            mensaje,
            nivel: zona.nivel,
            distancia: Math.round(distancia),
          });
          zonasNotificadas.current.add(zonaKey);

          if ("vibrate" in navigator) navigator.vibrate([200, 100, 200]);

          setTimeout(() => setAlerta(null), 8000);
          break;
        }
      },
      (err) => console.error("GPS error:", err),
      { enableHighAccuracy: true, maximumAge: 3000, timeout: 10000 },
    );

    return () => {
      if (watchId.current !== null) {
        navigator.geolocation.clearWatch(watchId.current);
      }
    };
  }, [rutaActiva, zonas, routeWaypoints]);

  if (!rutaActiva) return null;

  return (
    <div
      style={{
        position: "fixed",
        bottom: "24px",
        left: "50%",
        transform: "translateX(-50%)",
        zIndex: 9999,
        width: "90%",
        maxWidth: "400px",
      }}
    >
      {userPos && (
        <div
          style={{
            background: "white",
            border: "1px solid #e2e8f0",
            borderRadius: "10px",
            padding: "8px 12px",
            fontSize: "11px",
            color: "#94a3b8",
            marginBottom: "8px",
            textAlign: "center",
            boxShadow: "0 2px 8px rgba(0,0,0,0.08)",
          }}
        >
          📍 GPS activo — monitoreando ruta
        </div>
      )}

      {alerta && (
        <div
          style={{
            background: alerta.nivel === "alto" ? "#fef2f2" : "#fff7ed",
            border: `2px solid ${alerta.nivel === "alto" ? "#ef4444" : "#f97316"}`,
            borderRadius: "12px",
            padding: "14px 16px",
            boxShadow: "0 4px 20px rgba(0,0,0,0.15)",
            animation: "slideUp 0.3s ease",
          }}
        >
          <div
            style={{
              fontSize: "15px",
              fontWeight: 600,
              color: alerta.nivel === "alto" ? "#dc2626" : "#ea580c",
              marginBottom: "4px",
            }}
          >
            {alerta.mensaje}
          </div>
          <div style={{ fontSize: "12px", color: "#64748b" }}>
            A {alerta.distancia}m de tu posición actual
          </div>
          <button
            onClick={() => setAlerta(null)}
            style={{
              position: "absolute",
              top: "8px",
              right: "10px",
              background: "none",
              border: "none",
              cursor: "pointer",
              fontSize: "16px",
              color: "#94a3b8",
            }}
          >
            ✕
          </button>
        </div>
      )}

      <style>{`
        @keyframes slideUp {
          from { transform: translateY(20px); opacity: 0; }
          to { transform: translateY(0); opacity: 1; }
        }
      `}</style>
    </div>
  );
}
