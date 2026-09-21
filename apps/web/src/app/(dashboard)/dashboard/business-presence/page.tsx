"use client";

import React, { useState } from "react";
import { Globe, Layout, Link as LinkIcon, ExternalLink, Plus, CheckCircle2 } from "lucide-react";
import styles from "./business-presence.module.css";

export default function BusinessPresencePage() {
  const [sites] = useState([
    {
      id: "site_01",
      title: "Growixa Product Launch Landing Page",
      slug: "grow-v2",
      url: "https://growixa.com/p/grow-v2",
      views: 3420,
      conversions: 412,
    },
  ]);

  const [links] = useState([
    { id: "link_01", title: "Book 1-on-1 Growth Demo", slug: "demo", clicks: 890 },
    { id: "link_02", title: "View Pricing & Upgrade Plans", slug: "pricing-link", clicks: 1240 },
  ]);

  return (
    <div className={styles.container}>
      <header className={styles.header}>
        <div>
          <span className={styles.eyebrow}><Globe className="w-3.5 h-3.5" /> Website &amp; Business Presence</span>
          <h1 className={styles.title}>Landing Page Builder &amp; Link Management</h1>
          <p className={styles.subtitle}>
            Build responsive landing pages, audit website SEO, manage social bio CTA links, and capture leads into CRM.
          </p>
        </div>

        <button type="button" className={styles.primaryBtn}>
          <Plus className="w-4 h-4" /> Create Landing Page
        </button>
      </header>

      <div className={styles.grid}>
        {/* Landing Pages Section */}
        <div className={styles.card}>
          <div className={styles.cardHeader}>
            <Layout className="w-5 h-5 text-rose-700" />
            <h2>Active Landing Pages</h2>
          </div>

          <div className={styles.list}>
            {sites.map((s) => (
              <div key={s.id} className={styles.listItem}>
                <div>
                  <h3 className={styles.itemTitle}>{s.title}</h3>
                  <a href={s.url} target="_blank" rel="noreferrer" className={styles.itemUrl}>
                    {s.url} <ExternalLink className="w-3 h-3 inline ml-1" />
                  </a>
                </div>

                <div className={styles.statRow}>
                  <div className={styles.statBadge}>
                    <span>Views</span>
                    <strong>{s.views.toLocaleString()}</strong>
                  </div>
                  <div className={styles.statBadge}>
                    <span>Conversions</span>
                    <strong>{s.conversions}</strong>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* CTA & Bio Links Section */}
        <div className={styles.card}>
          <div className={styles.cardHeader}>
            <LinkIcon className="w-5 h-5 text-rose-700" />
            <h2>Smart CTA &amp; Social Bio Links</h2>
          </div>

          <div className={styles.list}>
            {links.map((l) => (
              <div key={l.id} className={styles.listItem}>
                <div>
                  <h3 className={styles.itemTitle}>{l.title}</h3>
                  <span className={styles.slugBadge}>growixa.link/{l.slug}</span>
                </div>

                <div className={styles.statBadge}>
                  <span>Total Clicks</span>
                  <strong>{l.clicks.toLocaleString()}</strong>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
