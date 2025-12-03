import React from "react";
import {
  BrowserRouter as Router,
  Routes,
  Route,
  Navigate,
} from "react-router-dom";
import MainLayout from "@/layout/MainLayout";
import ChatPage from "@/pages/Chat";
import ProjectsPage from "@/pages/Projects";
import ReportsPage from "@/pages/Reports";
import SettingsPage from "@/pages/Settings";
import AdminDashboard from "@/pages/AdminDashboard";
import PdfViewerModal from "@/components/modals/PdfViewerModal";
import CsvViewerModal from "@/components/modals/CsvViewerModal";
import ExpertGraphModal from "@/components/modals/ExpertGraphModal";

function App() {
  return (
    <Router>
      <Routes>
        {/* All routes are now public - no authentication required */}
        <Route
          path="/"
          element={
            <MainLayout currentPageName="Chat">
              <ChatPage />
            </MainLayout>
          }
        />
        <Route
          path="/chat"
          element={
            <MainLayout currentPageName="Chat">
              <ChatPage />
            </MainLayout>
          }
        />
        <Route
          path="/chat/:id"
          element={
            <MainLayout currentPageName="Chat">
              <ChatPage />
            </MainLayout>
          }
        />
        <Route
          path="/projects"
          element={
            <MainLayout currentPageName="Projects">
              <ProjectsPage />
            </MainLayout>
          }
        />
        <Route
          path="/reports"
          element={
            <MainLayout currentPageName="Reports">
              <ReportsPage />
            </MainLayout>
          }
        />
        <Route
          path="/settings"
          element={
            <MainLayout currentPageName="Settings">
              <SettingsPage />
            </MainLayout>
          }
        />
        <Route
          path="/admin"
          element={
            <MainLayout currentPageName="Admin">
              <AdminDashboard />
            </MainLayout>
          }
        />

        {/* Default redirect */}
        <Route path="*" element={<Navigate to="/chat" replace />} />
      </Routes>

      {/* Global Modals */}
      <PdfViewerModal />
      <CsvViewerModal />
      <ExpertGraphModal />
    </Router>
  );
}

export default App;
