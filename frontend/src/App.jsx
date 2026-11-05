import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import AppLayout from './layouts/AppLayout';

// Pages
import SecurityOverview from './pages/SecurityOverview';
import ScansList from './pages/ScansList';
import NewScan from './pages/NewScan';
import ScanDetail from './pages/ScanDetail';
import FindingsList from './pages/FindingsList';
import FindingDetail from './pages/FindingDetail';
import VerificationDetail from './pages/VerificationDetail';
import PatchesList from './pages/PatchesList';
import PatchReview from './pages/PatchReview';
import DiffViewerPage from './pages/DiffViewerPage';
import RepositoriesList from './pages/RepositoriesList';
import RepositoryDetail from './pages/RepositoryDetail';
import TopologyPage from './pages/TopologyPage';
import CodeViewPage from './pages/CodeViewPage';
import OperationsMetricsPage from './pages/OperationsMetricsPage';
import MethodPage from './pages/MethodPage';
import SettingsPage from './pages/SettingsPage';

export default function App() {
  return (
    <Router>
      <AppLayout>
        <Routes>
          {/* Dashboard / Security Overview */}
          <Route path="/" element={<SecurityOverview />} />

          {/* Operations: Scans & Execution */}
          <Route path="/scans" element={<ScansList />} />
          <Route path="/scans/new" element={<NewScan />} />
          <Route path="/scans/:id" element={<ScanDetail />} />

          {/* Intelligence: Findings & Evidence */}
          <Route path="/findings" element={<FindingsList />} />
          <Route path="/findings/:id" element={<FindingDetail />} />
          <Route path="/verification/:id" element={<VerificationDetail />} />

          {/* Intelligence: Patches & Diffs */}
          <Route path="/patches" element={<PatchesList />} />
          <Route path="/patches/:id" element={<PatchReview />} />
          <Route path="/patches/:id/diff" element={<DiffViewerPage />} />

          {/* Intelligence: Repositories & Graph */}
          <Route path="/repositories" element={<RepositoriesList />} />
          <Route path="/repositories/:id" element={<RepositoryDetail />} />
          <Route path="/topology" element={<TopologyPage />} />
          <Route path="/code" element={<CodeViewPage />} />

          {/* Analysis & System */}
          <Route path="/metrics" element={<OperationsMetricsPage />} />
          <Route path="/method" element={<MethodPage />} />
          <Route path="/settings" element={<SettingsPage />} />

          {/* Fallback */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AppLayout>
    </Router>
  );
}
