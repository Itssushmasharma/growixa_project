"use client";

import React, { useState } from "react";
import { Workflow, Sparkles, CheckCircle2, Clock, Plus } from "lucide-react";
import styles from "./planner.module.css";

export default function MarketingPlannerPage() {
  const [tasks] = useState([
    { id: "t1", title: "Design Instagram Launch Carousel", channel: "Instagram", status: "IN_PROGRESS", owner: "Creative Studio" },
    { id: "t2", title: "Setup Postmark Transactional Email Relay", channel: "Email", status: "COMPLETED", owner: "DevOps / Tech" },
    { id: "t3", title: "Launch Google Ads High Intent Keyword Campaign", channel: "Google Ads", status: "TODO", owner: "Growth Team" },
  ]);

  return (
    <div className={styles.container}>
      <header className={styles.header}>
        <div>
          <span className={styles.eyebrow}><Workflow className="w-3.5 h-3.5" /> AI Growth &amp; Marketing Planner</span>
          <h1 className={styles.title}>Marketing Campaign Planner</h1>
          <p className={styles.subtitle}>
            Generate AI-powered GTM strategies, allocate channel budgets, assign team task workflows, and track execution.
          </p>
        </div>

        <button type="button" className={styles.primaryBtn}>
          <Sparkles className="w-4 h-4" /> Generate AI Strategy Plan
        </button>
      </header>

      <div className={styles.card}>
        <div className={styles.cardHeader}>
          <Clock className="w-5 h-5 text-rose-700" />
          <h2>GTM Execution Task Kanban</h2>
        </div>

        <div className={styles.taskList}>
          {tasks.map((t) => (
            <div key={t.id} className={styles.taskItem}>
              <div>
                <h3 className={styles.taskTitle}>{t.title}</h3>
                <div className={styles.metaRow}>
                  <span className={styles.channelBadge}>{t.channel}</span>
                  <span className={styles.ownerText}>Assigned to: <strong>{t.owner}</strong></span>
                </div>
              </div>

              <span className={`${styles.statusBadge} ${t.status === "COMPLETED" ? styles.statusDone : t.status === "IN_PROGRESS" ? styles.statusProg : styles.statusTodo}`}>
                {t.status.replace("_", " ")}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
