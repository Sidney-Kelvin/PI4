import { AlertTriangle, Info, RefreshCw, XCircle } from "lucide-react";

interface StateMessageProps {
  type?: "info" | "warning" | "error";
  title: string;
  message: string;
  command?: string;
  onRetry?: () => void;
}

const estilos = {
  info: { box: "bg-blue-50 border-blue-200 text-blue-900", icon: Info },
  warning: { box: "bg-amber-50 border-amber-200 text-amber-900", icon: AlertTriangle },
  error: { box: "bg-red-50 border-red-200 text-red-900", icon: XCircle },
};

/** Mensagem de estado (sem dados, sem modelo, erro da API) com comando sugerido e opção de tentar novamente. */
export default function StateMessage({ type = "info", title, message, command, onRetry }: StateMessageProps) {
  const { box, icon: Icon } = estilos[type];
  return (
    <div className={`border rounded-lg p-4 text-sm ${box}`} role={type === "error" ? "alert" : "status"}>
      <div className="flex gap-3">
        <Icon size={18} className="shrink-0 mt-0.5" aria-hidden="true" />
        <div className="flex-1 min-w-0">
          <p className="font-semibold">{title}</p>
          <p className="mt-1">{message}</p>
          {command && (
            <code className="block mt-2 px-3 py-2 rounded bg-gray-900 text-gray-100 text-xs overflow-x-auto">
              {command}
            </code>
          )}
          {onRetry && (
            <button
              onClick={onRetry}
              className="mt-3 inline-flex items-center gap-1.5 text-xs font-medium underline underline-offset-2"
            >
              <RefreshCw size={13} aria-hidden="true" /> Tentar novamente
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
