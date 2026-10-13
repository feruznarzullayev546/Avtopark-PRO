import type { ReactNode } from "react";

export type StatusOption = { value: string; label: string; count?: number; icon?: ReactNode };
export function StatusPills({ options, value, onChange, label = "Holat bo‘yicha filtrlash" }: {
  options: StatusOption[]; value: string; onChange: (value: string) => void; label?: string;
}) {
  return <div className="ap-status-pills" role="group" aria-label={label}>{options.map(option => <button key={option.value} type="button" className={`ap-status-pill${value === option.value ? " is-active" : ""}`} aria-pressed={value === option.value} onClick={() => onChange(option.value)}>{option.icon}{option.label}{option.count !== undefined && <span>{option.count}</span>}</button>)}</div>;
}
