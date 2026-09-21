"use client";

import React, { useState } from "react";
import { Target, DollarSign, TrendingUp, Link as LinkIcon, Plus, Check } from "lucide-react";
import styles from "./ads-hub.module.css";

export default function AdsHubPage() {
  const [campaigns] = useState([
    {
      id: "ad_camp_01",
      name: "Q4 Outbound SaaS Lead Gen",
      platform: "Google Ads",
      budget: "$150 / day",
      clicks: "1,420",
      conversions: "184",
      spend: "$680.00",
      roas: "3.42x",
    },
    {
      id: "ad_camp_02",
      name: "Instagram Retargeting Reel",
      platform: "Meta Ads",
      budget: "$75 / day",
      clicks: "980",
      conversions: "112",
      spend: "$320.00",
      roas: "4.15x",
    },
  ]);

  const [destUrl, setDestUrl] = useState("https://growixa.com/pricing");
  const [source, setSource] = useState("google");
  const [medium, setMedium] = useState("cpc");
  const [campaignName, setCampaignName] = useState("q4_outbound");
  const [generatedUtm, setGeneratedUtm] = useState("");

  const handleBuildUtm = () => {
    setGeneratedUtm(`${destUrl}?utm_source=${source}&utm_medium=${medium}&utm_campaign=${campaignName}`);
  };

  return (
    <div className={styles.container}>
      <header className={styles.header}>
        <div>
          <span className={styles.eyebrow}><Target className="w-3.5 h-3.5" /> Google &amp; Meta Ads Workspace</span>
          <h1 className={styles.title}>Unified PPC Ads Hub</h1>
          <p className={styles.subtitle}>
            Plan ad campaigns across Google Ads and Meta Ads, manage daily budgets, build UTM tracking links, and measure ROAS.
          </p>
        </div>

        <button type="button" className={styles.primaryBtn}>
          <Plus className="w-4 h-4" /> Create Ad Campaign
        </button>
      </header>

      {/* Campaigns List */}
      <div className={styles.card}>
        <div className={styles.cardHeader}>
          <TrendingUp className="w-5 h-5 text-rose-700" />
          <h2>Active Ad Campaigns</h2>
        </div>

        <div className={styles.tableWrap}>
          <table className={styles.table}>
            <thead>
              <tr>
                <th>Campaign Name</th>
                <th>Platform</th>
                <th>Daily Budget</th>
                <th>Clicks</th>
                <th>Conversions</th>
                <th>Spend</th>
                <th>ROAS</th>
              </tr>
            </thead>
            <tbody>
              {campaigns.map((c) => (
                <tr key={c.id}>
                  <td><strong>{c.name}</strong></td>
                  <td><span className={styles.platformTag}>{c.platform}</span></td>
                  <td>{c.budget}</td>
                  <td>{c.clicks}</td>
                  <td><strong>{c.conversions}</strong></td>
                  <td>{c.spend}</td>
                  <td><span className={styles.roasTag}>{c.roas}</span></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* UTM Link Builder Box */}
      <div className={styles.card} style={{ marginTop: 28 }}>
        <div className={styles.cardHeader}>
          <LinkIcon className="w-5 h-5 text-rose-700" />
          <h2>UTM Campaign Tracking Link Generator</h2>
        </div>

        <div className={styles.utmFormGrid}>
          <div>
            <label className={styles.label}>Destination URL</label>
            <input
              type="text"
              className={styles.input}
              value={destUrl}
              onChange={(e) => setDestUrl(e.target.value)}
            />
          </div>
          <div>
            <label className={styles.label}>UTM Source</label>
            <input
              type="text"
              className={styles.input}
              value={source}
              onChange={(e) => setSource(e.target.value)}
            />
          </div>
          <div>
            <label className={styles.label}>UTM Medium</label>
            <input
              type="text"
              className={styles.input}
              value={medium}
              onChange={(e) => setMedium(e.target.value)}
            />
          </div>
          <div>
            <label className={styles.label}>Campaign Name</label>
            <input
              type="text"
              className={styles.input}
              value={campaignName}
              onChange={(e) => setCampaignName(e.target.value)}
            />
          </div>
        </div>

        <button type="button" className={styles.secondaryBtn} onClick={handleBuildUtm}>
          Build Tracking Link
        </button>

        {generatedUtm && (
          <div className={styles.utmResult}>
            <span>{generatedUtm}</span>
          </div>
        )}
      </div>
    </div>
  );
}
