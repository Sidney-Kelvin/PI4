import { NavLink } from "react-router-dom";
import {
  LayoutDashboard,
  ShoppingCart,
  TrendingDown,
  Package,
  Building2,
  BarChart3,
  BrainCircuit,
} from "lucide-react";

const links = [
  { to: "/", label: "Dashboard", icon: LayoutDashboard },
  { to: "/varejo", label: "Histórico de Varejo", icon: BarChart3 },
  { to: "/previsao", label: "Previsão (LSTM)", icon: BrainCircuit },
  { to: "/vendas", label: "Vendas", icon: ShoppingCart },
  { to: "/despesas", label: "Despesas", icon: TrendingDown },
  { to: "/estoque", label: "Estoque", icon: Package },
  { to: "/empresa", label: "Empresa", icon: Building2 },
];

export default function Sidebar() {
  return (
    <aside className="w-64 min-h-screen bg-gray-900 text-white flex flex-col" aria-label="Menu principal">
      <div className="px-6 py-6 border-b border-gray-700">
        <h1 className="text-xl font-bold tracking-tight">Pi3 Gestão</h1>
        <p className="text-xs text-gray-400 mt-0.5">Controle financeiro</p>
      </div>

      <nav className="flex-1 px-3 py-4 space-y-1" aria-label="Navegação">
        {links.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            end={to === "/"}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                isActive
                  ? "bg-blue-600 text-white"
                  : "text-gray-300 hover:bg-gray-800 hover:text-white"
              }`
            }
          >
            <Icon size={18} aria-hidden="true" />
            {label}
          </NavLink>
        ))}
      </nav>

      <div className="px-6 py-4 border-t border-gray-700">
        <p className="text-xs text-gray-500">v1.0.0</p>
      </div>
    </aside>
  );
}
