import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuth } from './api/auth'
import Home from './pages/Home'
import Reports from './pages/Reports'
import Integrations from './pages/Integrations'
import Clients from './pages/Clients'
import Login from './pages/Login'
import Layout from './components/Layout'

function PrivateRoute({ children }: { children: React.ReactNode }) {
  const { token } = useAuth()
  return token ? <>{children}</> : <Navigate to="/login" replace />
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route
        path="/"
        element={
          <PrivateRoute>
            <Layout />
          </PrivateRoute>
        }
      >
        <Route index element={<Home />} />
        <Route path="clients" element={<Clients />} />
        <Route path="reports" element={<Reports />} />
        <Route path="integrations" element={<Integrations />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
