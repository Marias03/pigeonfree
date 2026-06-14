"use client";

import { useEffect } from "react";

const KAZAN_CENTER: [number, number] = [55.8304, 49.0661];

interface Zona {
  lat: number;
  lng: number;
  nombre: string;
  nivel: "alto" | "medio" | "bajo";
}

const ZONAS_DEMO: Zona[] = [
  { lat: 55.7963, lng: 49.1088, nombre: "Plaza de la Libertad", nivel: "alto" },
  { lat: 55.7987, lng: 49.1221, nombre: "Kremlin de Kazán", nivel: "alto" },
  { lat: 55.8058, lng: 49.1175, nombre: "Bauman Street", nivel: "medio" },
  { lat: 55.8134, lng: 49.1043, nombre: "Estación Central", nivel: "alto" },
  { lat: 55.8201, lng: 49.1302, nombre: "Mercado Central", nivel: "medio" },
];

const COLOR_NIVEL: Record<string, string> = {
  alto: "#ef4444",
  medio: "#f97316",
  bajo: "#22c55e",
};

interface Props {
  mapRef: React.MutableRefObject<any>;
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

      if (mapRef.current) return;

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

      ZONAS_DEMO.forEach((zona) => {
        const circle = L.circle([zona.lat, zona.lng], {
          color: COLOR_NIVEL[zona.nivel],
          fillColor: COLOR_NIVEL[zona.nivel],
          fillOpacity: 0.2,
          radius: 150,
          weight: 2,
        }).addTo(map);

        circle.bindPopup(`
          <strong style="color:#1e293b">${zona.nombre}</strong><br/>
          <span style="font-size:12px;color:#64748b">Riesgo:</span>
          <b style="color:${COLOR_NIVEL[zona.nivel]}">${zona.nivel}</b>
        `);
      });

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
