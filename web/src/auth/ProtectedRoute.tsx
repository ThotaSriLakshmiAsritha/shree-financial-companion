import type { ReactNode } from "react";
import { Navigate } from "react-router-dom";

import { useAuth } from "./AuthContext";
import { useI18n } from "../i18n";

export function ProtectedRoute({ children }: { children: ReactNode }) {
  const { loading, session } = useAuth();
  const { t } = useI18n();
  if (loading) {
    return <div className="flex min-h-screen items-center justify-center bg-cream text-ink">{t("common.restoringSession")}</div>;
  }
  if (!session) return <Navigate to="/login" replace />;
  return <>{children}</>;
}
