import { BrowserRouter, Routes, Route } from "react-router-dom";
import LoginPage from "./pages/LoginPage/LoginPage";
import Dashboard from "./pages/Dashboard/Dashboard";
import RepoDetails from "./pages/RepoDetails/RepoDetails";
import ProtectedRoute from "./components/ProtectedRoute";

export default function App() {
  return (
    <BrowserRouter basename="/system-dependency-explorer">
      <Routes>

        <Route path="/login" element={<LoginPage />} />

        <Route
          path="/dashboard"
          element={
            <ProtectedRoute>
              <Dashboard />
            </ProtectedRoute>
          }
        />

        <Route
          path="/repo-details/:repoId"
          element={
            <ProtectedRoute>
              <RepoDetails />
            </ProtectedRoute>
          }
        />

        <Route path="*" element={<LoginPage />} />

      </Routes>
    </BrowserRouter>
  );
}

