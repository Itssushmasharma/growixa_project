"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { PageHeader } from "@/components/page-header/page-header";
import { useToast } from "@/components/toast/toast-context";
import { apiFetch } from "@/lib/api-client";
import styles from "../integrations-page.module.css";

export default function SMSIntegrationPage() {
  const router = useRouter();
  const { showToast } = useToast();
  const [saving, setSaving] = useState(false);
  
  const [form, setForm] = useState({
    provider: "TWILIO",
    account_sid: "",
    auth_token: "",
    sender_number: ""
  });

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    try {
      await apiFetch("/sms/connections", {
        method: "POST",
        body: JSON.stringify(form)
      });
      showToast("success", "SMS Provider connected successfully!");
      router.push("/dashboard/integrations");
    } catch {
      showToast("error", "Failed to connect SMS Provider.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className={styles.page}>
      <PageHeader
        icon="📱"
        title="Connect SMS Provider"
        description="Link your Twilio account to send SMS text message campaigns."
      />
      <div className={styles.grid}>
        <form className={styles.form} onSubmit={handleSubmit}>
          <div className={styles.field}>
            <label className={styles.label}>Provider</label>
            <select className={styles.select} value={form.provider} onChange={e => setForm({...form, provider: e.target.value})}>
              <option value="TWILIO">Twilio</option>
            </select>
          </div>
          <div className={styles.field}>
            <label className={styles.label}>Account SID</label>
            <input required className={styles.input} value={form.account_sid} onChange={e => setForm({...form, account_sid: e.target.value})} />
          </div>
          <div className={styles.field}>
            <label className={styles.label}>Auth Token</label>
            <input type="password" required className={styles.input} value={form.auth_token} onChange={e => setForm({...form, auth_token: e.target.value})} />
          </div>
          <div className={styles.field}>
            <label className={styles.label}>Sender Phone Number</label>
            <input required className={styles.input} placeholder="+1234567890" value={form.sender_number} onChange={e => setForm({...form, sender_number: e.target.value})} />
          </div>
          <div className={styles.formActions}>
            <button type="submit" disabled={saving} className={styles.actionButton}>
              {saving ? "Connecting..." : "Connect SMS"}
            </button>
            <button type="button" onClick={() => router.back()} className={styles.secondaryButton}>
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
