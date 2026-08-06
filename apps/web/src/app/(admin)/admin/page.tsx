"use client";

import { useEffect, useState } from "react";

import { useToast } from "@/components/toast/toast-context";
import { ApiError, apiFetch } from "@/lib/api-client";

import styles from "./admin-page.module.css";

export interface HealthResponse {
  status: "ok" | "degraded" | string;
  checks: {
    postgres: string;
    redis: string;
    rabbitmq: string;
  };
}

function parseApiErrorDetail(error: unknown, fallback: string): string {
  if (error instanceof ApiError) {
    try {
      const parsed = JSON.parse(error.message) as { detail?: string };
      if (parsed.detail) return parsed.detail;
    } catch {
      // Keep fallback
    }
  }
  return fallback;
}

export default function AdminHealthPage() {
  const { showToast } = useToast();
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [triggeringJob, setTriggeringJob] = useState(false);

  async function fetchHealth() {
    setLoading(true);
    setLoadError(null);
    try {
      const data = await apiFetch<HealthResponse>("/health");
      setHealth(data);
    } catch {
      setLoadError("Could not load system health checks.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void fetchHealth();
  }, []);

  async function handleTriggerJob() {
    setTriggeringJob(true);
    try {
      const res = await apiFetch<{ job_id: string }>("/system/jobs/healthcheck", {
        method: "POST",
      });
      showToast("success", `Healthcheck job enqueued (job_id: ${res.job_id})`);
    } catch (error) {
      showToast("error", parseApiErrorDetail(error, "Could not trigger healthcheck job."));
    } finally {
      setTriggeringJob(false);
    }
  }

  if (loading && !health) {
    return (
      <div className={styles.page}>
        <div className={styles.loadingCard}>Loading health checks…</div>
      </div>
    );
  }

  if (loadError && !health) {
    return (
      <div className={styles.page}>
        <div className={styles.loadingCard}>
          <p>{loadError}</p>
          <button type="button" className={styles.secondaryButton} onClick={fetchHealth}>
            Retry
          </button>
        </div>
      </div>
    );
  }

  const isOk = health?.status === "ok";

  return (
    <div className={styles.page}>
      <div className={styles.topRow}>
        <div>
          <h1 className={styles.title}>System Health</h1>
          <p className={styles.subtitle}>
            Monitor core infrastructure services and publish-consume pipeline readiness.
          </p>
        </div>
        <div className={styles.topActions}>
          <button
            type="button"
            className={styles.secondaryButton}
            onClick={fetchHealth}
            disabled={loading}
          >
            {loading ? "Refreshing…" : "Refresh"}
          </button>
          <button
            type="button"
            className={styles.actionButton}
            onClick={handleTriggerJob}
            disabled={triggeringJob}
          >
            {triggeringJob ? "Triggering…" : "Run healthcheck job"}
          </button>
        </div>
      </div>

      {health && (
        <div className={`${styles.banner} ${isOk ? styles.bannerOk : styles.bannerDegraded}`}>
          <span>
            {isOk
              ? "🟢 System Operational — All health checks are passing."
              : "⚠️ System Degraded — One or more health checks reported an error."}
          </span>
        </div>
      )}

      {health && (
        <div className={styles.grid}>
          <ServiceCard name="PostgreSQL Database" checkResult={health.checks.postgres} />
          <ServiceCard name="Redis Cache & Locks" checkResult={health.checks.redis} />
          <ServiceCard name="RabbitMQ Message Broker" checkResult={health.checks.rabbitmq} />
        </div>
      )}
    </div>
  );
}

function ServiceCard({ name, checkResult }: { name: string; checkResult: string }) {
  const isOk = checkResult === "ok";
  return (
    <div className={styles.card}>
      <div className={styles.cardHeader}>
        <span className={styles.serviceName}>{name}</span>
        <span className={`${styles.pill} ${isOk ? styles.pillOk : styles.pillError}`}>
          {isOk ? "OK" : "ERROR"}
        </span>
      </div>
      {!isOk && <div className={styles.checkDetail}>{checkResult}</div>}
    </div>
  );
}
