import { Link, Navigate, Route, Routes } from "react-router-dom";
import { useAuth } from "./context/AuthContext";
import ProtectedRoute from "./components/ProtectedRoute";
import LoginPage from "./pages/LoginPage";
import RegisterPage from "./pages/RegisterPage";
import PlantListPage from "./pages/PlantListPage";
import PlantNewPage from "./pages/PlantNewPage";
import PlantDetailPage from "./pages/PlantDetailPage";

function NavBar() {
  const { user, logout } = useAuth();
  if (!user) return null;
  return (
    <nav className="navbar">
      <Link to="/plants">Plant Tracker</Link>
      <div className="navbar-right">
        <span>{user.display_name || user.email}</span>
        <button onClick={logout}>Log out</button>
      </div>
    </nav>
  );
}

export default function App() {
  return (
    <>
      <NavBar />
      <main>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
          <Route element={<ProtectedRoute />}>
            <Route path="/plants" element={<PlantListPage />} />
            <Route path="/plants/new" element={<PlantNewPage />} />
            <Route path="/plants/:id" element={<PlantDetailPage />} />
          </Route>
          <Route path="/" element={<Navigate to="/plants" replace />} />
        </Routes>
      </main>
    </>
  );
}
