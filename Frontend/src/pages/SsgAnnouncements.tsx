import { FormEvent, useEffect, useMemo, useState } from "react";
import Modal from "react-modal";
import { FaEdit, FaPlus, FaTrashAlt } from "react-icons/fa";

import {
  createGovernanceAnnouncement,
  deleteGovernanceAnnouncement,
  fetchGovernanceAnnouncements,
  GovernanceAnnouncementItem,
  GovernanceAnnouncementStatus,
  updateGovernanceAnnouncement,
} from "../api/governanceHierarchyApi";
import NavbarSSG from "../components/NavbarSSG";
import "../css/GovernanceHierarchyManagement.css";
import "../css/SsgWorkspace.css";
import { useSsgWorkspace } from "../hooks/useSsgWorkspace";
import {
  formatDateLabel,
  toStatusToneClass,
  truncateText,
} from "../utils/ssgWorkspaceHelpers";

interface AnnouncementDraftState {
  id?: number;
  title: string;
  body: string;
  status: GovernanceAnnouncementStatus;
}

const emptyDraft: AnnouncementDraftState = {
  title: "",
  body: "",
  status: "draft",
};

Modal.setAppElement("#root");

const SsgAnnouncements = () => {
  const { officerName, ssgAccessUnit } = useSsgWorkspace();
  const [announcements, setAnnouncements] = useState<GovernanceAnnouncementItem[]>([]);
  const [draft, setDraft] = useState<AnnouncementDraftState>(emptyDraft);
  const [editingAnnouncement, setEditingAnnouncement] = useState<GovernanceAnnouncementItem | null>(null);
  const [pendingDelete, setPendingDelete] = useState<GovernanceAnnouncementItem | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const loadAnnouncements = async () => {
    if (!ssgAccessUnit) {
      setAnnouncements([]);
      setLoading(false);
      return;
    }

    setLoading(true);
    try {
      const items = await fetchGovernanceAnnouncements(ssgAccessUnit.governance_unit_id);
      setAnnouncements(items);
      setError(null);
    } catch (requestError) {
      setError(
        requestError instanceof Error ? requestError.message : "Failed to load SSG announcements"
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void loadAnnouncements();
  }, [ssgAccessUnit?.governance_unit_id]);

  const counts = useMemo(
    () => ({
      published: announcements.filter((item) => item.status === "published").length,
      draft: announcements.filter((item) => item.status === "draft").length,
      archived: announcements.filter((item) => item.status === "archived").length,
    }),
    [announcements]
  );

  const openCreateModal = () => {
    setEditingAnnouncement(null);
    setDraft(emptyDraft);
    setError(null);
    setIsModalOpen(true);
  };

  const openEditModal = (announcement: GovernanceAnnouncementItem) => {
    setEditingAnnouncement(announcement);
    setDraft({
      id: announcement.id,
      title: announcement.title,
      body: announcement.body,
      status: announcement.status,
    });
    setError(null);
    setIsModalOpen(true);
  };

  const handleSave = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!ssgAccessUnit) {
      setError("Missing governance scope for this SSG workspace.");
      return;
    }

    const title = draft.title.trim();
    const body = draft.body.trim();
    if (!title || !body) {
      setError("Title and body are required before saving an announcement.");
      return;
    }

    void (async () => {
      try {
        if (draft.id) {
          await updateGovernanceAnnouncement(draft.id, { title, body, status: draft.status });
        } else {
          await createGovernanceAnnouncement(ssgAccessUnit.governance_unit_id, {
            title,
            body,
            status: draft.status,
          });
        }
        await loadAnnouncements();
        setIsModalOpen(false);
        setEditingAnnouncement(null);
        setDraft(emptyDraft);
        setError(null);
      } catch (requestError) {
        setError(
          requestError instanceof Error ? requestError.message : "Failed to save the SSG announcement"
        );
      }
    })();
  };

  const updateStatus = (
    announcement: GovernanceAnnouncementItem,
    status: GovernanceAnnouncementStatus
  ) => {
    void (async () => {
      try {
        await updateGovernanceAnnouncement(announcement.id, { status });
        await loadAnnouncements();
      } catch (requestError) {
        setError(
          requestError instanceof Error ? requestError.message : "Failed to update announcement status"
        );
      }
    })();
  };

  const handleDelete = () => {
    if (!pendingDelete) return;
    void (async () => {
      try {
        await deleteGovernanceAnnouncement(pendingDelete.id);
        await loadAnnouncements();
        setPendingDelete(null);
      } catch (requestError) {
        setError(
          requestError instanceof Error ? requestError.message : "Failed to delete the SSG announcement"
        );
      }
    })();
  };

  return (
    <div className="ssg-workspace-page">
      <NavbarSSG />

      <main className="container py-4 ssg-workspace-main">
        <section className="ssg-page-header">
          <div className="ssg-page-header__copy">
            <p className="ssg-page-eyebrow">SSG Announcements</p>
            <h1>Campus announcements</h1>
            <p>
              Draft, publish, archive, and maintain student government updates for your campus.
            </p>
          </div>
          <div className="ssg-page-actions">
            <button type="button" className="btn btn-light" onClick={openCreateModal}>
              <FaPlus className="me-2" />
              New Announcement
            </button>
          </div>
        </section>

        <section className="ssg-stat-grid">
          <article className="ssg-stat-card">
            <span className="ssg-stat-card__label">Published</span>
            <strong className="ssg-stat-card__value">{counts.published}</strong>
            <span className="ssg-stat-card__hint">Visible campus announcements</span>
          </article>
          <article className="ssg-stat-card">
            <span className="ssg-stat-card__label">Draft</span>
            <strong className="ssg-stat-card__value">{counts.draft}</strong>
            <span className="ssg-stat-card__hint">Updates still being prepared</span>
          </article>
          <article className="ssg-stat-card">
            <span className="ssg-stat-card__label">Archived</span>
            <strong className="ssg-stat-card__value">{counts.archived}</strong>
            <span className="ssg-stat-card__hint">Past announcements kept for reference</span>
          </article>
          <article className="ssg-stat-card">
            <span className="ssg-stat-card__label">Total</span>
            <strong className="ssg-stat-card__value">{announcements.length}</strong>
            <span className="ssg-stat-card__hint">Campus announcement records in this workspace</span>
          </article>
        </section>

        {error && <div className="alert alert-danger mb-0">{error}</div>}

        <section className="ssg-panel-card">
          <div className="ssg-panel-card__header">
            <div>
              <h2 className="ssg-panel-card__title">Announcement directory</h2>
              <p className="ssg-panel-card__subtitle">
                Scope is limited to the current campus SSG workspace.
              </p>
            </div>
          </div>

          {loading ? (
            <div className="ssg-empty-state">Loading announcements...</div>
          ) : announcements.length === 0 ? (
            <div className="ssg-empty-state">
              No announcements yet. Create the first SSG announcement to begin publishing updates.
            </div>
          ) : (
            <div className="ssg-table-wrap">
              <table className="ssg-data-table">
                <thead>
                  <tr>
                    <th>Announcement</th>
                    <th>Status</th>
                    <th>Author</th>
                    <th>Date</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {announcements.map((announcement) => (
                    <tr key={announcement.id}>
                      <td data-label="Announcement">
                        <strong>{announcement.title}</strong>
                        <div className="ssg-announcement-body-preview">
                          {truncateText(announcement.body, 140)}
                        </div>
                      </td>
                      <td data-label="Status">
                        <span className={`ssg-badge ${toStatusToneClass(announcement.status)}`}>
                          {announcement.status}
                        </span>
                      </td>
                      <td data-label="Author">{announcement.author_name || officerName}</td>
                      <td data-label="Date">{formatDateLabel(announcement.updated_at)}</td>
                      <td data-label="Actions">
                        <div className="ssg-table-actions">
                          {announcement.status === "draft" && (
                            <button
                              type="button"
                              className="btn btn-outline-success"
                              onClick={() => updateStatus(announcement, "published")}
                            >
                              Publish
                            </button>
                          )}
                          {announcement.status === "published" && (
                            <button
                              type="button"
                              className="btn btn-outline-secondary"
                              onClick={() => updateStatus(announcement, "archived")}
                            >
                              Archive
                            </button>
                          )}
                          <button
                            type="button"
                            className="btn btn-outline-primary"
                            onClick={() => openEditModal(announcement)}
                          >
                            <FaEdit className="me-2" />
                            Edit
                          </button>
                          <button
                            type="button"
                            className="btn btn-outline-danger"
                            onClick={() => setPendingDelete(announcement)}
                          >
                            <FaTrashAlt className="me-2" />
                            Delete
                          </button>
                        </div>
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
        isOpen={isModalOpen}
        onRequestClose={() => setIsModalOpen(false)}
        className="ssg-setup-modal ssg-announcement-modal"
        overlayClassName="ssg-setup-overlay"
      >
        <form onSubmit={handleSave}>
          <div className="ssg-setup-modal__header">
            <h3>{editingAnnouncement ? "Edit Announcement" : "New Announcement"}</h3>
            <button type="button" className="ssg-setup-modal__close" onClick={() => setIsModalOpen(false)}>
              &times;
            </button>
          </div>

          <div className="ssg-setup-modal__body">
            <div className="form-group">
              <label htmlFor="announcementTitle">Title</label>
              <input
                id="announcementTitle"
                value={draft.title}
                onChange={(event) => setDraft((current) => ({ ...current, title: event.target.value }))}
                required
              />
            </div>
            <div className="form-group">
              <label htmlFor="announcementBody">Body</label>
              <textarea
                id="announcementBody"
                rows={7}
                value={draft.body}
                onChange={(event) => setDraft((current) => ({ ...current, body: event.target.value }))}
                required
              />
            </div>
            <div className="form-group">
              <label htmlFor="announcementStatus">Status</label>
              <select
                id="announcementStatus"
                value={draft.status}
                onChange={(event) =>
                  setDraft((current) => ({
                    ...current,
                    status: event.target.value as GovernanceAnnouncementStatus,
                  }))
                }
              >
                <option value="draft">Draft</option>
                <option value="published">Published</option>
                <option value="archived">Archived</option>
              </select>
            </div>
          </div>

          <div className="ssg-setup-modal__footer">
            <button type="button" className="btn btn-outline-secondary" onClick={() => setIsModalOpen(false)}>
              Cancel
            </button>
            <button type="submit" className="btn btn-primary">
              {editingAnnouncement ? "Save Changes" : "Create Announcement"}
            </button>
          </div>
        </form>
      </Modal>

      <Modal
        isOpen={pendingDelete !== null}
        onRequestClose={() => setPendingDelete(null)}
        className="ssg-setup-modal ssg-setup-modal--compact"
        overlayClassName="ssg-setup-overlay"
      >
        <div className="ssg-setup-modal__header">
          <h3>Delete Announcement</h3>
          <button type="button" className="ssg-setup-modal__close" onClick={() => setPendingDelete(null)}>
            &times;
          </button>
        </div>
        <div className="ssg-setup-modal__body">
          <div className="ssg-inline-confirm">
            Delete <strong>{pendingDelete?.title}</strong>? This announcement will be removed from the
            SSG workspace on this device.
          </div>
        </div>
        <div className="ssg-setup-modal__footer">
          <button type="button" className="btn btn-outline-secondary" onClick={() => setPendingDelete(null)}>
            Cancel
          </button>
          <button type="button" className="btn btn-danger" onClick={handleDelete}>
            Confirm Delete
          </button>
        </div>
      </Modal>
    </div>
  );
};

export default SsgAnnouncements;
