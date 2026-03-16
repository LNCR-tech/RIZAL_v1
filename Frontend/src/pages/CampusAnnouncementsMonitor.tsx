import { useDeferredValue, useEffect, useMemo, useState } from "react";
import Modal from "react-modal";
import { FaBullhorn, FaEye, FaSearch } from "react-icons/fa";

import {
  fetchSchoolGovernanceAnnouncements,
  GovernanceAnnouncementMonitorItem,
  GovernanceAnnouncementStatus,
  GovernanceUnitType,
} from "../api/governanceHierarchyApi";
import NavbarSchoolIT from "../components/NavbarSchoolIT";
import "../css/GovernanceHierarchyManagement.css";
import "../css/SsgWorkspace.css";
import { formatDateLabel, toStatusToneClass, truncateText } from "../utils/ssgWorkspaceHelpers";

Modal.setAppElement("#root");

const CampusAnnouncementsMonitor = () => {
  const [announcements, setAnnouncements] = useState<GovernanceAnnouncementMonitorItem[]>([]);
  const [searchTerm, setSearchTerm] = useState("");
  const [statusFilter, setStatusFilter] = useState<GovernanceAnnouncementStatus | "all">("all");
  const [unitTypeFilter, setUnitTypeFilter] = useState<GovernanceUnitType | "all">("all");
  const [selectedAnnouncement, setSelectedAnnouncement] =
    useState<GovernanceAnnouncementMonitorItem | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const deferredSearchTerm = useDeferredValue(searchTerm);

  useEffect(() => {
    const loadAnnouncements = async () => {
      setLoading(true);
      try {
        const items = await fetchSchoolGovernanceAnnouncements({ limit: 250 });
        setAnnouncements(items);
        setError(null);
      } catch (requestError) {
        setError(
          requestError instanceof Error
            ? requestError.message
            : "Failed to load campus governance announcements"
        );
      } finally {
        setLoading(false);
      }
    };

    void loadAnnouncements();
  }, []);

  const stats = useMemo(
    () => ({
      total: announcements.length,
      published: announcements.filter((item) => item.status === "published").length,
      draft: announcements.filter((item) => item.status === "draft").length,
      archived: announcements.filter((item) => item.status === "archived").length,
    }),
    [announcements]
  );

  const filteredAnnouncements = useMemo(() => {
    const normalizedSearch = deferredSearchTerm.trim().toLowerCase();
    return announcements.filter((item) => {
      const matchesStatus = statusFilter === "all" || item.status === statusFilter;
      const matchesUnitType = unitTypeFilter === "all" || item.governance_unit_type === unitTypeFilter;
      const matchesSearch =
        normalizedSearch.length === 0 ||
        [
          item.title,
          item.body,
          item.governance_unit_code,
          item.governance_unit_name,
          item.author_name ?? "",
        ]
          .join(" ")
          .toLowerCase()
          .includes(normalizedSearch);

      return matchesStatus && matchesUnitType && matchesSearch;
    });
  }, [announcements, deferredSearchTerm, statusFilter, unitTypeFilter]);

  return (
    <div className="ssg-workspace-page">
      <NavbarSchoolIT />

      <main className="container py-4 ssg-workspace-main">
        <section className="ssg-page-header">
          <div className="ssg-page-header__copy">
            <p className="ssg-page-eyebrow">Campus Admin / Announcements</p>
            <h1>Campus announcement monitor</h1>
            <p>
              Review SSG, SG, and ORG announcements across your campus without leaving the Campus
              Admin workspace.
            </p>
          </div>
        </section>

        <section className="ssg-stat-grid">
          <article className="ssg-stat-card">
            <span className="ssg-stat-card__label">Total</span>
            <strong className="ssg-stat-card__value">{stats.total}</strong>
            <span className="ssg-stat-card__hint">Announcement records across this campus</span>
          </article>
          <article className="ssg-stat-card">
            <span className="ssg-stat-card__label">Published</span>
            <strong className="ssg-stat-card__value">{stats.published}</strong>
            <span className="ssg-stat-card__hint">Visible announcements</span>
          </article>
          <article className="ssg-stat-card">
            <span className="ssg-stat-card__label">Draft</span>
            <strong className="ssg-stat-card__value">{stats.draft}</strong>
            <span className="ssg-stat-card__hint">Still being prepared</span>
          </article>
          <article className="ssg-stat-card">
            <span className="ssg-stat-card__label">Archived</span>
            <strong className="ssg-stat-card__value">{stats.archived}</strong>
            <span className="ssg-stat-card__hint">Stored for audit and reference</span>
          </article>
        </section>

        {error && <div className="alert alert-danger mb-0">{error}</div>}

        <section className="ssg-panel-card">
          <div className="ssg-panel-card__header">
            <div>
              <h2 className="ssg-panel-card__title">Announcement directory</h2>
              <p className="ssg-panel-card__subtitle">
                School-scoped monitoring only. Other campuses are excluded at the API level.
              </p>
            </div>
          </div>

          <div className="ssg-feature-controls">
            <div className="ssg-feature-search">
              <FaSearch />
              <input
                type="text"
                placeholder="Search title, unit, or author..."
                value={searchTerm}
                onChange={(event) => setSearchTerm(event.target.value)}
              />
            </div>

            <select
              className="ssg-feature-select"
              value={unitTypeFilter}
              onChange={(event) =>
                setUnitTypeFilter(event.target.value as GovernanceUnitType | "all")
              }
            >
              <option value="all">All Units</option>
              <option value="SSG">SSG</option>
              <option value="SG">SG</option>
              <option value="ORG">ORG</option>
            </select>

            <select
              className="ssg-feature-select"
              value={statusFilter}
              onChange={(event) =>
                setStatusFilter(event.target.value as GovernanceAnnouncementStatus | "all")
              }
            >
              <option value="all">All Statuses</option>
              <option value="published">Published</option>
              <option value="draft">Draft</option>
              <option value="archived">Archived</option>
            </select>
          </div>

          {loading ? (
            <div className="ssg-empty-state">Loading announcements...</div>
          ) : filteredAnnouncements.length === 0 ? (
            <div className="ssg-empty-state">No campus announcements match the current filters.</div>
          ) : (
            <div className="ssg-table-wrap">
              <table className="ssg-data-table">
                <thead>
                  <tr>
                    <th>Unit</th>
                    <th>Announcement</th>
                    <th>Status</th>
                    <th>Author</th>
                    <th>Updated</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredAnnouncements.map((announcement) => (
                    <tr key={announcement.id}>
                      <td data-label="Unit">
                        <div className="ssg-feature-meta">
                          <strong>{announcement.governance_unit_code}</strong>
                          <small>
                            {announcement.governance_unit_type} / {announcement.governance_unit_name}
                          </small>
                        </div>
                      </td>
                      <td data-label="Announcement">
                        <strong>{announcement.title}</strong>
                        <div className="ssg-announcement-body-preview">
                          {truncateText(announcement.body, 150)}
                        </div>
                      </td>
                      <td data-label="Status">
                        <span className={`ssg-badge ${toStatusToneClass(announcement.status)}`}>
                          {announcement.status}
                        </span>
                      </td>
                      <td data-label="Author">{announcement.author_name || "Unknown"}</td>
                      <td data-label="Updated">{formatDateLabel(announcement.updated_at)}</td>
                      <td data-label="Actions">
                        <button
                          type="button"
                          className="btn btn-outline-primary"
                          onClick={() => setSelectedAnnouncement(announcement)}
                        >
                          <FaEye className="me-2" />
                          View
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>
      </main>

      <Modal
        isOpen={selectedAnnouncement !== null}
        onRequestClose={() => setSelectedAnnouncement(null)}
        className="ssg-setup-modal ssg-announcement-modal"
        overlayClassName="ssg-setup-overlay"
      >
        <div className="ssg-setup-modal__header">
          <h3>Announcement Details</h3>
          <button
            type="button"
            className="ssg-setup-modal__close"
            onClick={() => setSelectedAnnouncement(null)}
          >
            &times;
          </button>
        </div>

        {selectedAnnouncement && (
          <div className="ssg-setup-modal__body">
            <div className="ssg-selected-student-card mb-3">
              <div className="ssg-selected-student-card__avatar">
                <FaBullhorn />
              </div>
              <div className="ssg-selected-student-card__details">
                <strong>{selectedAnnouncement.title}</strong>
                <div className="ssg-selected-student-card__meta">
                  {selectedAnnouncement.governance_unit_code} / {selectedAnnouncement.governance_unit_name}
                </div>
                <div className="ssg-selected-student-card__meta">
                  {selectedAnnouncement.author_name || "Unknown"} ·{" "}
                  {formatDateLabel(selectedAnnouncement.updated_at)}
                </div>
              </div>
            </div>

            <div className="mb-3">
              <span className={`ssg-badge ${toStatusToneClass(selectedAnnouncement.status)}`}>
                {selectedAnnouncement.status}
              </span>
            </div>

            <div className="form-group">
              <label>Body</label>
              <textarea readOnly rows={10} value={selectedAnnouncement.body} />
            </div>
          </div>
        )}

        <div className="ssg-setup-modal__footer">
          <button
            type="button"
            className="btn btn-outline-secondary"
            onClick={() => setSelectedAnnouncement(null)}
          >
            Close
          </button>
        </div>
      </Modal>
    </div>
  );
};

export default CampusAnnouncementsMonitor;
