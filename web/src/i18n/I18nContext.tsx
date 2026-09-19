import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from "react";

import type { SupportedLanguage } from "@sahachari/contracts";

import { useAuth } from "../auth/AuthContext";
import { en, hi, te, type Language, type TranslationKey } from "./messages";

const LANGUAGE_STORAGE_KEY = "sahachari.language";
const dictionaries = { en, hi, te } satisfies Record<Language, Record<TranslationKey, string>>;

type I18nContextValue = {
  language: Language;
  setLanguage: (language: Language) => Promise<void>;
  t: (key: TranslationKey, values?: Record<string, string | number>) => string;
};

const I18nContext = createContext<I18nContextValue | undefined>(undefined);

function readStoredLanguage(): Language {
  const stored = window.localStorage.getItem(LANGUAGE_STORAGE_KEY);
  return stored === "en" || stored === "hi" || stored === "te" ? stored : "en";
}

export function I18nProvider({ children }: { children: ReactNode }) {
  const { profile, session, saveProfile } = useAuth();
  const [language, setLanguageState] = useState<Language>(() => readStoredLanguage());

  useEffect(() => {
    if (profile?.preferred_language) {
      setLanguageState(profile.preferred_language);
      window.localStorage.setItem(LANGUAGE_STORAGE_KEY, profile.preferred_language);
    }
  }, [profile?.preferred_language]);

  async function setLanguage(nextLanguage: SupportedLanguage) {
    setLanguageState(nextLanguage);
    window.localStorage.setItem(LANGUAGE_STORAGE_KEY, nextLanguage);
    if (session && profile && profile.preferred_language !== nextLanguage) {
      await saveProfile({ preferred_language: nextLanguage });
    }
  }

  const value = useMemo<I18nContextValue>(
    () => ({
      language,
      setLanguage,
      t(key, values) {
        const template = dictionaries[language][key] ?? dictionaries.en[key];
        return Object.entries(values ?? {}).reduce(
          (text, [name, replacement]) => text.replaceAll("{{" + name + "}}", String(replacement)),
          template,
        );
      },
    }),
    [language, profile, session],
  );

  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>;
}

export function useI18n() {
  const context = useContext(I18nContext);
  if (!context) throw new Error("useI18n must be used inside I18nProvider.");
  return context;
}

