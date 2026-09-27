import type { ElementType, ReactNode } from "react";

export interface StatCardProps {
  title: string;
  value: string;
  icon: ElementType;
  color: string;
  bg: string;
  hint?: ReactNode;
}

export default function StatCard({ title, value, icon: Icon, color, bg, hint }: StatCardProps) {
  return (
    <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-5 flex items-center gap-4">
      <div className={`p-3 rounded-lg ${bg}`}>
        <Icon size={22} className={color} aria-hidden="true" />
      </div>
      <div className="min-w-0">
        <p className="text-xs text-gray-500 font-medium">{title}</p>
        <p className="text-xl font-bold text-gray-800 mt-0.5 truncate">{value}</p>
        {hint && <div className="text-xs text-gray-500 mt-0.5">{hint}</div>}
      </div>
    </div>
  );
}
