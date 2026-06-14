"use client";

import { useEffect, useState } from "react";
import i18n from "../i18n";
import { I18nextProvider } from "react-i18next";

export default function I18nProvider({
  children,
}: {
  children: React.ReactNode;
}) {
  const [ready, setReady] = useState(false);

  useEffect(() => {
    const loadTranslations = async () => {
      const langs = ["es", "en", "ru", "zh"];
      for (const lang of langs) {
        const res = await fetch(`/locales/${lang}/common.json`);
        const data = await res.json();
        i18n.addResourceBundle(lang, "common", data, true, true);
      }
      setReady(true);
    };
    loadTranslations();
  }, []);

  if (!ready) return null;

  return <I18nextProvider i18n={i18n}>{children}</I18nextProvider>;
}
