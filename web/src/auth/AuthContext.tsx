import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import type { Session } from "@supabase/supabase-js";

import type { Profile, ProfileUpdateRequest, UserPreferences } from "@sahachari/contracts";

import { getAuthMe, updateAuthMe } from "../api/client";
import { supabase, supabaseConfigured } from "./supabase";

type AuthContextValue = {
  session: Session | null;
  profile: Profile | null;
  preferences: UserPreferences | null;
  loading: boolean;
  authError: string | null;
  signInWithPassword: (email: string, password: string) => Promise<void>;
  signUp: (email: string, password: string) => Promise<void>;
  signInWithGoogle: () => Promise<void>;
  linkGoogleAccount: () => Promise<void>;
  signOut: () => Promise<void>;
  saveProfile: (payload: ProfileUpdateRequest) => Promise<Profile>;
  refreshProfile: () => Promise<Profile | null>;
};

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

function configurationError() {
  return new Error("Supabase authentication is not configured. Add VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY.");
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [session, setSession] = useState<Session | null>(null);
  const [profile, setProfile] = useState<Profile | null>(null);
  const [preferences, setPreferences] = useState<UserPreferences | null>(null);
  const [loading, setLoading] = useState(true);
  const [authError, setAuthError] = useState<string | null>(null);

  async function loadProfile(nextSession: Session): Promise<Profile | null> {
    try {
      const response = await getAuthMe(nextSession.access_token);
      setProfile(response.profile);
      setPreferences(response.preferences);
      setAuthError(null);
      return response.profile;
    } catch (error) {
      setAuthError(error instanceof Error ? error.message : "Unable to load your profile.");
      return null;
    }
  }

  useEffect(() => {
    if (!supabase) {
      setLoading(false);
      return;
    }

    let active = true;
    void supabase.auth.getSession().then(async ({ data, error }) => {
      if (error) {
        setAuthError(error.message);
      }
      if (!active) return;
      setSession(data.session);
      if (data.session) {
        await loadProfile(data.session);
      }
      if (active) setLoading(false);
    });

    const { data } = supabase.auth.onAuthStateChange((_event, nextSession) => {
      setSession(nextSession);
      if (!nextSession) {
        setProfile(null);
        setPreferences(null);
        setLoading(false);
        return;
      }
      window.setTimeout(() => {
        void loadProfile(nextSession).finally(() => {
          if (active) setLoading(false);
        });
      }, 0);
    });

    return () => {
      active = false;
      data.subscription.unsubscribe();
    };
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({
      session,
      profile,
      preferences,
      loading,
      authError,
      async signInWithPassword(email, password) {
        if (!supabase) throw configurationError();
        const { error } = await supabase.auth.signInWithPassword({ email, password });
        if (error) throw error;
      },
      async signUp(email, password) {
        if (!supabase) throw configurationError();
        const { error } = await supabase.auth.signUp({
          email,
          password,
          options: { emailRedirectTo: window.location.origin },
        });
        if (error) throw error;
      },
      async signInWithGoogle() {
        if (!supabase) throw configurationError();
        const { error } = await supabase.auth.signInWithOAuth({
          provider: "google",
          options: { redirectTo: window.location.origin },
        });
        if (error) throw error;
      },
      async linkGoogleAccount() {
        if (!supabase) throw configurationError();
        const { error } = await supabase.auth.linkIdentity({
          provider: "google",
          options: { redirectTo: window.location.origin },
        });
        if (error) throw error;
      },
      async signOut() {
        if (!supabase) return;
        const { error } = await supabase.auth.signOut();
        if (error) throw error;
        setSession(null);
        setProfile(null);
        setPreferences(null);
      },
      async saveProfile(payload) {
        if (!session) throw new Error("Sign in before editing your profile.");
        const response = await updateAuthMe(session.access_token, payload);
        setProfile(response.profile);
        setPreferences(response.preferences);
        return response.profile;
      },
      async refreshProfile() {
        if (!session) return null;
        return loadProfile(session);
      },
    }),
    [authError, loading, preferences, profile, session],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth must be used inside AuthProvider.");
  return context;
}

export { supabaseConfigured };
