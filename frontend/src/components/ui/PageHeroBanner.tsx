import type { ReactNode } from "react";
import { ChevronRight, RefreshCw, Plus } from "lucide-react";

type Crumb = { label: string; href?: string };
type Props = {
  title: string; description: string; icon?: ReactNode; crumbs?: Crumb[];
  imageUrl?: string; createLabel?: string; onCreate?: () => void; onRefresh?: () => void;
  refreshing?: boolean; extraActions?: ReactNode;
};

/** Reusable page header. Supply a module-specific image and action callbacks. */
export function PageHeroBanner({
  title, description, icon, crumbs = [{ label: "Bosh sahifa", href: "/" }],
  imageUrl = "https://images.unsplash.com/photo-1519003722824-194d4455a60c?auto=format&fit=crop&w=1800&q=85",
  createLabel, onCreate, onRefresh, refreshing = false, extraActions,
}: Props) {
  return <section className="ap-page-hero" style={{ backgroundImage: `linear-gradient(90deg,rgba(3,17,43,.94) 0%,rgba(9,39,83,.82) 55%,rgba(10,38,80,.5) 100%),url("${imageUrl}")` }}>
    <div className="ap-page-hero__content">
      <nav className="ap-breadcrumbs" aria-label="Breadcrumb">{crumbs.map((c, i) => <span className="ap-breadcrumbs__item" key={`${c.label}-${i}`}>{c.href ? <a href={c.href}>{c.label}</a> : <span aria-current="page">{c.label}</span>}{i < crumbs.length - 1 && <ChevronRight size={13} aria-hidden="true" />}</span>)}</nav>
      <div className="ap-page-hero__title-row">{icon && <span className="ap-page-hero__icon">{icon}</span>}<div><h1>{title}</h1><p>{description}</p></div></div>
    </div>
    <div className="ap-page-hero__actions">{extraActions}{onRefresh && <button className="ap-btn ap-btn--ghost" type="button" onClick={onRefresh} disabled={refreshing}><RefreshCw size={16} className={refreshing ? "ap-spin" : ""}/><span>Yangilash</span></button>}{onCreate && <button className="ap-btn ap-btn--primary" type="button" onClick={onCreate}><Plus size={17}/><span>{createLabel || `Yangi ${title.toLowerCase()}`}</span></button>}</div>
  </section>;
}
