import { Outlet, useLocation } from "react-router-dom";
import Sidebar from "./Sidebar";
import Header from "./Header";
import { useAccessibility } from "../../context/AccessibilityContext";

const pageTitles: Record<string, string> = {
  "/": "Dashboard",
  "/varejo": "Histórico de Varejo",
  "/previsao": "Previsão de Vendas (LSTM)",
  "/vendas": "Vendas",
  "/despesas": "Despesas",
  "/estoque": "Estoque",
  "/empresa": "Consulta Empresa",
};

export default function Layout() {
  const { colorFilter } = useAccessibility();
  const location = useLocation();
  const title = pageTitles[location.pathname] ?? "FinanTrack";

  return (
    <>
      {/* Acessibilidade: pula para o conteúdo principal */}
      <a href="#main-content" className="skip-nav">
        Pular para o conteúdo
      </a>

      {/* Filtros SVG para daltonismo */}
      <svg aria-hidden="true" className="absolute w-0 h-0">
        <defs>
          <filter id="protanopia">
            <feColorMatrix type="matrix" values="0.567,0.433,0,0,0 0.558,0.442,0,0,0 0,0.242,0.758,0,0 0,0,0,1,0" />
          </filter>
          <filter id="deuteranopia">
            <feColorMatrix type="matrix" values="0.625,0.375,0,0,0 0.7,0.3,0,0,0 0,0.3,0.7,0,0 0,0,0,1,0" />
          </filter>
          <filter id="tritanopia">
            <feColorMatrix type="matrix" values="0.95,0.05,0,0,0 0,0.433,0.567,0,0 0,0.475,0.525,0,0 0,0,0,1,0" />
          </filter>
        </defs>
      </svg>

      <div
        className={`flex min-h-screen ${
          colorFilter !== "none" ? `filter-${colorFilter}` : ""
        }`}
      >
        <Sidebar />
        <div className="flex-1 flex flex-col">
          <Header title={title} />
          <main id="main-content" className="flex-1 p-6 bg-gray-50" tabIndex={-1}>
            <Outlet />
          </main>
        </div>
      </div>
    </>
  );
}
