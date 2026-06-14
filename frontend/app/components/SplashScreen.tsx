"use client";

import { useEffect, useState } from "react";

export default function SplashScreen({ onFinish }: { onFinish: () => void }) {
  const [progress, setProgress] = useState(0);
  const [status, setStatus] = useState("Initializing radar...");

  const messages = [
    "Initializing radar...",
    "Scanning for pigeons...",
    "Mapping danger zones...",
    "Calculating safe routes...",
    "Ready.",
  ];

  useEffect(() => {
    let current = 0;
    const interval = setInterval(() => {
      current += 1;
      setProgress(current);

      const msgIndex = Math.floor((current / 100) * messages.length);
      setStatus(messages[Math.min(msgIndex, messages.length - 1)]);

      if (current >= 100) {
        clearInterval(interval);
        setTimeout(onFinish, 600);
      }
    }, 25);

    return () => clearInterval(interval);
  }, []);

  return (
    <div
      style={{
        position: "fixed",
        inset: 0,
        background: "#000d00",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        zIndex: 9999,
        gap: "24px",
        fontFamily: "monospace",
      }}
    >
      {/* Radar */}
      <div style={{ position: "relative", width: "180px", height: "180px" }}>
        {/* Anillos */}
        {[180, 130, 80, 40].map((size, i) => (
          <div
            key={i}
            style={{
              position: "absolute",
              width: size,
              height: size,
              borderRadius: "50%",
              border: `1px solid rgba(0,255,70,${0.15 + i * 0.05})`,
              top: "50%",
              left: "50%",
              transform: "translate(-50%, -50%)",
            }}
          />
        ))}

        {/* Cruz */}
        <div
          style={{
            position: "absolute",
            top: "50%",
            left: 0,
            right: 0,
            height: "1px",
            background: "rgba(0,255,70,0.15)",
          }}
        />
        <div
          style={{
            position: "absolute",
            left: "50%",
            top: 0,
            bottom: 0,
            width: "1px",
            background: "rgba(0,255,70,0.15)",
          }}
        />

        {/* Sweep animado con CSS */}
        <div
          style={{
            position: "absolute",
            top: "50%",
            left: "50%",
            width: "90px",
            height: "1px",
            background:
              "linear-gradient(90deg, rgba(0,255,70,0.8), transparent)",
            transformOrigin: "left center",
            animation: "sweep 2s linear infinite",
          }}
        />

        {/* Blips */}
        <div
          style={{
            position: "absolute",
            top: "28%",
            left: "62%",
            width: "6px",
            height: "6px",
            background: "#00ff46",
            borderRadius: "50%",
            animation: "blip 2s ease-in-out infinite",
            boxShadow: "0 0 8px #00ff46",
          }}
        />
        <div
          style={{
            position: "absolute",
            top: "62%",
            left: "32%",
            width: "5px",
            height: "5px",
            background: "#00ff46",
            borderRadius: "50%",
            animation: "blip 2s ease-in-out infinite 0.7s",
            boxShadow: "0 0 8px #00ff46",
          }}
        />
        <div
          style={{
            position: "absolute",
            top: "45%",
            left: "75%",
            width: "4px",
            height: "4px",
            background: "#00ff46",
            borderRadius: "50%",
            animation: "blip 2s ease-in-out infinite 1.3s",
            boxShadow: "0 0 6px #00ff46",
          }}
        />

        {/* Paloma en el centro */}
        <div
          style={{
            position: "absolute",
            top: "50%",
            left: "50%",
            transform: "translate(-50%, -50%)",
            fontSize: "20px",
            animation: "bobble 1.5s ease-in-out infinite",
          }}
        >
          🕊️
        </div>
      </div>

      {/* Logo */}
      <div style={{ textAlign: "center" }}>
        <div
          style={{
            fontSize: "20px",
            fontWeight: 500,
            color: "#00ff46",
            letterSpacing: "0.2em",
          }}
        >
          PIGEONFREE
        </div>
        <div
          style={{
            fontSize: "11px",
            color: "rgba(0,255,70,0.5)",
            letterSpacing: "0.1em",
            marginTop: "4px",
          }}
        >
          PIGEON DETECTION SYSTEM v1.0
        </div>
      </div>

      {/* Status */}
      <div
        style={{
          fontSize: "11px",
          color: "rgba(0,255,70,0.7)",
          letterSpacing: "0.08em",
          height: "16px",
        }}
      >
        {status}
      </div>

      {/* Barra de progreso */}
      <div
        style={{
          width: "200px",
          height: "2px",
          background: "rgba(0,255,70,0.1)",
          borderRadius: "2px",
          overflow: "hidden",
        }}
      >
        <div
          style={{
            height: "100%",
            width: `${progress}%`,
            background: "#00ff46",
            borderRadius: "2px",
            boxShadow: "0 0 8px #00ff46",
            transition: "width 0.02s linear",
          }}
        />
      </div>

      <div
        style={{
          fontSize: "10px",
          color: "rgba(0,255,70,0.4)",
          letterSpacing: "0.05em",
        }}
      >
        {progress}%
      </div>

      <style>{`
        @keyframes sweep {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
        @keyframes blip {
          0%, 100% { opacity: 0; }
          50% { opacity: 1; }
        }
        @keyframes bobble {
          0%, 100% { transform: translate(-50%, -50%) rotate(-3deg); }
          50% { transform: translate(-50%, -56%) rotate(3deg); }
        }
      `}</style>
    </div>
  );
}
