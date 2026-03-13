import React from "react";
import { Link } from "react-router-dom";

import "../css/DashboardHomeLayout.css";

export interface DashboardCardItem {
  title: string;
  description: string;
  icon: React.ReactNode;
  link: string;
}

interface DashboardHomeLayoutProps {
  navbar: React.ReactNode;
  title: string;
  description: string;
  cards: DashboardCardItem[];
  logoSrc?: string | null;
  logoAlt?: string;
}

export const DashboardHomeLayout: React.FC<DashboardHomeLayoutProps> = ({
  navbar,
  title,
  description,
  cards,
  logoSrc,
  logoAlt = "Dashboard logo",
}) => {
  return (
    <div className="dashboard-home">
      {navbar}

      <main className="dashboard-home__main">
        <section className="dashboard-home__hero">
          {logoSrc ? (
            <img
              src={logoSrc}
              alt={logoAlt}
              className="dashboard-home__hero-logo"
            />
          ) : null}
          <h1 className="dashboard-home__title">{title}</h1>
          <p className="dashboard-home__description">{description}</p>
        </section>

        <section className="dashboard-home__cards container-fluid px-0">
          <div className="row row-cols-1 row-cols-sm-2 row-cols-xl-3 g-4">
            {cards.map((card) => (
              <div className="col" key={card.link}>
                <Link
                  to={card.link}
                  className="dashboard-home__card-link"
                >
                  <article className="dashboard-home__card card h-100 border-0 shadow-sm">
                    <div className="card-body d-flex flex-column align-items-start gap-3">
                      <div className="dashboard-home__icon">{card.icon}</div>
                      <div>
                        <h2 className="dashboard-home__card-title">
                          {card.title}
                        </h2>
                        <p className="dashboard-home__card-description">
                          {card.description}
                        </p>
                      </div>
                    </div>
                  </article>
                </Link>
              </div>
            ))}
          </div>
        </section>
      </main>

      <footer className="dashboard-home__footer">
        <div className="dashboard-home__footer-inner">
          <p>Developed by: A.B.C.C</p>
        </div>
      </footer>
    </div>
  );
};

export default DashboardHomeLayout;
