"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { PageHeader } from "@/components/page-header/page-header";
import shared from "../shared.module.css";
import { Tag } from "../types";

export default function TagsManagementPage() {
  const [tags, setTags] = useState<Tag[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [newTagName, setNewTagName] = useState("");
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [editingTag, setEditingTag] = useState<Tag | null>(null);
  const [editName, setEditName] = useState("");
  const [deleteTarget, setDeleteTarget] = useState<Tag | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [toastMsg, setToastMsg] = useState<string | null>(null);

  const showToast = (msg: string) => {
    setToastMsg(msg);
    setTimeout(() => setToastMsg(null), 4000);
  };

  const fetchTags = async () => {
    setLoading(true);
    try {
      const res = await fetch("/api/proxy/contacts/tags");
      if (res.ok) {
        const data = await res.json();
        setTags(data || []);
      }
    } catch {
      setTags([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTags();
  }, []);

  const handleCreateTag = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newTagName.trim()) return;
    setSubmitting(true);
    setErrorMsg(null);

    try {
      const res = await fetch("/api/proxy/contacts/tags", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: newTagName.trim() }),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || "Failed to create tag");
      }

      showToast(`Tag "${newTagName.trim()}" created!`);
      setNewTagName("");
      setIsCreateOpen(false);
      fetchTags();
    } catch (err: unknown) {
      setErrorMsg(err instanceof Error ? err.message : "Could not create tag");
    } finally {
      setSubmitting(false);
    }
  };

  const handleRenameTag = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingTag || !editName.trim()) return;
    setSubmitting(true);
    setErrorMsg(null);

    try {
      const res = await fetch(`/api/proxy/contacts/tags/${editingTag.id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: editName.trim() }),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || "Failed to rename tag");
      }

      showToast(`Tag renamed to "${editName.trim()}"`);
      setEditingTag(null);
      fetchTags();
    } catch (err: unknown) {
      setErrorMsg(err instanceof Error ? err.message : "Could not rename tag");
    } finally {
      setSubmitting(false);
    }
  };

  const handleDeleteTag = async () => {
    if (!deleteTarget) return;
    setSubmitting(true);
    try {
      const res = await fetch(`/api/proxy/contacts/tags/${deleteTarget.id}`, {
        method: "DELETE",
      });
      if (!res.ok) throw new Error("Failed to delete tag");
      showToast(`Tag "${deleteTarget.name}" deleted`);
      setDeleteTarget(null);
      fetchTags();
    } catch (err: unknown) {
      setErrorMsg(err instanceof Error ? err.message : "Could not delete tag");
    } finally {
      setSubmitting(false);
    }
  };

  const filteredTags = tags.filter((t) =>
    t.name.toLowerCase().includes(search.toLowerCase().trim()),
  );

  return (
    <div style={{ padding: "28px 32px", maxWidth: "1200px", margin: "0 auto" }}>
      {toastMsg && (
        <div
          style={{
            position: "fixed",
            bottom: "24px",
            right: "24px",
            zIndex: 9999,
            background: "linear-gradient(135deg, #0F6B6D 0%, #061819 100%)",
            border: "1px solid #D4AF37",
            color: "#F8F8F5",
            padding: "14px 22px",
            borderRadius: "12px",
            boxShadow: "0 10px 30px rgba(0,0,0,0.6)",
            fontWeight: 600,
            fontSize: "0.9rem",
            display: "flex",
            alignItems: "center",
            gap: "10px",
          }}
        >
          <span>🏷️</span> {toastMsg}
        </div>
      )}

      <PageHeader
        title="Tag & Label Manager"
        description="Categorize audiences, organize lead groups, and power behavioral automations with flexible color tags."
        actions={
          <div style={{ display: "flex", gap: "10px" }}>
            <Link href="/dashboard/contacts" className={shared.statusTab}>
              ← Contacts Hub
            </Link>
            <button
              onClick={() => {
                setErrorMsg(null);
                setNewTagName("");
                setIsCreateOpen(true);
              }}
              className={shared.primaryButton}
              id="btn-create-tag"
            >
              <span>+</span> Create Tag
            </button>
          </div>
        }
      />

      {/* Metrics / Overview */}
      <div className={shared.metricsGrid}>
        <div className={shared.metricCard}>
          <div className={shared.metricLabel}>Total Tags</div>
          <div className={shared.metricValue}>{tags.length}</div>
        </div>
        <div className={shared.metricCard}>
          <div className={shared.metricLabel}>Assigned Contacts</div>
          <div className={shared.metricValue} style={{ color: "#D4AF37" }}>
            {tags.reduce((acc, t) => acc + (t.contacts_count || 0), 0)}
          </div>
        </div>
      </div>

      {/* Search Toolbar */}
      <div className={shared.card} style={{ marginBottom: "24px" }}>
        <div className={shared.toolbar} style={{ marginBottom: 0 }}>
          <div className={shared.searchGroup}>
            <input
              type="text"
              placeholder="Search tags by name..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className={shared.searchInput}
              id="search-tags"
            />
          </div>
        </div>
      </div>

      {/* Tags Grid / List */}
      <div className={shared.card}>
        {loading ? (
          <div style={{ padding: "48px 0", textAlign: "center", color: "#8E9C9D" }}>
            <div style={{ fontSize: "1.5rem", marginBottom: "8px" }}>⏳</div>
            Loading tags...
          </div>
        ) : filteredTags.length === 0 ? (
          <div style={{ padding: "56px 20px", textAlign: "center" }}>
            <div style={{ fontSize: "2.8rem", marginBottom: "14px" }}>🏷️</div>
            <h3
              style={{ color: "#F8F8F5", fontSize: "1.2rem", fontWeight: 700, marginBottom: "8px" }}
            >
              No tags found
            </h3>
            <p
              style={{
                color: "#8E9C9D",
                maxWidth: "420px",
                margin: "0 auto 20px",
                fontSize: "0.88rem",
              }}
            >
              {search
                ? "No tags matching your search query."
                : "Create tags like 'VIP', 'Webinar Attendee', or 'High Intent' to segment your audience seamlessly."}
            </p>
            <button
              onClick={() => {
                setErrorMsg(null);
                setNewTagName("");
                setIsCreateOpen(true);
              }}
              className={shared.primaryButton}
            >
              + Create First Tag
            </button>
          </div>
        ) : (
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))",
              gap: "16px",
            }}
          >
            {filteredTags.map((tag) => (
              <div
                key={tag.id}
                style={{
                  background: "rgba(15, 107, 109, 0.14)",
                  border: "1px solid rgba(212, 175, 55, 0.2)",
                  borderRadius: "14px",
                  padding: "16px 20px",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                  transition: "all 0.2s ease",
                }}
              >
                <div>
                  <div
                    style={{
                      display: "flex",
                      alignItems: "center",
                      gap: "8px",
                      marginBottom: "4px",
                    }}
                  >
                    <span
                      style={{
                        display: "inline-block",
                        width: "10px",
                        height: "10px",
                        borderRadius: "50%",
                        background: "#D4AF37",
                        boxShadow: "0 0 8px rgba(212, 175, 55, 0.5)",
                      }}
                    />
                    <span style={{ color: "#F8F8F5", fontWeight: 800, fontSize: "0.95rem" }}>
                      {tag.name}
                    </span>
                  </div>
                  <Link
                    href={`/dashboard/contacts?tag_id=${tag.id}`}
                    style={{
                      fontSize: "0.78rem",
                      color: "#8E9C9D",
                      textDecoration: "none",
                    }}
                  >
                    👥 {tag.contacts_count ?? 0} contacts tagged
                  </Link>
                </div>

                <div style={{ display: "flex", gap: "6px" }}>
                  <button
                    onClick={() => {
                      setEditingTag(tag);
                      setEditName(tag.name);
                      setErrorMsg(null);
                    }}
                    style={{
                      background: "rgba(255, 255, 255, 0.08)",
                      border: "1px solid rgba(255, 255, 255, 0.15)",
                      color: "#F8F8F5",
                      padding: "4px 10px",
                      borderRadius: "6px",
                      fontSize: "0.75rem",
                      fontWeight: 600,
                      cursor: "pointer",
                    }}
                  >
                    Rename
                  </button>
                  <button
                    onClick={() => setDeleteTarget(tag)}
                    style={{
                      background: "rgba(239, 68, 68, 0.15)",
                      border: "1px solid rgba(239, 68, 68, 0.3)",
                      color: "#f87171",
                      padding: "4px 10px",
                      borderRadius: "6px",
                      fontSize: "0.75rem",
                      fontWeight: 600,
                      cursor: "pointer",
                    }}
                  >
                    Delete
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Create Modal */}
      {isCreateOpen && (
        <div
          style={{
            position: "fixed",
            inset: 0,
            background: "rgba(4, 15, 16, 0.85)",
            backdropFilter: "blur(10px)",
            zIndex: 999,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            padding: "20px",
          }}
          onClick={() => !submitting && setIsCreateOpen(false)}
        >
          <div
            style={{
              background: "linear-gradient(145deg, #072224 0%, #041416 100%)",
              border: "1px solid #D4AF37",
              borderRadius: "20px",
              padding: "28px",
              maxWidth: "440px",
              width: "100%",
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <h3
              style={{
                color: "#F8F8F5",
                fontSize: "1.2rem",
                fontWeight: 800,
                marginBottom: "16px",
              }}
            >
              Create New Tag
            </h3>
            {errorMsg && (
              <div
                style={{
                  color: "#fca5a5",
                  background: "rgba(239, 68, 68, 0.15)",
                  padding: "10px",
                  borderRadius: "8px",
                  fontSize: "0.85rem",
                  marginBottom: "14px",
                }}
              >
                ⚠️ {errorMsg}
              </div>
            )}
            <form onSubmit={handleCreateTag}>
              <label
                style={{
                  display: "block",
                  color: "#D4AF37",
                  fontSize: "0.75rem",
                  fontWeight: 800,
                  textTransform: "uppercase",
                  marginBottom: "6px",
                }}
              >
                Tag Name *
              </label>
              <input
                type="text"
                required
                placeholder="e.g. VIP Customer"
                value={newTagName}
                onChange={(e) => setNewTagName(e.target.value)}
                className={shared.searchInput}
                style={{ width: "100%", marginBottom: "18px" }}
                autoFocus
              />
              <div style={{ display: "flex", justifyContent: "flex-end", gap: "10px" }}>
                <button
                  type="button"
                  onClick={() => setIsCreateOpen(false)}
                  disabled={submitting}
                  style={{
                    background: "transparent",
                    border: "none",
                    color: "#8E9C9D",
                    cursor: "pointer",
                    fontWeight: 600,
                  }}
                >
                  Cancel
                </button>
                <button type="submit" disabled={submitting} className={shared.primaryButton}>
                  {submitting ? "Creating..." : "Save Tag"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Rename Modal */}
      {editingTag && (
        <div
          style={{
            position: "fixed",
            inset: 0,
            background: "rgba(4, 15, 16, 0.85)",
            backdropFilter: "blur(10px)",
            zIndex: 999,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            padding: "20px",
          }}
          onClick={() => !submitting && setEditingTag(null)}
        >
          <div
            style={{
              background: "linear-gradient(145deg, #072224 0%, #041416 100%)",
              border: "1px solid #D4AF37",
              borderRadius: "20px",
              padding: "28px",
              maxWidth: "440px",
              width: "100%",
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <h3
              style={{
                color: "#F8F8F5",
                fontSize: "1.2rem",
                fontWeight: 800,
                marginBottom: "16px",
              }}
            >
              Rename Tag
            </h3>
            {errorMsg && (
              <div
                style={{
                  color: "#fca5a5",
                  background: "rgba(239, 68, 68, 0.15)",
                  padding: "10px",
                  borderRadius: "8px",
                  fontSize: "0.85rem",
                  marginBottom: "14px",
                }}
              >
                ⚠️ {errorMsg}
              </div>
            )}
            <form onSubmit={handleRenameTag}>
              <label
                style={{
                  display: "block",
                  color: "#D4AF37",
                  fontSize: "0.75rem",
                  fontWeight: 800,
                  textTransform: "uppercase",
                  marginBottom: "6px",
                }}
              >
                New Name *
              </label>
              <input
                type="text"
                required
                value={editName}
                onChange={(e) => setEditName(e.target.value)}
                className={shared.searchInput}
                style={{ width: "100%", marginBottom: "18px" }}
                autoFocus
              />
              <div style={{ display: "flex", justifyContent: "flex-end", gap: "10px" }}>
                <button
                  type="button"
                  onClick={() => setEditingTag(null)}
                  disabled={submitting}
                  style={{
                    background: "transparent",
                    border: "none",
                    color: "#8E9C9D",
                    cursor: "pointer",
                    fontWeight: 600,
                  }}
                >
                  Cancel
                </button>
                <button type="submit" disabled={submitting} className={shared.primaryButton}>
                  {submitting ? "Renaming..." : "Update Tag"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Delete Confirmation Modal */}
      {deleteTarget && (
        <div
          style={{
            position: "fixed",
            inset: 0,
            background: "rgba(4, 15, 16, 0.85)",
            backdropFilter: "blur(10px)",
            zIndex: 999,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            padding: "20px",
          }}
          onClick={() => !submitting && setDeleteTarget(null)}
        >
          <div
            style={{
              background: "#072224",
              border: "1px solid rgba(239, 68, 68, 0.5)",
              borderRadius: "20px",
              padding: "28px",
              maxWidth: "420px",
              width: "100%",
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <h3
              style={{
                color: "#F8F8F5",
                fontSize: "1.15rem",
                fontWeight: 800,
                marginBottom: "10px",
              }}
            >
              Delete Tag &quot;{deleteTarget.name}&quot;?
            </h3>
            <p
              style={{
                color: "#8E9C9D",
                fontSize: "0.88rem",
                marginBottom: "20px",
                lineHeight: 1.5,
              }}
            >
              This tag will be removed from all assigned contacts. Contacts themselves will NOT be
              deleted.
            </p>
            <div style={{ display: "flex", justifyContent: "flex-end", gap: "10px" }}>
              <button
                onClick={() => setDeleteTarget(null)}
                disabled={submitting}
                style={{
                  background: "transparent",
                  border: "none",
                  color: "#8E9C9D",
                  cursor: "pointer",
                  fontWeight: 600,
                }}
              >
                Cancel
              </button>
              <button
                onClick={handleDeleteTag}
                disabled={submitting}
                style={{
                  background: "#ef4444",
                  border: "none",
                  color: "#ffffff",
                  padding: "8px 18px",
                  borderRadius: "999px",
                  fontWeight: 700,
                  cursor: "pointer",
                }}
              >
                {submitting ? "Deleting..." : "Confirm Delete"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
