"use client";

import React, { useState } from "react";
import { UserCheck, Code, Plus, CheckCircle2 } from "lucide-react";
import styles from "./lead-gen.module.css";

export default function LeadGenPage() {
  const [forms] = useState([
    {
      id: "form_demo_01",
      title: "Homepage Growth Assessment Form",
      targetList: "Inbound Leads",
      submissions: 48,
      embedCode: '<iframe src="https://growixa.com/forms/embed/form_demo_01" width="100%" height="400"></iframe>',
    },
  ]);

  return (
    <div className={styles.container}>
      <header className={styles.header}>
        <div>
          <span className={styles.eyebrow}><UserCheck className="w-3.5 h-3.5" /> Lead Generation &amp; CRM Routing</span>
          <h1 className={styles.title}>Landing Page Lead Capture Studio</h1>
          <p className={styles.subtitle}>
            Create lead capture forms, track UTM source attribution, and route new leads into Growixa CRM lists automatically.
          </p>
        </div>

        <button type="button" className={styles.primaryBtn}>
          <Plus className="w-4 h-4" /> Build Lead Form
        </button>
      </header>

      <div className={styles.card}>
        <div className={styles.cardHeader}>
          <Code className="w-5 h-5 text-rose-700" />
          <h2>Lead Forms &amp; Embed Snippets</h2>
        </div>

        <div className={styles.formList}>
          {forms.map((f) => (
            <div key={f.id} className={styles.formCard}>
              <div className={styles.formTop}>
                <div>
                  <h3 className={styles.formTitle}>{f.title}</h3>
                  <span className={styles.targetListBadge}>Routes to: <strong>{f.targetList}</strong></span>
                </div>

                <div className={styles.subCountBadge}>
                  <span>Total Leads Captured</span>
                  <strong>{f.submissions}</strong>
                </div>
              </div>

              <div className={styles.embedBox}>
                <label className={styles.label}>HTML / iFrame Embed Snippet</label>
                <code className={styles.codeSnippet}>{f.embedCode}</code>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
