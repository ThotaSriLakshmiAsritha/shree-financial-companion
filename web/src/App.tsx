import { useState } from "react";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";

import { getHealth } from "./api/client";
import { AuthPage } from "./auth/AuthPage";
import { useAuth } from "./auth/AuthContext";
import { OnboardingPage } from "./auth/OnboardingPage";
import { ProtectedRoute } from "./auth/ProtectedRoute";
import { useI18n } from "./i18n";
import { StatusCard } from "./components/StatusCard";

function Dashboard() {
  const { profile, signOut, linkGoogleAccount } = useAuth();
  const { t, language, setLanguage } = useI18n();
  const [connection, setConnection] = useState<"idle" | "checking" | "connected" | "error">("idle");

  async function handleHealthCheck() {
    setConnection("checking");
    try {
      await getHealth();
      setConnection("connected");
    } catch {
      setConnection("error");
    }
  }

  return (
    <div className="min-h-screen bg-cream text-ink">
      <header className="border-b border-ink/10 bg-cream/90">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-4 px-6 py-5">
          <a className="text-xl font-semibold tracking-tight" href="/" aria-label={t("brand.home")}>
            sahachari<span className="text-leaf">.</span>
          </a>
          <nav className="order-3 w-full md:order-2 md:w-auto" aria-label={t("navigation.primary")}>
            <div className="flex flex-wrap gap-4 text-sm font-semibold text-ink/70">
              <a href="#home" className="hover:text-leaf">{t("navigation.dashboard")}</a>
              <a href="#talk" className="hover:text-leaf">{t("navigation.talk")}</a>
              <a href="#money" className="hover:text-leaf">{t("navigation.money")}</a>
              <a href="#goals" className="hover:text-leaf">{t("navigation.goals")}</a>
              <a href="#learn" className="hover:text-leaf">{t("navigation.learn")}</a>
              <a href="#stay-safe" className="hover:text-leaf">{t("navigation.staySafe")}</a>
            </div>
          </nav>
          <div className="order-2 flex items-center gap-2 md:order-3">
            <label className="text-sm font-medium">
              <span className="sr-only">{t("language.select")}</span>
              <select
                className="rounded-full border border-ink/15 bg-white px-3 py-2 outline-none focus:ring-2 focus:ring-leaf"
                aria-label={t("language.select")}
                value={language}
                onChange={(event) => void setLanguage(event.target.value as typeof language)}
              >
                <option value="en">{t("language.english")}</option>
                <option value="hi">{t("language.hindi")}</option>
                <option value="te">{t("language.telugu")}</option>
              </select>
            </label>
            <button
              className="rounded-full border border-ink/15 bg-white px-3 py-2 text-sm font-semibold hover:border-leaf focus:outline-none focus:ring-2 focus:ring-leaf"
              type="button"
              onClick={() => void linkGoogleAccount()}
            >
              {t("auth.linkGoogle")}
            </button>
            <button
              className="rounded-full border border-ink/15 bg-white px-3 py-2 text-sm font-semibold hover:border-leaf focus:outline-none focus:ring-2 focus:ring-leaf"
              type="button"
              onClick={() => void signOut()}
            >
              {t("auth.signOut")}
            </button>
          </div>
        </div>
      </header>

      <main id="home" className="mx-auto max-w-6xl px-6 py-12">
        <section className="grid gap-8 rounded-3xl bg-ink p-8 text-white md:grid-cols-[1.3fr_0.7fr] md:p-12">
          <div>
            <span className="inline-flex rounded-full bg-sun px-3 py-1 text-sm font-semibold text-ink">
              {t("dashboard.foundationReady")}
            </span>
            <h1 className="mt-6 max-w-xl text-4xl font-semibold tracking-tight md:text-6xl">
              {profile?.display_name ? t("dashboard.greeting") + ", " + profile.display_name : t("dashboard.greeting")}
            </h1>
            <p className="mt-5 max-w-lg text-lg leading-8 text-white/75">{t("dashboard.subtitle")}</p>
            <a
              className="mt-8 inline-flex rounded-full bg-sun px-5 py-3 font-semibold text-ink transition hover:bg-white focus:outline-none focus:ring-2 focus:ring-sun focus:ring-offset-2 focus:ring-offset-ink"
              href="#talk"
            >
              {t("conversation.talkToCompanion")}
            </a>
          </div>
          <div id="goals" className="flex items-end justify-end">
            <div className="w-full max-w-xs rounded-3xl border border-white/15 bg-white/10 p-6 backdrop-blur">
              <p className="text-sm text-white/65">{t("goals.nextGoal")}</p>
              <p className="mt-3 text-2xl font-semibold">{t("goals.sewingMachine")}</p>
              <div className="mt-5 h-2 rounded-full bg-white/15" aria-hidden="true">
                <div className="h-full w-1/3 rounded-full bg-sun" />
              </div>
              <p className="mt-3 text-sm text-white/65">{t("goals.progress", { current: "₹500", target: "₹15,000" })}</p>
            </div>
          </div>
        </section>

        <section className="mt-10" aria-labelledby="overview-heading">
          <div className="flex flex-wrap items-end justify-between gap-4">
            <div>
              <p className="text-sm font-semibold uppercase tracking-[0.2em] text-leaf">{t("dashboard.overview")}</p>
              <h2 id="overview-heading" className="mt-2 text-2xl font-semibold">{t("dashboard.overviewSubtitle")}</h2>
            </div>
            <button
              type="button"
              onClick={handleHealthCheck}
              className="rounded-full border border-ink/15 bg-white px-4 py-2 text-sm font-semibold hover:border-leaf focus:outline-none focus:ring-2 focus:ring-leaf"
            >
              {t("common.checkConnection")}
            </button>
          </div>
          <p className="mt-3 min-h-5 text-sm text-ink/60" role="status" aria-live="polite">
            {connection === "checking" && t("common.checking")}
            {connection === "connected" && t("common.apiConnected")}
            {connection === "error" && t("common.apiUnavailable")}
          </p>
          <div className="mt-5 grid gap-4 md:grid-cols-3">
            <StatusCard label={t("dashboard.income")} value="₹8,500" detail={t("dashboard.incomeDetail")} />
            <StatusCard label={t("dashboard.expenses")} value="₹5,200" detail={t("dashboard.expensesDetail")} />
            <StatusCard label={t("dashboard.savings")} value="₹3,300" detail={t("dashboard.savingsDetail")} />
          </div>
        </section>

        <section id="talk" className="mt-10 rounded-3xl border border-ink/10 bg-white p-6 shadow-sm" aria-labelledby="conversation-heading">
          <p className="text-sm font-semibold uppercase tracking-[0.2em] text-leaf">{t("navigation.talk")}</p>
          <h2 id="conversation-heading" className="mt-2 text-2xl font-semibold">{t("conversation.title")}</h2>
          <div className="mt-5 rounded-2xl bg-cream p-5">
            <p className="font-semibold">{t("conversation.listening")}</p>
            <p className="mt-2 text-ink/60">{t("conversation.empty")}</p>
            <button className="mt-5 rounded-full bg-ink px-4 py-2 text-sm font-semibold text-white hover:bg-leaf focus:outline-none focus:ring-2 focus:ring-leaf" type="button">
              {t("conversation.holdToSpeak")}
            </button>
          </div>
        </section>

        <section id="money" className="mt-10 rounded-3xl border border-ink/10 bg-white p-6 shadow-sm" aria-labelledby="money-heading">
          <h2 id="money-heading" className="text-2xl font-semibold">{t("navigation.money")}</h2>
          <p className="mt-3 text-ink/60">{t("money.emptyTransactions")}</p>
        </section>

        <section className="mt-10 grid gap-4 md:grid-cols-3">
          <article id="learn" className="rounded-2xl border border-ink/10 bg-white p-6 text-left shadow-sm">
            <span className="text-2xl" aria-hidden="true">📚</span>
            <h2 className="mt-4 text-xl font-semibold">{t("learn.title")}</h2>
            <p className="mt-2 text-ink/60">{t("learn.description")}</p>
          </article>
          <article id="stay-safe" className="rounded-2xl border border-ink/10 bg-white p-6 text-left shadow-sm">
            <span className="text-2xl" aria-hidden="true">🛡️</span>
            <h2 className="mt-4 text-xl font-semibold">{t("staySafe.title")}</h2>
            <p className="mt-2 text-ink/60">{t("staySafe.description")}</p>
          </article>
          <article className="rounded-2xl border border-ink/10 bg-white p-6 text-left shadow-sm" aria-labelledby="notifications-heading">
            <span className="text-2xl" aria-hidden="true">🔔</span>
            <h2 id="notifications-heading" className="mt-4 text-xl font-semibold">{t("notifications.title")}</h2>
            <p className="mt-2 text-ink/60">{t("notifications.empty")}</p>
          </article>
        </section>
      </main>
    </div>
  );
}

function DashboardRoute() {
  const { profile } = useAuth();
  const { t } = useI18n();
  if (!profile) return <div className="flex min-h-screen items-center justify-center bg-cream text-ink">{t("common.loadingProfile")}</div>;
  if (!profile.onboarding_completed) return <Navigate to="/onboarding" replace />;
  return <Dashboard />;
}

function OnboardingRoute() {
  const { profile } = useAuth();
  if (profile?.onboarding_completed) return <Navigate to="/" replace />;
  return <OnboardingPage />;
}

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<AuthPage />} />
        <Route
          path="/onboarding"
          element={
            <ProtectedRoute>
              <OnboardingRoute />
            </ProtectedRoute>
          }
        />
        <Route
          path="*"
          element={
            <ProtectedRoute>
              <DashboardRoute />
            </ProtectedRoute>
          }
        />
      </Routes>
    </BrowserRouter>
  );
}

export default App;

