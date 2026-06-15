"use client";

import { useEffect } from "react";

const KAZAN_CENTER: [number, number] = [55.8304, 49.0661];

interface Props {
  mapRef: React.RefObject<any>;
}

export default function Map({ mapRef }: Props) {
  useEffect(() => {
    const initMap = async () => {
      const L = (await import("leaflet")).default;
      await import("leaflet/dist/leaflet.css");
      await import("leaflet-routing-machine");

      delete (L.Icon.Default.prototype as any)._getIconUrl;
      L.Icon.Default.mergeOptions({
        iconRetinaUrl:
          "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",
        iconUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
        shadowUrl:
          "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
      });

      const container = document.getElementById("map-container");
      if (mapRef.current || (container && (container as any)._leaflet_id))
        return;

      const map = L.map("map-container", { zoomControl: false }).setView(
        KAZAN_CENTER,
        13,
      );

      L.tileLayer(
        "https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png",
        {
          attribution:
            '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="https://carto.com/">CARTO</a>',
          maxZoom: 19,
        },
      ).addTo(map);

      L.control.zoom({ position: "bottomright" }).addTo(map);

      map.on("click", (e: any) => {
        if ((window as any).__pigeonReportMode) {
          const { lat, lng } = e.latlng;
          (window as any).__pigeonReportMode = false;
          (window as any).__pigeonReportCallback?.(lat, lng);
        }
      });

      try {
        const res = await fetch("http://127.0.0.1:8000/zones");
        const data = await res.json();

        data.zones.forEach(
          (zona: {
            lat: number;
            lng: number;
            score: number;
            nivel: string;
            probabilidad: number;
          }) => {
            const color =
              zona.nivel === "alto"
                ? "#ef4444"
                : zona.nivel === "medio"
                  ? "#f97316"
                  : "#22c55e";

            const radio =
              zona.probabilidad >= 0.6
                ? 120
                : zona.probabilidad >= 0.35
                  ? 90
                  : 60;

            const opacidad = 0.1 + zona.probabilidad * 0.4;

            const circle = L.circle([zona.lat, zona.lng], {
              color,
              fillColor: color,
              fillOpacity: opacidad,
              radius: radio,
              weight: zona.probabilidad >= 0.6 ? 2 : 1,
            }).addTo(map);

            const porcentaje = Math.round(zona.probabilidad * 100);
            const emoji =
              zona.nivel === "alto"
                ? "🔴"
                : zona.nivel === "medio"
                  ? "🟠"
                  : "🟢";

            circle.bindPopup(`
            <div style="font-family:sans-serif;min-width:160px">
              <strong style="color:#1e293b;font-size:13px">${emoji} Zona de palomas</strong><br/>
              <div style="margin-top:6px">
                <div style="font-size:11px;color:#64748b">Probabilidad ML</div>
                <div style="background:#f1f5f9;border-radius:4px;margin-top:3px;overflow:hidden;height:8px">
                  <div style="background:${color};height:100%;width:${porcentaje}%;transition:width 0.3s"></div>
                </div>
                <div style="font-size:12px;font-weight:500;color:${color};margin-top:3px">${porcentaje}% — ${zona.nivel}</div>
              </div>
            </div>
          `);
          },
        );
      } catch (e) {
        console.error("Error cargando zonas:", e);
      }
      // Exponer función para modo reporte
      (mapRef.current as any) = map;
      map.on("click", (e: any) => {
        if ((window as any).__reportMode) {
          (window as any).__reportCallback?.(e.latlng.lat, e.latlng.lng);
        }
      });

      mapRef.current = map;
      window.dispatchEvent(new Event("mapReady"));
    };

    initMap();

    return () => {
      if (mapRef.current) {
        mapRef.current.remove();
        mapRef.current = null;
      }
    };
  }, []);

  return <div id="map-container" style={{ height: "100%", width: "100%" }} />;
}
