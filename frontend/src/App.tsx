import React, { useEffect, useState, Component, ReactNode, lazy, Suspense } from "react";
import { BrowserRouter, Routes as RouterRoutes, Route } from "react-router-dom";
import { AppShell } from "./layouts/AppShell";
import { Login } from "./components/Login";
import { I18nProvider } from "./i18n";
import { api } from "./services/api";
import type { Me } from "./types/api";

import "./styles/global.css";
import "./styles/design-overhaul.css";
import "./styles/premium-v77.css";
import "./styles/reference-dashboard.css";
import "./styles/layout-fix.css";
import "./styles/avtopark-design-system.css";
import "./styles/ui-components.css"
import "./styles/auth-layout-fix.css";

const Dashboard = lazy(() => import("./pages/Dashboard").then(m => ({ default: m.Dashboard })));
const DriverHome = lazy(() => import("./pages/DriverHome").then(m => ({ default: m.DriverHome })));
const Vehicles = lazy(() => import("./pages/Fleet").then(m => ({ default: m.Vehicles })));
const Drivers = lazy(() => import("./pages/Fleet").then(m => ({ default: m.Drivers })));
const Trips = lazy(() => import("./pages/Trips").then(m => ({ default: m.Trips })));
const RoutesPage = lazy(() => import("./pages/Routes").then(m => ({ default: m.RoutesPage })));
const Notifications = lazy(() => import("./pages/Notifications").then(m => ({ default: m.Notifications })));
const Companies = lazy(() => import("./pages/Companies").then(m => ({ default: m.Companies })));
const FuelPage = lazy(() => import("./pages/Fuel").then(m => ({ default: m.FuelPage })));
const Warehouse = lazy(() => import("./pages/Warehouse").then(m => ({ default: m.Warehouse })));
const Maintenance = lazy(() => import("./pages/Maintenance").then(m => ({ default: m.Maintenance })));
const Replacements = lazy(() => import("./pages/Replacements").then(m => ({ default: m.Replacements })));
const Finance = lazy(() => import("./pages/Finance").then(m => ({ default: m.Finance })));
const AccessControl = lazy(() => import("./pages/AccessControl").then(m => ({ default: m.AccessControl })));
const Enterprise = lazy(() => import("./pages/Enterprise").then(m => ({ default: m.Enterprise })));
const Billing = lazy(() => import("./pages/Billing").then(m => ({ default: m.Billing })));
const Platform = lazy(() => import("./pages/Platform").then(m => ({ default: m.Platform })));
const Settings = lazy(() => import("./pages/Settings").then(m => ({ default: m.Settings })));
const Chat = lazy(() => import("./pages/Chat").then(m => ({ default: m.Chat })));
const Reports = lazy(() => import("./pages/Reports").then(m => ({ default: m.Reports })));

// === XATO USHLAGICH (ErrorBoundary) ===
class ErrorBoundary extends Component<{ children: ReactNode }, { error: Error | null }> {
  state = { error: null as Error | null };
  static getDerivedStateFromError(error: Error) { return { error }; }
  componentDidCatch(error: Error, info: any) { console.error("Sahifa xatosi:", error, info); }
  render() {
    if (this.state.error) {
      return (
        <div style={{ padding: 24, fontFamily: "sans-serif" }}>
          <h2 style={{ color: "#c0392b" }}>Sahifada xatolik yuz berdi</h2>
          <pre style={{ background: "#f5f5f5", padding: 12, borderRadius: 6, overflow: "auto" }}>
            {this.state.error.message}
          </pre>
          <button onClick={() => this.setState({ error: null })} style={{ padding: "8px 16px", cursor: "pointer" }}>
            Qayta urinish
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}

export function App() {
  const [me, setMe] = useState<Me | null>(null);
  const [checking, setChecking] = useState(true);

  const refresh = () => {
    setChecking(true);
    api.me()
      .then(setMe)
      .catch(() => setMe({ authenticated: false }))
      .finally(() => setChecking(false));
  };

  useEffect(refresh, []);

  if (checking) return <div className="loading-screen"><span className="spinner" />Yuklanmoqda...</div>;
  if (!me?.authenticated) return <Login onSuccess={refresh} />;

  return (
    <I18nProvider>
      <BrowserRouter>
        <AppShell me={me} onLogout={refresh}>
          <ErrorBoundary>
            <Suspense fallback={<div className="loading-screen"><span className="spinner" />Yuklanmoqda...</div>}>
              <RouterRoutes>
                <Route path="/" element={me.is_super ? <Platform /> : me.user?.role === "DRIVER" ? <DriverHome /> : <Dashboard />} />
                <Route path="/vehicles" element={<Vehicles />} />
                <Route path="/trips" element={<Trips />} />
                <Route path="/routes" element={<RoutesPage />} />
                <Route path="/drivers" element={<Drivers />} />
                <Route path="/warehouse" element={<Warehouse />} />
                <Route path="/maintenance" element={<Maintenance />} />
                <Route path="/replacements" element={<Replacements />} />
                <Route path="/fuel" element={<FuelPage />} />
                <Route path="/finance" element={<Finance />} />
                <Route path="/reports" element={<Reports />} />
                <Route path="/notifications" element={<Notifications />} />
                <Route path="/companies" element={<Companies />} />
                <Route path="/access" element={<AccessControl />} />
                <Route path="/enterprise" element={<Enterprise />} />
                <Route path="/billing" element={<Billing />} />
                <Route path="/platform" element={<Platform />} />
                <Route path="/settings" element={<Settings />} />
                <Route path="/chat" element={<Chat />} />
              </RouterRoutes>
            </Suspense>
          </ErrorBoundary>
        </AppShell>
      </BrowserRouter>
    </I18nProvider>
  );
}

export default App;
