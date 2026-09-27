import { BrowserRouter, Routes, Route } from "react-router-dom";
import { AccessibilityProvider } from "./context/AccessibilityContext";
import Layout from "./components/layout/Layout";
import DashboardPage from "./pages/Dashboard";
import VendasPage from "./pages/Vendas";
import DespesasPage from "./pages/Despesas";
import EstoquePage from "./pages/Estoque";
import EmpresaPage from "./pages/Empresa";
import VarejoPage from "./pages/Varejo";
import PrevisaoPage from "./pages/Previsao";

export default function App() {
  return (
    <AccessibilityProvider>
      <BrowserRouter>
        <Routes>
          <Route element={<Layout />}>
            <Route path="/" element={<DashboardPage />} />
            <Route path="/varejo" element={<VarejoPage />} />
            <Route path="/previsao" element={<PrevisaoPage />} />
            <Route path="/vendas" element={<VendasPage />} />
            <Route path="/despesas" element={<DespesasPage />} />
            <Route path="/estoque" element={<EstoquePage />} />
            <Route path="/empresa" element={<EmpresaPage />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </AccessibilityProvider>
  );
}
