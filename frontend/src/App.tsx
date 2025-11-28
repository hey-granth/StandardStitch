import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import { Layout } from './components/Layout';
import { Login } from './pages/Login';
import { Signup } from './pages/Signup';
import { RoleSelection } from './pages/RoleSelection';
import { VendorOnboard } from './pages/VendorOnboard';
import { SchoolList } from './pages/SchoolList';
import { SchoolDetails } from './pages/SchoolDetails';
import { Cart } from './pages/Cart';
import { Orders } from './pages/Orders';
import { VendorDashboard } from './pages/VendorDashboard';
import { AdminDashboard } from './pages/AdminDashboard';

const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { user, isLoading } = useAuth();
  if (isLoading) return <div>Loading...</div>;
  if (!user) return <Navigate to="/login" />;
  return <>{children}</>;
};

const AppRoutes: React.FC = () => {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/signup" element={<Signup />} />

      <Route path="/" element={
        <ProtectedRoute>
          <Navigate to="/role-selection" replace />
        </ProtectedRoute>
      } />

      <Route path="/role-selection" element={
        <ProtectedRoute>
          <Layout><RoleSelection /></Layout>
        </ProtectedRoute>
      } />

      <Route path="/schools" element={<Layout><SchoolList /></Layout>} />
      <Route path="/schools/:id" element={<Layout><SchoolDetails /></Layout>} />

      <Route path="/vendor/onboard" element={
        <ProtectedRoute>
          <Layout><VendorOnboard /></Layout>
        </ProtectedRoute>
      } />

      <Route path="/cart" element={
        <ProtectedRoute>
          <Layout><Cart /></Layout>
        </ProtectedRoute>
      } />

      <Route path="/orders" element={
        <ProtectedRoute>
          <Layout><Orders /></Layout>
        </ProtectedRoute>
      } />

      <Route path="/vendor/dashboard" element={
        <ProtectedRoute>
          <Layout><VendorDashboard /></Layout>
        </ProtectedRoute>
      } />

      <Route path="/admin" element={
        <ProtectedRoute>
          <Layout><AdminDashboard /></Layout>
        </ProtectedRoute>
      } />
    </Routes>
  );
};

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <AppRoutes />
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
