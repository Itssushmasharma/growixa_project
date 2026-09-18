"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { PageHeader } from "@/components/page-header/page-header";
import shared from "../shared.module.css";
import { Company, CompanyLifecycleStage } from "../types";

const LIFECYCLE_STAGES: { label: string; value: CompanyLifecycleStage; color: string }[] = [
  { label: "Prospect", value: "PROSPECT", color: "rgba(148, 163, 184, 0.2)" },
  { label: "Lead", value: "LEAD", color: "rgba(59, 130, 246, 0.2)" },
  { label: "Qualified", value: "QUALIFIED", color: "rgba(168, 85, 247, 0.2)" },
  { label: "Customer", value: "CUSTOMER", color: "rgba(34, 197, 94, 0.2)" },
  { label: "Partner", value: "PARTNER", color: "rgba(234, 179, 8, 0.2)" },
  { label: "Churned", value: "CHURNED", color: "rgba(239, 68, 68, 0.2)" },
  { label: "Other", value: "OTHER", color: "rgba(100, 116, 139, 0.2)" },
];

export default function CompaniesPage() {
  const [companies, setCompanies] = useState<Company[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [stageFilter, setStageFilter] = useState<string>("ALL");

  // Modals state
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [editingCompany, setEditingCompany] = useState<Company | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<Company | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [toastMsg, setToastMsg] = useState<string | null>(null);

  // Form inputs
  const [formData, setFormData] = useState({
    name: "",
    domain: "",
    industry: "",
    website: "",
    phone: "",
    address: "",
    lifecycle_stage: "PROSPECT" as CompanyLifecycleStage,
  });

  const showToast = (msg: string) => {
    setToastMsg(msg);
    setTimeout(() => setToastMsg(null), 4000);
  };

  const fetchCompanies = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (search.trim()) params.append("search", search.trim());
      if (stageFilter !== "ALL") params.append("lifecycle_stage", stageFilter);

      const res = await fetch(`/api/proxy/contacts/companies?${params.toString()}`);
      if (res.ok) {
        const data = await res.json();
        setCompanies(data.items || []);
        setTotal(data.total || 0);
      }
    } catch {
      // Mock / fallback if offline or proxy error
      setCompanies([]);
    } finally {
      setLoading(false);
    }
  }, [search, stageFilter]);

  useEffect(() => {
    fetchCompanies();
  }, [fetchCompanies]);

  const metrics = useMemo(() => {
    const counts = {
      total: total || companies.length,
      customers: companies.filter((c) => c.lifecycle_stage === "CUSTOMER").length,
      qualified: companies.filter((c) => c.lifecycle_stage === "QUALIFIED").length,
      leads: companies.filter(
        (c) => c.lifecycle_stage === "LEAD" || c.lifecycle_stage === "PROSPECT",
      ).length,
    };
    return counts;
  }, [companies, total]);

  const handleCreateOrUpdate = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setErrorMsg(null);

    try {
      const isEdit = !!editingCompany;
      const url = isEdit
        ? `/api/proxy/contacts/companies/${editingCompany.id}`
        : "/api/proxy/contacts/companies";
      const method = isEdit ? "PATCH" : "POST";

      const res = await fetch(url, {
        method,
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(formData),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || "Failed to save company record");
      }

      showToast(isEdit ? "Company updated successfully!" : "Company created successfully!");
      setIsCreateOpen(false);
      setEditingCompany(null);
      resetForm();
      fetchCompanies();
    } catch (err: unknown) {
      setErrorMsg(err instanceof Error ? err.message : "An error occurred");
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async () => {
    if (!deleteTarget) return;
    setSubmitting(true);
    try {
      const res = await fetch(`/api/proxy/contacts/companies/${deleteTarget.id}`, {
        method: "DELETE",
      });
      if (!res.ok) throw new Error("Failed to delete company");
      showToast(`Company "${deleteTarget.name}" deleted`);
      setDeleteTarget(null);
      fetchCompanies();
    } catch (err: unknown) {
      setErrorMsg(err instanceof Error ? err.message : "Could not delete company");
    } finally {
      setSubmitting(false);
    }
  };

  const resetForm = () => {
    setFormData({
      name: "",
      domain: "",
      industry: "",
      website: "",
      phone: "",
      address: "",
      lifecycle_stage: "PROSPECT",
    });
  };

  const openEdit = (c: Company) => {
    setEditingCompany(c);
    setFormData({
      name: c.name,
      domain: c.domain || "",
      industry: c.industry || "",
      website: c.website || "",
      phone: c.phone || "",
      address: c.address || "",
      lifecycle_stage: c.lifecycle_stage,
    });
    setIsCreateOpen(true);
  };

  return (
    <div style={{ padding: "28px 32px", maxWidth: "1400px", margin: "0 auto" }}>
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
          <span>✨</span> {toastMsg}
        </div>
      )}

      <PageHeader
        title="B2B Companies CRM"
        description="Organize client accounts, enrich firmographic data, and manage contact relationships across your enterprise pipeline."
        actions={
          <div style={{ display: "flex", gap: "10px" }}>
            <Link href="/dashboard/contacts" className={shared.statusTab}>
              ← Contacts Hub
            </Link>
            <button
              onClick={() => {
                resetForm();
                setEditingCompany(null);
                setIsCreateOpen(true);
              }}
              className={shared.primaryButton}
              id="btn-create-company"
            >
              <span>+</span> New Company
            </button>
          </div>
        }
      />

      {/* Metrics Row */}
      <div className={shared.metricsGrid}>
        <div className={shared.metricCard}>
          <div className={shared.metricLabel}>Total Companies</div>
          <div className={shared.metricValue}>{metrics.total}</div>
        </div>
        <div className={shared.metricCard}>
          <div className={shared.metricLabel}>Customers</div>
          <div className={shared.metricValue} style={{ color: "#4ade80" }}>
            {metrics.customers}
          </div>
        </div>
        <div className={shared.metricCard}>
          <div className={shared.metricLabel}>Qualified Opps</div>
          <div className={shared.metricValue} style={{ color: "#c084fc" }}>
            {metrics.qualified}
          </div>
        </div>
        <div className={shared.metricCard}>
          <div className={shared.metricLabel}>Active Leads</div>
          <div className={shared.metricValue} style={{ color: "#60a5fa" }}>
            {metrics.leads}
          </div>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className={shared.card} style={{ marginBottom: "24px" }}>
        <div className={shared.toolbar} style={{ marginBottom: 0 }}>
          <div className={shared.searchGroup}>
            <input
              type="text"
              placeholder="Search companies by name, domain, industry..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className={shared.searchInput}
              id="search-companies"
            />
          </div>

          <div style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}>
            <button
              onClick={() => setStageFilter("ALL")}
              className={stageFilter === "ALL" ? shared.statusTabActive : shared.statusTab}
            >
              All Stages
            </button>
            {LIFECYCLE_STAGES.map((st) => (
              <button
                key={st.value}
                onClick={() => setStageFilter(st.value)}
                className={stageFilter === st.value ? shared.statusTabActive : shared.statusTab}
              >
                {st.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Companies List */}
      <div className={shared.card}>
        {loading ? (
          <div style={{ padding: "48px 0", textAlign: "center", color: "#8E9C9D" }}>
            <div style={{ fontSize: "1.5rem", marginBottom: "8px" }}>⏳</div>
            Loading company directory...
          </div>
        ) : companies.length === 0 ? (
          <div style={{ padding: "56px 20px", textAlign: "center" }}>
            <div style={{ fontSize: "2.8rem", marginBottom: "14px" }}>🏢</div>
            <h3
              style={{ color: "#F8F8F5", fontSize: "1.2rem", fontWeight: 700, marginBottom: "8px" }}
            >
              No companies found
            </h3>
            <p
              style={{
                color: "#8E9C9D",
                maxWidth: "420px",
                margin: "0 auto 20px",
                fontSize: "0.88rem",
              }}
            >
              {search || stageFilter !== "ALL"
                ? "Try adjusting your search terms or lifecycle filter."
                : "Create your first company profile to group contacts by organization and track account deals."}
            </p>
            <button
              onClick={() => {
                resetForm();
                setEditingCompany(null);
                setIsCreateOpen(true);
              }}
              className={shared.primaryButton}
            >
              + Add Company Record
            </button>
          </div>
        ) : (
          <div style={{ overflowX: "auto" }}>
            <table style={{ width: "100%", borderCollapse: "collapse", textAlign: "left" }}>
              <thead>
                <tr style={{ borderBottom: "1px solid rgba(212, 175, 55, 0.18)" }}>
                  <th
                    style={{
                      padding: "14px 16px",
                      color: "#D4AF37",
                      fontSize: "0.75rem",
                      fontWeight: 800,
                      textTransform: "uppercase",
                    }}
                  >
                    Company
                  </th>
                  <th
                    style={{
                      padding: "14px 16px",
                      color: "#D4AF37",
                      fontSize: "0.75rem",
                      fontWeight: 800,
                      textTransform: "uppercase",
                    }}
                  >
                    Domain & Web
                  </th>
                  <th
                    style={{
                      padding: "14px 16px",
                      color: "#D4AF37",
                      fontSize: "0.75rem",
                      fontWeight: 800,
                      textTransform: "uppercase",
                    }}
                  >
                    Industry
                  </th>
                  <th
                    style={{
                      padding: "14px 16px",
                      color: "#D4AF37",
                      fontSize: "0.75rem",
                      fontWeight: 800,
                      textTransform: "uppercase",
                    }}
                  >
                    Lifecycle Stage
                  </th>
                  <th
                    style={{
                      padding: "14px 16px",
                      color: "#D4AF37",
                      fontSize: "0.75rem",
                      fontWeight: 800,
                      textTransform: "uppercase",
                    }}
                  >
                    Contacts
                  </th>
                  <th
                    style={{
                      padding: "14px 16px",
                      color: "#D4AF37",
                      fontSize: "0.75rem",
                      fontWeight: 800,
                      textTransform: "uppercase",
                      textAlign: "right",
                    }}
                  >
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody>
                {companies.map((c) => {
                  const stageObj = LIFECYCLE_STAGES.find((s) => s.value === c.lifecycle_stage);
                  return (
                    <tr
                      key={c.id}
                      style={{
                        borderBottom: "1px solid rgba(255, 255, 255, 0.05)",
                        transition: "background 0.15s ease",
                      }}
                      onMouseEnter={(e) =>
                        (e.currentTarget.style.background = "rgba(15, 107, 109, 0.12)")
                      }
                      onMouseLeave={(e) => (e.currentTarget.style.background = "transparent")}
                    >
                      <td style={{ padding: "16px", color: "#F8F8F5", fontWeight: 700 }}>
                        <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                          <div
                            style={{
                              width: "36px",
                              height: "36px",
                              borderRadius: "10px",
                              background:
                                "linear-gradient(135deg, rgba(212, 175, 55, 0.2), rgba(15, 107, 109, 0.3))",
                              display: "flex",
                              alignItems: "center",
                              justifyContent: "center",
                              fontWeight: 800,
                              color: "#D4AF37",
                              border: "1px solid rgba(212, 175, 55, 0.3)",
                            }}
                          >
                            {c.name.slice(0, 2).toUpperCase()}
                          </div>
                          <div>
                            <div>{c.name}</div>
                            {c.phone && (
                              <div
                                style={{ fontSize: "0.75rem", color: "#8E9C9D", fontWeight: 400 }}
                              >
                                📞 {c.phone}
                              </div>
                            )}
                          </div>
                        </div>
                      </td>
                      <td style={{ padding: "16px", color: "#8E9C9D", fontSize: "0.85rem" }}>
                        {c.domain ? (
                          <span
                            style={{
                              background: "rgba(15, 107, 109, 0.25)",
                              padding: "2px 8px",
                              borderRadius: "6px",
                              border: "1px solid rgba(15, 107, 109, 0.4)",
                              color: "#A2C3C4",
                              fontFamily: "var(--font-mono, monospace)",
                            }}
                          >
                            {c.domain}
                          </span>
                        ) : c.website ? (
                          <a
                            href={c.website.startsWith("http") ? c.website : `https://${c.website}`}
                            target="_blank"
                            rel="noreferrer"
                            style={{ color: "#D4AF37", textDecoration: "none" }}
                          >
                            {c.website} ↗
                          </a>
                        ) : (
                          "—"
                        )}
                      </td>
                      <td style={{ padding: "16px", color: "#F8F8F5", fontSize: "0.85rem" }}>
                        {c.industry || "General"}
                      </td>
                      <td style={{ padding: "16px" }}>
                        <span
                          style={{
                            display: "inline-block",
                            padding: "3px 10px",
                            borderRadius: "999px",
                            fontSize: "0.72rem",
                            fontWeight: 800,
                            letterSpacing: "0.05em",
                            background: stageObj?.color || "rgba(255, 255, 255, 0.1)",
                            color: "#F8F8F5",
                            border: "1px solid rgba(255, 255, 255, 0.15)",
                          }}
                        >
                          {stageObj?.label || c.lifecycle_stage}
                        </span>
                      </td>
                      <td style={{ padding: "16px" }}>
                        <Link
                          href={`/dashboard/contacts?company_id=${c.id}`}
                          style={{
                            display: "inline-flex",
                            alignItems: "center",
                            gap: "6px",
                            background: "rgba(212, 175, 55, 0.15)",
                            border: "1px solid rgba(212, 175, 55, 0.3)",
                            color: "#D4AF37",
                            padding: "3px 10px",
                            borderRadius: "999px",
                            fontSize: "0.75rem",
                            fontWeight: 700,
                            textDecoration: "none",
                          }}
                        >
                          👥 {c.contacts_count} contacts
                        </Link>
                      </td>
                      <td style={{ padding: "16px", textAlign: "right" }}>
                        <div style={{ display: "inline-flex", gap: "8px" }}>
                          <button
                            onClick={() => openEdit(c)}
                            style={{
                              background: "rgba(255, 255, 255, 0.08)",
                              border: "1px solid rgba(255, 255, 255, 0.15)",
                              color: "#F8F8F5",
                              padding: "5px 12px",
                              borderRadius: "6px",
                              cursor: "pointer",
                              fontSize: "0.78rem",
                              fontWeight: 600,
                            }}
                          >
                            Edit
                          </button>
                          <button
                            onClick={() => setDeleteTarget(c)}
                            style={{
                              background: "rgba(239, 68, 68, 0.15)",
                              border: "1px solid rgba(239, 68, 68, 0.3)",
                              color: "#f87171",
                              padding: "5px 12px",
                              borderRadius: "6px",
                              cursor: "pointer",
                              fontSize: "0.78rem",
                              fontWeight: 600,
                            }}
                          >
                            Delete
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Create / Edit Modal */}
      {isCreateOpen && (
        <div
          style={{
            position: "fixed",
            inset: 0,
            background: "rgba(4, 15, 16, 0.82)",
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
              maxWidth: "520px",
              width: "100%",
              boxShadow: "0 20px 60px rgba(0,0,0,0.8)",
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                marginBottom: "20px",
              }}
            >
              <h2 style={{ color: "#F8F8F5", fontSize: "1.25rem", fontWeight: 800 }}>
                {editingCompany ? "Edit Company Account" : "Add New Company"}
              </h2>
              <button
                onClick={() => setIsCreateOpen(false)}
                style={{
                  background: "none",
                  border: "none",
                  color: "#8E9C9D",
                  fontSize: "1.2rem",
                  cursor: "pointer",
                }}
              >
                ✕
              </button>
            </div>

            {errorMsg && (
              <div
                style={{
                  background: "rgba(239, 68, 68, 0.15)",
                  border: "1px solid rgba(239, 68, 68, 0.4)",
                  color: "#fca5a5",
                  padding: "10px 14px",
                  borderRadius: "8px",
                  fontSize: "0.85rem",
                  marginBottom: "16px",
                }}
              >
                ⚠️ {errorMsg}
              </div>
            )}

            <form onSubmit={handleCreateOrUpdate}>
              <div style={{ display: "flex", flexDirection: "column", gap: "14px" }}>
                <div>
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
                    Company Name *
                  </label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. Acme Corporation"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    className={shared.searchInput}
                    style={{ width: "100%" }}
                  />
                </div>

                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px" }}>
                  <div>
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
                      Domain (for dedup)
                    </label>
                    <input
                      type="text"
                      placeholder="acme.com"
                      value={formData.domain}
                      onChange={(e) => setFormData({ ...formData, domain: e.target.value })}
                      className={shared.searchInput}
                      style={{ width: "100%" }}
                    />
                  </div>
                  <div>
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
                      Industry
                    </label>
                    <input
                      type="text"
                      placeholder="e.g. SaaS / FinTech"
                      value={formData.industry}
                      onChange={(e) => setFormData({ ...formData, industry: e.target.value })}
                      className={shared.searchInput}
                      style={{ width: "100%" }}
                    />
                  </div>
                </div>

                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px" }}>
                  <div>
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
                      Website
                    </label>
                    <input
                      type="text"
                      placeholder="https://acme.com"
                      value={formData.website}
                      onChange={(e) => setFormData({ ...formData, website: e.target.value })}
                      className={shared.searchInput}
                      style={{ width: "100%" }}
                    />
                  </div>
                  <div>
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
                      Phone
                    </label>
                    <input
                      type="text"
                      placeholder="+1 (555) 019-2834"
                      value={formData.phone}
                      onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                      className={shared.searchInput}
                      style={{ width: "100%" }}
                    />
                  </div>
                </div>

                <div>
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
                    Lifecycle Stage
                  </label>
                  <select
                    value={formData.lifecycle_stage}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        lifecycle_stage: e.target.value as CompanyLifecycleStage,
                      })
                    }
                    className={shared.searchInput}
                    style={{ width: "100%", background: "#061819" }}
                  >
                    {LIFECYCLE_STAGES.map((s) => (
                      <option key={s.value} value={s.value}>
                        {s.label}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
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
                    Address / Notes
                  </label>
                  <input
                    type="text"
                    placeholder="City, Country or headquarters location"
                    value={formData.address}
                    onChange={(e) => setFormData({ ...formData, address: e.target.value })}
                    className={shared.searchInput}
                    style={{ width: "100%" }}
                  />
                </div>

                <div
                  style={{
                    display: "flex",
                    justifyContent: "flex-end",
                    gap: "10px",
                    marginTop: "14px",
                  }}
                >
                  <button
                    type="button"
                    onClick={() => setIsCreateOpen(false)}
                    disabled={submitting}
                    style={{
                      background: "rgba(255, 255, 255, 0.08)",
                      border: "none",
                      color: "#F8F8F5",
                      padding: "10px 18px",
                      borderRadius: "999px",
                      fontWeight: 600,
                      cursor: "pointer",
                    }}
                  >
                    Cancel
                  </button>
                  <button type="submit" disabled={submitting} className={shared.primaryButton}>
                    {submitting ? "Saving..." : editingCompany ? "Save Changes" : "Create Company"}
                  </button>
                </div>
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
              Delete Company Record?
            </h3>
            <p
              style={{
                color: "#8E9C9D",
                fontSize: "0.88rem",
                marginBottom: "20px",
                lineHeight: 1.5,
              }}
            >
              Are you sure you want to remove <strong>{deleteTarget.name}</strong>? Linked contacts
              will not be deleted, but will become unassigned.
            </p>
            <div style={{ display: "flex", justifyContent: "flex-end", gap: "10px" }}>
              <button
                onClick={() => setDeleteTarget(null)}
                disabled={submitting}
                style={{
                  background: "rgba(255, 255, 255, 0.08)",
                  border: "none",
                  color: "#F8F8F5",
                  padding: "8px 16px",
                  borderRadius: "999px",
                  fontWeight: 600,
                  cursor: "pointer",
                }}
              >
                Cancel
              </button>
              <button
                onClick={handleDelete}
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
