import { createClient } from "@supabase/supabase-js";

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL || "https://oqknqbpaqpwjimpngnyx.supabase.co";
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY || "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im9xa25xYnBhcXB3amltcG5nbnl4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODk3MzU1ODAsImV4cCI6MjEwNTMxMTU4MH0.j2FICCBLxfeo48Cqe8SsLMVTMIDcD1n1p_FF9_0q5Os";

export const supabaseConfigured = Boolean(supabaseUrl && supabaseAnonKey);

export const supabase = supabaseConfigured
  ? createClient(supabaseUrl!, supabaseAnonKey!, {
      auth: {
        persistSession: true,
        autoRefreshToken: true,
        detectSessionInUrl: true,
      },
    })
  : null;

