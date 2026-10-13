import type { ReactNode } from "react";

type Column<T> = { key: keyof T; label: string; render?: (row: T) => ReactNode; primary?: boolean };
/** Shows a conventional table on desktop and accessible card stack on small screens. */
export function ResponsiveDataList<T extends { id: string | number }>({ rows, columns, getTitle, getSubtitle }: {
  rows: T[]; columns: Column<T>[]; getTitle: (row: T) => ReactNode; getSubtitle?: (row: T) => ReactNode;
}) {
  return <div className="ap-responsive-data">
    <div className="ap-data-table-wrap"><table className="ap-data-table"><thead><tr>{columns.map(c => <th key={String(c.key)}>{c.label}</th>)}</tr></thead><tbody>{rows.map(row => <tr key={row.id}>{columns.map(c => <td key={String(c.key)}>{c.render ? c.render(row) : String(row[c.key] ?? "—")}</td>)}</tr>)}</tbody></table></div>
    <div className="ap-data-cards">{rows.map(row => <article className="ap-data-card" key={row.id}><header><strong>{getTitle(row)}</strong>{getSubtitle && <span>{getSubtitle(row)}</span>}</header><dl>{columns.filter(c => !c.primary).map(c => <div key={String(c.key)}><dt>{c.label}</dt><dd>{c.render ? c.render(row) : String(row[c.key] ?? "—")}</dd></div>)}</dl></article>)}</div>
    {!rows.length && <div className="ap-data-empty">Ma’lumot topilmadi.</div>}
  </div>;
}
