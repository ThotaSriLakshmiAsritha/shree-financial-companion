import { FormEvent, useState } from "react";
import { useNavigate } from "react-router-dom";

import type { SupportedLanguage } from "@sahachari/contracts";

import { useAuth } from "./AuthContext";
import { useI18n } from "../i18n";

const languages: { code: SupportedLanguage; labelKey: "language.english" | "language.hindi" | "language.telugu" }[] = [
  { code: "te", labelKey: "language.telugu" },
  { code: "hi", labelKey: "language.hindi" },
  { code: "en", labelKey: "language.english" },
];

export function OnboardingPage() {
  const navigate = useNavigate();
  const { profile, preferences, saveProfile, authError } = useAuth();
  const { t, language, setLanguage } = useI18n();
  const [selectedLanguage, setSelectedLanguage] = useState<SupportedLanguage>(profile?.preferred_language ?? language);
  const [displayName, setDisplayName] = useState(profile?.display_name ?? "");
  const [phoneNumber, setPhoneNumber] = useState(profile?.phone_number ?? "");
  const [monthlyIncome, setMonthlyIncome] = useState(
    preferences?.monthly_income_estimate ? String(preferences.monthly_income_estimate) : "",
  );
  const [voiceEnabled, setVoiceEnabled] = useState(preferences?.voice_enabled ?? true);
  const [consentAccepted, setConsentAccepted] = useState(preferences?.consent_accepted ?? false);
  const [error, setError] = useState("");

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    try {
      await saveProfile({
        display_name: displayName.trim(),
        phone_number: phoneNumber.trim(),
        preferred_language: selectedLanguage,
        onboarding_completed: true,
        voice_enabled: voiceEnabled,
        preferred_channel: voiceEnabled ? "web" : "web",
        monthly_income_estimate: monthlyIncome ? Number(monthlyIncome) : undefined,
        financial_setup_completed: Boolean(monthlyIncome),
        consent_accepted: consentAccepted,
      });
      navigate("/", { replace: true });
    } catch {
      setError(t("errors.onboarding"));
    }
  }

  async function handleLanguageChange(nextLanguage: SupportedLanguage) {
    setSelectedLanguage(nextLanguage);
    await setLanguage(nextLanguage);
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-cream px-6 py-12 text-ink">
      <form className="w-full max-w-2xl rounded-3xl border border-ink/10 bg-white p-8 shadow-sm" onSubmit={handleSubmit}>
        <div className="flex items-center justify-between">
          <p className="text-xl font-semibold tracking-tight">
            sahachari<span className="text-leaf">.</span>
          </p>
          <span className="rounded-full bg-leaf/10 px-3 py-1 text-sm font-semibold text-leaf">
            {t("onboarding.languageLegend")}
          </span>
        </div>
        <h1 className="mt-10 text-3xl font-semibold">{t("onboarding.title")}</h1>
        <p className="mt-3 text-ink/60">{t("onboarding.subtitle")}</p>

        <fieldset className="mt-8">
          <legend className="text-sm font-semibold">{t("onboarding.languageLegend")}</legend>
          <div className="mt-3 grid gap-3 sm:grid-cols-3">
            {languages.map((item) => (
              <label
                key={item.code}
                className={[
                  "cursor-pointer rounded-2xl border p-4 transition focus-within:ring-2 focus-within:ring-leaf",
                  selectedLanguage === item.code ? "border-leaf bg-leaf/10" : "border-ink/10",
                ].join(" ")}
              >
                <input
                  className="sr-only"
                  type="radio"
                  name="preferred-language"
                  value={item.code}
                  checked={selectedLanguage === item.code}
                  onChange={() => void handleLanguageChange(item.code)}
                />
                <span className="block font-semibold">{t(item.labelKey)}</span>
              </label>
            ))}
          </div>
        </fieldset>

        <div className="mt-8 grid gap-4 sm:grid-cols-2">
          <label className="block text-sm font-medium">
            {t("onboarding.name")}
            <input
              className="mt-2 w-full rounded-xl border border-ink/15 px-4 py-3 outline-none focus:ring-2 focus:ring-leaf"
              required
              value={displayName}
              onChange={(event) => setDisplayName(event.target.value)}
            />
          </label>
          <label className="block text-sm font-medium">
            {t("onboarding.phone")}
            <input
              className="mt-2 w-full rounded-xl border border-ink/15 px-4 py-3 outline-none focus:ring-2 focus:ring-leaf"
              type="tel"
              required
              placeholder={t("onboarding.phonePlaceholder")}
              value={phoneNumber}
              onChange={(event) => setPhoneNumber(event.target.value)}
            />
          </label>
        </div>

        <section className="mt-8 rounded-2xl border border-ink/10 bg-cream/60 p-5" aria-labelledby="optional-setup-heading">
          <h2 id="optional-setup-heading" className="font-semibold">{t("onboarding.optionalSetup")}</h2>
          <label className="mt-4 block text-sm font-medium">
            {t("onboarding.monthlyIncome")}
            <input
              className="mt-2 w-full rounded-xl border border-ink/15 bg-white px-4 py-3 outline-none focus:ring-2 focus:ring-leaf"
              type="number"
              min="0"
              inputMode="decimal"
              value={monthlyIncome}
              onChange={(event) => setMonthlyIncome(event.target.value)}
            />
          </label>
          <p className="mt-2 text-sm text-ink/60">{t("onboarding.monthlyIncomeHelp")}</p>
        </section>

        <section className="mt-6 rounded-2xl border border-ink/10 bg-cream/60 p-5" aria-labelledby="voice-heading">
          <h2 id="voice-heading" className="font-semibold">{t("onboarding.voicePreference")}</h2>
          <label className="mt-4 flex items-start gap-3 text-sm">
            <input
              className="mt-1 h-4 w-4 accent-leaf"
              type="checkbox"
              checked={voiceEnabled}
              onChange={(event) => setVoiceEnabled(event.target.checked)}
            />
            <span>{t("onboarding.voiceEnabled")}</span>
          </label>
        </section>

        <label className="mt-6 flex items-start gap-3 text-sm">
          <input
            className="mt-1 h-4 w-4 accent-leaf"
            type="checkbox"
            required
            checked={consentAccepted}
            onChange={(event) => setConsentAccepted(event.target.checked)}
          />
          <span>
            {t("onboarding.consent")}
            <span className="mt-1 block text-ink/60">{t("onboarding.consentHelp")}</span>
          </span>
        </label>

        {(error || authError) && (
          <p className="mt-5 rounded-xl bg-red-50 px-4 py-3 text-sm text-red-800" role="alert">
            {error || t("errors.sessionRestore")}
          </p>
        )}

        <button className="mt-8 w-full rounded-full bg-ink px-4 py-3 font-semibold text-white hover:bg-leaf focus:outline-none focus:ring-2 focus:ring-leaf" type="submit">
          {t("onboarding.continue")}
        </button>
      </form>
    </main>
  );
}

