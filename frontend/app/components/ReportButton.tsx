"use client";

import { useState } from "react";

interface Props {
  mapRef: React.RefObject<any>;
}

export default function ReportButton({ mapRef }: Props) {
  const [modo, setModo] = useState(false);
  const [estado, setEstado] = useState<"idle" | "loading" | "success" | "fail">(
    "idle",
  );
  const [mensaje, setMensaje] = useState("");

  const activarModo = () => {
    if (!mapRef.current) return;
    setModo(true);
    setEstado("idle");
    setMensaje("Toca el mapa donde viste palomas 🗺️");

    (window as any).__pigeonReportMode = true;
    (window as any).__pigeonReportCallback = async (
      lat: number,
      lng: number,
    ) => {
      (window as any).__reportMode = false;
      setEstado("loading");
      setMensaje("Reportando zona...");

      try {
        const res = await fetch(
          `http://127.0.0.1:8000/report?lat=${lat}&lng=${lng}`,
          { method: "POST" },
        );
        const data = await res.json();

        if (data.detectado) {
          setEstado("success");
          setMensaje(data.mensaje);
        } else {
          setEstado("fail");
          setMensaje(data.mensaje);
        }
      } catch {
        setEstado("fail");
        setMensaje("Error al reportar");
      }

      setTimeout(() => {
        setModo(false);
        setEstado("idle");
        setMensaje("");
      }, 3000);
    };
  };

  const cancelar = () => {
    (window as any).__pigeonReportMode = false;
    setModo(false);
    setEstado("idle");
    setMensaje("");
  };

  return (
    <div
      style={{
        padding: "10px 16px",
        borderBottom: "1px solid #f1f5f9",
        flexShrink: 0,
      }}
    >
      {!modo ? (
        <button
          onClick={activarModo}
          style={{
            width: "100%",
            background: "white",
            color: "#64748b",
            border: "1px solid #e2e8f0",
            borderRadius: "8px",
            padding: "8px",
            fontSize: "12px",
            fontWeight: 500,
            cursor: "pointer",
          }}
        >
          🕊️ Reportar palomas aquí
        </button>
      ) : (
        <div>
          <div
            style={{
              padding: "8px 10px",
              borderRadius: "8px",
              background: "#fef2f2",
              border: "1px solid #fca5a5",
              fontSize: "12px",
              color: "#dc2626",
              marginBottom: "6px",
              textAlign: "center",
            }}
          >
            {mensaje}
          </div>
          <button
            onClick={cancelar}
            style={{
              width: "100%",
              background: "white",
              color: "#94a3b8",
              border: "1px solid #e2e8f0",
              borderRadius: "8px",
              padding: "6px",
              fontSize: "11px",
              cursor: "pointer",
            }}
          >
            Cancelar
          </button>
        </div>
      )}

      {estado === "success" && (
        <div
          style={{
            marginTop: "6px",
            padding: "6px 10px",
            borderRadius: "6px",
            fontSize: "11px",
            background: "#f0fdf4",
            color: "#16a34a",
            border: "1px solid #bbf7d0",
          }}
        >
          ✅ {mensaje}
        </div>
      )}
      {estado === "fail" && (
        <div
          style={{
            marginTop: "6px",
            padding: "6px 10px",
            borderRadius: "6px",
            fontSize: "11px",
            background: "#fef2f2",
            color: "#dc2626",
            border: "1px solid #fca5a5",
          }}
        >
          ❌ {mensaje}
        </div>
      )}
    </div>
  );
}
