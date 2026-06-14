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

      // Cargar zonas reales desde el backend
      try {
        const res = await fetch("http://127.0.0.1:8000/zones");
        const data = await res.json();

        data.zones.forEach(
          (zona: {
            lat: number;
            lng: number;
            score: number;
            nivel: string;
          }) => {
            const color =
              zona.nivel === "alto"
                ? "#ef4444"
                : zona.nivel === "medio"
                  ? "#f97316"
                  : "#22c55e";
            const circle = L.circle([zona.lat, zona.lng], {
              color,
              fillColor: color,
              fillOpacity: 0.2,
              radius: 80,
              weight: 1.5,
            }).addTo(map);

            circle.bindPopup(`
            <strong style="color:#1e293b">Zona de palomas</strong><br/>
            <span style="font-size:12px;color:#64748b">Score: ${zona.score}</span>
          `);
          },
        );
      } catch (e) {
        console.error("Error cargando zonas:", e);
      }

      mapRef.current = map;
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
