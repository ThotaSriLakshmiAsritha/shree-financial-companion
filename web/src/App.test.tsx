import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import App from "./App";
import { AuthProvider } from "./auth/AuthContext";
import { I18nProvider } from "./i18n";

vi.mock("./auth/supabase", () => ({
  supabase: null,
  supabaseConfigured: false,
}));

function renderApp() {
  return render(
    <AuthProvider>
      <I18nProvider>
        <App />
      </I18nProvider>
    </AuthProvider>,
  );
}

describe("App", () => {
  it("renders the accessible authentication shell", () => {
    renderApp();
    expect(screen.getByRole("heading", { name: /welcome back/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /continue with google/i })).toBeInTheDocument();
  });

  it("switches between sign-in and sign-up", () => {
    renderApp();
    fireEvent.click(screen.getByRole("button", { name: /new here/i }));
    expect(screen.getByRole("heading", { name: /create your account/i })).toBeInTheDocument();
  });

  it("localizes the authentication shell", () => {
    renderApp();
    fireEvent.change(screen.getByRole("combobox", { name: /choose language/i }), { target: { value: "te" } });
    expect(screen.getByRole("heading", { name: /మళ్లీ స్వాగతం/i })).toBeInTheDocument();
    expect(window.localStorage.getItem("sahachari.language")).toBe("te");
  });
});
