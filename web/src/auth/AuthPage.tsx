import { FormEvent, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import { useAuth } from "./AuthContext";
import { useI18n } from "../i18n";

export function AuthPage() {
  const navigate = useNavigate();
  const { session, signInWithPassword, signUp, signInWithGoogle, authError } = useAuth();
  const { t, language, setLanguage } = useI18n();
  const [mode, setMode] = useState<"login" | "signup">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    if (session) navigate("/", { replace: true });
  }, [navigate, session]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setMessage("");
    try {
      if (mode === "login") {
        await signInWithPassword(email, password);
      } else {
        await signUp(email, password);
        setMessage(t("auth.accountCreated"));
      }
    } catch {
      setError(t("errors.authentication"));
    }
  }

  async function handleGoogle() {
    setError("");
    try {
      await signInWithGoogle();
    } catch {
      setError(t("errors.authentication"));
    }
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-cream px-6 py-12 text-ink">
      <section className="w-full max-w-md rounded-3xl border border-ink/10 bg-white p-8 shadow-sm">
        <div className="flex items-center justify-between">
          <p className="text-xl font-semibold tracking-tight">
            sahachari<span className="text-leaf">.</span>
          </p>
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
        </div>
        <h1 className="mt-10 text-3xl font-semibold">
          {mode === "login" ? t("auth.welcomeBack") : t("auth.createAccount")}
        </h1>
        <p className="mt-3 text-ink/60">
          {mode === "login" ? t("auth.signInDescription") : t("auth.signUpDescription")}
        </p>

        <button
          className="mt-8 w-full rounded-full border border-ink/15 px-4 py-3 font-semibold hover:border-leaf focus:outline-none focus:ring-2 focus:ring-leaf"
          type="button"
          onClick={handleGoogle}
        >
          {t("auth.continueWithGoogle")}
        </button>

        <div className="my-6 flex items-center gap-3 text-xs uppercase tracking-[0.2em] text-ink/40">
          <span className="h-px flex-1 bg-ink/10" />
          <span>{t("auth.orEmail")}</span>
          <span className="h-px flex-1 bg-ink/10" />
        </div>

        <form className="space-y-4" onSubmit={handleSubmit}>
          <label className="block text-sm font-medium">
            {t("auth.email")}
            <input
              className="mt-2 w-full rounded-xl border border-ink/15 px-4 py-3 outline-none focus:ring-2 focus:ring-leaf"
              type="email"
              autoComplete="email"
              required
              value={email}
              onChange={(event) => setEmail(event.target.value)}
            />
          </label>
          <label className="block text-sm font-medium">
            {t("auth.password")}
            <input
              className="mt-2 w-full rounded-xl border border-ink/15 px-4 py-3 outline-none focus:ring-2 focus:ring-leaf"
              type="password"
              autoComplete={mode === "login" ? "current-password" : "new-password"}
              minLength={6}
              required
              value={password}
              onChange={(event) => setPassword(event.target.value)}
            />
          </label>
          {(error || authError) && (
            <p className="rounded-xl bg-red-50 px-4 py-3 text-sm text-red-800" role="alert">
              {error || t("errors.sessionRestore")}
            </p>
          )}
          {message && (
            <p className="rounded-xl bg-leaf/10 px-4 py-3 text-sm text-leaf" role="status">
              {message}
            </p>
          )}
          <button className="w-full rounded-full bg-ink px-4 py-3 font-semibold text-white hover:bg-leaf focus:outline-none focus:ring-2 focus:ring-leaf" type="submit">
            {mode === "login" ? t("auth.signIn") : t("auth.createAccountButton")}
          </button>
        </form>

        <button
          className="mt-6 text-sm font-semibold text-leaf underline-offset-4 hover:underline"
          type="button"
          onClick={() => {
            setMode(mode === "login" ? "signup" : "login");
            setError("");
            setMessage("");
          }}
        >
          {mode === "login" ? t("auth.newHere") : t("auth.alreadyHaveAccount")}
        </button>
      </section>
    </main>
  );
}

