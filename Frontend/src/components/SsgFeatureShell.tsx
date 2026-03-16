import { ReactNode } from "react";

import NavbarSSG from "./NavbarSSG";
import NavbarSG from "./NavbarSG";
import NavbarORG from "./NavbarORG";
import { GovernanceUnitType } from "../api/governanceHierarchyApi";
import "../css/SsgWorkspace.css";
import "../css/SsgFeatureShell.css";

export interface SsgFeatureStat {
  label: string;
  value: string | number;
  hint: string;
}

interface SsgFeatureShellProps {
  eyebrow: string;
  title: string;
  description: string;
  stats: SsgFeatureStat[];
  actions?: ReactNode;
  children: ReactNode;
  unitType?: GovernanceUnitType;
}

export const SsgFeatureShell = ({
  eyebrow,
  title,
  description,
  stats,
  actions,
  children,
  unitType = "SSG",
}: SsgFeatureShellProps) => {
  const navbar =
    unitType === "ORG" ? <NavbarORG /> : unitType === "SG" ? <NavbarSG /> : <NavbarSSG />;

  return (
    <div className="ssg-workspace-page">
      {navbar}

      <main className="container py-4 ssg-workspace-main">
        <section className="ssg-page-header">
          <div className="ssg-page-header__copy">
            <p className="ssg-page-eyebrow">{eyebrow}</p>
            <h1>{title}</h1>
            <p>{description}</p>
          </div>
          {actions ? <div className="ssg-page-actions">{actions}</div> : null}
        </section>

        <section className="ssg-stat-grid">
          {stats.map((stat) => (
            <article key={stat.label} className="ssg-stat-card">
              <span className="ssg-stat-card__label">{stat.label}</span>
              <strong className="ssg-stat-card__value">{stat.value}</strong>
              <span className="ssg-stat-card__hint">{stat.hint}</span>
            </article>
          ))}
        </section>

        {children}
      </main>
    </div>
  );
};

export default SsgFeatureShell;
