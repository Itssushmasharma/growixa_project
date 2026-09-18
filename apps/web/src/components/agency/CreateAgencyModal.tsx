"use client";

import React, { useState } from "react";
import styles from "./create-agency-modal.module.css";
import { createAgency } from "../../lib/api/agency";

interface CreateAgencyModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

export function CreateAgencyModal({ isOpen, onClose, onSuccess }: CreateAgencyModalProps) {
  const [name, setName] = useState("");
  const [subdomain, setSubdomain] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      await createAgency({ name, subdomain: subdomain || null });
      onSuccess();
      onClose();
      setName("");
      setSubdomain("");
    } catch (err: unknown) {
      const error = err as Error;
      setError(error.message || "Failed to create agency");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={styles.overlay}>
      <div className={styles.modal} role="dialog" aria-modal="true">
        <h2 className={styles.title}>Create New Agency</h2>
        <form onSubmit={handleSubmit}>
          <div className={styles.formGroup}>
            <label className={styles.label} htmlFor="agency-name">
              Agency Name *
            </label>
            <input
              id="agency-name"
              type="text"
              className={styles.input}
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
              placeholder="E.g. Acme Marketing"
            />
          </div>
          <div className={styles.formGroup}>
            <label className={styles.label} htmlFor="agency-subdomain">
              Subdomain (optional)
            </label>
            <input
              id="agency-subdomain"
              type="text"
              className={styles.input}
              value={subdomain}
              onChange={(e) => setSubdomain(e.target.value)}
              placeholder="acme"
            />
          </div>
          {error && <div style={{ color: "red", fontSize: "0.875rem" }}>{error}</div>}
          <div className={styles.actions}>
            <button
              type="button"
              className={`${styles.button} ${styles.cancel}`}
              onClick={onClose}
              disabled={loading}
            >
              Cancel
            </button>
            <button
              type="submit"
              className={`${styles.button} ${styles.submit}`}
              disabled={loading || !name}
            >
              {loading ? "Creating..." : "Create Agency"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
