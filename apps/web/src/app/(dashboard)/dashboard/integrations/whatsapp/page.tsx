"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { PageHeader } from "@/components/page-header/page-header";
import { useToast } from "@/components/toast/toast-context";
import { apiFetch } from "@/lib/api-client";
import styles from "../integrations-page.module.css";

export default function WhatsAppIntegrationPage() {
  const router = useRouter();
  const { showToast } = useToast();
  const [saving, setSaving] = useState(false);
  
  const [form, setForm] = useState({
    waba_id: "",
    phone_number_id: "",
    access_token: "",
    webhook_verify_token: ""
  });

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    try {
      await apiFetch("/whatsapp/connections", {
        method: "POST",
        body: JSON.stringify(form)
      });
      showToast("success", "WhatsApp connected successfully!");
      router.push("/dashboard/integrations");
    } catch {
      showToast("error", "Failed to connect WhatsApp Provider.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className={styles.page}>
      <PageHeader
        icon="💬"
        title="Connect WhatsApp Business"
        description="Link your Meta Cloud API account to send WhatsApp messages and campaigns."
      />
      <div className={styles.grid}>
        <form className={styles.form} onSubmit={handleSubmit}>
          <div className={styles.field}>
            <label className={styles.label}>WhatsApp Business Account ID</label>
            <input required className={styles.input} value={form.waba_id} onChange={e => setForm({...form, waba_id: e.target.value})} />
          </div>
          <div className={styles.field}>
            <label className={styles.label}>Phone Number ID</label>
            <input required className={styles.input} value={form.phone_number_id} onChange={e => setForm({...form, phone_number_id: e.target.value})} />
          </div>
          <div className={styles.field}>
            <label className={styles.label}>System User Access Token</label>
            <input type="password" required className={styles.input} value={form.access_token} onChange={e => setForm({...form, access_token: e.target.value})} />
          </div>
          <div className={styles.field}>
            <label className={styles.label}>Webhook Verify Token</label>
            <input type="password" required className={styles.input} value={form.webhook_verify_token} onChange={e => setForm({...form, webhook_verify_token: e.target.value})} />
          </div>
          <div className={styles.formActions}>
            <button type="submit" disabled={saving} className={styles.actionButton}>
              {saving ? "Connecting..." : "Connect WhatsApp"}
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
