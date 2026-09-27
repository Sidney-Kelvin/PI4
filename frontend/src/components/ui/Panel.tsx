import type { ReactNode } from "react";

interface PanelProps {
  title: string;
  subtitle?: ReactNode;
  actions?: ReactNode;
  children: ReactNode;
  className?: string;
}

export default function Panel({ title, subtitle, actions, children, className = "" }: PanelProps) {
  return (
    <section className={`bg-white rounded-xl border border-gray-100 shadow-sm p-5 ${className}`}>
      <div className="flex flex-wrap items-start justify-between gap-3 mb-4">
        <div>
          <h3 className="text-sm font-semibold text-gray-800 uppercase tracking-wide">{title}</h3>
          {subtitle && <p className="text-xs text-gray-500 mt-1">{subtitle}</p>}
        </div>
        {actions}
      </div>
      {children}
    </section>
  );
}
