import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { CanteenProvider } from './context/CanteenContext';
import { Sidebar } from './components/layout/Sidebar';
import { Header } from './components/layout/Header';

import { DashboardPage } from './pages/DashboardPage';
import { AnalyticsCalendarPage } from './pages/AnalyticsCalendarPage';
import { ForecastingPage } from './pages/ForecastingPage';
import { MenuOptimizerPage } from './pages/MenuOptimizerPage';
import { SurplusFoodPage } from './pages/SurplusFoodPage';
import { SurplusMarketplacePage } from './pages/SurplusMarketplacePage';
import { InventoryPage } from './pages/InventoryPage';
import { ReportsPage } from './pages/ReportsPage';
import { SettingsPage } from './pages/SettingsPage';

// Standard App Shell Layout with Sidebar and Header
const AppShell: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  return (
    <div className="app-container">
      <Sidebar />
      <div className="app-main">
        <Header />
        <main>{children}</main>
      </div>
    </div>
  );
};

export const App: React.FC = () => {
  return (
    <CanteenProvider>
      <BrowserRouter>
        <Routes>
          {/* Public Student-Facing Surplus Marketplace (Without Manager Sidebar) */}
          <Route path="/surplus-marketplace" element={<SurplusMarketplacePage />} />

          {/* Authenticated Manager SaaS Shell Routes */}
          <Route
            path="/dashboard"
            element={
              <AppShell>
                <DashboardPage />
              </AppShell>
            }
          />
          <Route
            path="/analytics-calendar"
            element={
              <AppShell>
                <AnalyticsCalendarPage />
              </AppShell>
            }
          />
          <Route
            path="/forecasting"
            element={
              <AppShell>
                <ForecastingPage />
              </AppShell>
            }
          />
          <Route
            path="/menu-optimizer"
            element={
              <AppShell>
                <MenuOptimizerPage />
              </AppShell>
            }
          />
          <Route
            path="/surplus-food"
            element={
              <AppShell>
                <SurplusFoodPage />
              </AppShell>
            }
          />
          <Route
            path="/inventory"
            element={
              <AppShell>
                <InventoryPage />
              </AppShell>
            }
          />
          <Route
            path="/reports"
            element={
              <AppShell>
                <ReportsPage />
              </AppShell>
            }
          />
          <Route
            path="/settings"
            element={
              <AppShell>
                <SettingsPage />
              </AppShell>
            }
          />

          {/* Root Redirect */}
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </BrowserRouter>
    </CanteenProvider>
  );
};

export default App;
