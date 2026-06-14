"use client";

import { useTranslation } from "react-i18next";

const LANGS = [
  { code: "es", label: "ES" },
  { code: "en", label: "EN" },
  { code: "ru", label: "RU" },
  { code: "zh", label: "中文" },
];

export default function LanguageSwitcher() {
  const { i18n } = useTranslation();

  return (
    <div style={{ display: "flex", gap: "4px" }}>
      {LANGS.map((lang) => (
        <button
          key={lang.code}
          onClick={() => i18n.changeLanguage(lang.code)}
          style={{
            padding: "3px 8px",
            fontSize: "11px",
            fontWeight: i18n.language === lang.code ? 600 : 400,
            background: i18n.language === lang.code ? "#6366f1" : "transparent",
            color: i18n.language === lang.code ? "white" : "#94a3b8",
            border: `1px solid ${i18n.language === lang.code ? "#6366f1" : "#e2e8f0"}`,
            borderRadius: "6px",
            cursor: "pointer",
            transition: "all 0.15s",
          }}
        >
          {lang.label}
        </button>
      ))}
    </div>
  );
}
