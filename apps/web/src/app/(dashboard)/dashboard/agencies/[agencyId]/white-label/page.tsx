"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import styles from "./white-label.module.css";
import { getAgency, updateAgencyWhiteLabel, AgencyOut } from "@/lib/api/agency";

export default function WhiteLabelPage({ params }: { params: { agencyId: string } }) {
  const [agency, setAgency] = useState<AgencyOut | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState("");

  const [formData, setFormData] = useState({
    portal_name: "",
    portal_logo_url: "",
    custom_domain: "",
    brand_color_primary: "#2563eb",
    brand_color_secondary: "#1d4ed8",
  });

  useEffect(() => {
    async function loadData() {
      try {
        const data = await getAgency(params.agencyId);
        setAgency(data);
        setFormData({
          portal_name: data.portal_name || "",
          portal_logo_url: data.portal_logo_url || "",
          custom_domain: data.custom_domain || "",
          brand_color_primary: data.brand_color_primary || "#2563eb",
          brand_color_secondary: data.brand_color_secondary || "#1d4ed8",
        });
      } catch (err) {
        console.error("Failed to load agency:", err);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, [params.agencyId]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setMessage("");
    try {
      const updated = await updateAgencyWhiteLabel(params.agencyId, formData);
      setAgency(updated);
      setMessage("White-label settings updated successfully.");
    } catch (err: unknown) {
      const error = err as Error;
      setMessage(`Error: ${error.message || "Failed to update"}`);
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <div className={styles.container}>Loading settings...</div>;
  if (!agency) return <div className={styles.container}>Agency not found.</div>;

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <Link href={`/dashboard/agencies/${agency.id}`} className={styles.backLink}>
          &larr; Back to Agency Details
        </Link>
        <h1 className={styles.title}>White-Label Settings</h1>
      </div>

      <div className={styles.card}>
        <form onSubmit={handleSubmit}>
          <div className={styles.formGroup}>
            <label className={styles.label} htmlFor="portal_name">Portal Name</label>
            <input
              id="portal_name"
              name="portal_name"
              type="text"
              className={styles.input}
              value={formData.portal_name}
              onChange={handleChange}
              placeholder="e.g. Acme Client Portal"
            />
            <span className={styles.helpText}>This name will appear on the client dashboard.</span>
          </div>

          <div className={styles.formGroup}>
            <label className={styles.label} htmlFor="custom_domain">Custom Domain</label>
            <input
              id="custom_domain"
              name="custom_domain"
              type="text"
              className={styles.input}
              value={formData.custom_domain}
              onChange={handleChange}
              placeholder="app.youragency.com"
            />
            <span className={styles.helpText}>CNAME record must be pointed to our servers.</span>
          </div>

          <div className={styles.formGroup}>
            <label className={styles.label} htmlFor="portal_logo_url">Logo URL</label>
            <input
              id="portal_logo_url"
              name="portal_logo_url"
              type="url"
              className={styles.input}
              value={formData.portal_logo_url}
              onChange={handleChange}
              placeholder="https://example.com/logo.png"
            />
          </div>

          <div className={styles.formGroup}>
            <label className={styles.label}>Brand Colors</label>
            <div className={styles.colorInputs}>
              <div className={styles.colorWrapper}>
                <input
                  type="color"
                  name="brand_color_primary"
                  value={formData.brand_color_primary}
                  onChange={handleChange}
                />
                <span>Primary</span>
              </div>
              <div className={styles.colorWrapper}>
                <input
                  type="color"
                  name="brand_color_secondary"
                  value={formData.brand_color_secondary}
                  onChange={handleChange}
                />
                <span>Secondary</span>
              </div>
            </div>
          </div>

          {message && (
            <div style={{ color: message.startsWith("Error") ? "red" : "green", marginBottom: "16px" }}>
              {message}
            </div>
          )}

          <div className={styles.actions}>
            <button type="submit" className={`${styles.button} ${styles.submit}`} disabled={saving}>
              {saving ? "Saving..." : "Save Settings"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
