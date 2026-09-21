"use client";

import React, { useState } from "react";
import { MessageSquare, Send, Mail, ShieldCheck, Plus, Check } from "lucide-react";
import styles from "./communications.module.css";

export default function CommunicationsPage() {
  const [templates] = useState([
    {
      id: "tpl_otp_01",
      name: "Secure Login 2FA OTP",
      channel: "OTP / SMS",
      header: "Verification Code",
      dlt: "DLT_14071612001920",
      body: "Your Growixa verification code is {{otp_code}}. Valid for 10 minutes.",
    },
    {
      id: "tpl_wa_01",
      name: "Order Confirmation & Tracking",
      channel: "WhatsApp API",
      header: "Order Dispatch",
      dlt: "WA_CAT_771829",
      body: "Hi {{first_name}}, your order #{{order_id}} has been shipped! Track here: {{tracking_url}}",
    },
    {
      id: "tpl_email_01",
      name: "Welcome Onboarding Sequence",
      channel: "Postmark Email",
      header: "Welcome to Growixa",
      dlt: "RFC 8058 Header Approved",
      body: "Hi {{first_name}}, welcome aboard! Let's set up your brand kit and launch your first AI campaign.",
    },
  ]);

  const [testRecipient, setTestRecipient] = useState("+91-9205067380");
  const [testChannel, setTestChannel] = useState("SMS");
  const [otpLog, setOtpLog] = useState("");

  const handleSendTestOtp = () => {
    const otp = Math.floor(100000 + Math.random() * 900000);
    setOtpLog(`[SUCCESS] Dispatched OTP code ${otp} to ${testRecipient} via ${testChannel} high-priority gateway.`);
  };

  return (
    <div className={styles.container}>
      <header className={styles.header}>
        <div>
          <span className={styles.eyebrow}><MessageSquare className="w-3.5 h-3.5" /> Omnichannel Communications Engine</span>
          <h1 className={styles.title}>SMS, WhatsApp API &amp; OTP Verification</h1>
          <p className={styles.subtitle}>
            Manage DLT-approved transactional SMS templates, WhatsApp Business API catalogs, 2FA OTP verification, and Postmark relays.
          </p>
        </div>

        <button type="button" className={styles.primaryBtn}>
          <Plus className="w-4 h-4" /> Create Notification Template
        </button>
      </header>

      {/* Templates Studio Card */}
      <div className={styles.card}>
        <div className={styles.cardHeader}>
          <ShieldCheck className="w-5 h-5 text-rose-700" />
          <h2>Approved Multi-Channel Notification Templates</h2>
        </div>

        <div className={styles.templateGrid}>
          {templates.map((t) => (
            <div key={t.id} className={styles.tplCard}>
              <div className={styles.tplTop}>
                <div>
                  <h3 className={styles.tplTitle}>{t.name}</h3>
                  <span className={styles.channelTag}>{t.channel}</span>
                </div>
                <span className={styles.dltTag}>{t.dlt}</span>
              </div>

              <div className={styles.bodyBox}>
                <p className={styles.bodyText}>&ldquo;{t.body}&rdquo;</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Live OTP Sandbox Tester Card */}
      <div className={styles.card} style={{ marginTop: 28 }}>
        <div className={styles.cardHeader}>
          <Send className="w-5 h-5 text-rose-700" />
          <h2>Sub-Second 2FA OTP Sandbox Tester</h2>
        </div>

        <div className={styles.testFormRow}>
          <div style={{ flex: 1 }}>
            <label className={styles.label}>Recipient Phone Number / Email</label>
            <input
              type="text"
              className={styles.input}
              value={testRecipient}
              onChange={(e) => setTestRecipient(e.target.value)}
            />
          </div>

          <div>
            <label className={styles.label}>Route Channel</label>
            <select
              className={styles.select}
              value={testChannel}
              onChange={(e) => setTestChannel(e.target.value)}
            >
              <option value="SMS">High-Priority SMS</option>
              <option value="WHATSAPP">WhatsApp API</option>
              <option value="EMAIL">Postmark Email</option>
            </select>
          </div>

          <button type="button" className={styles.secondaryBtn} onClick={handleSendTestOtp}>
            <Send className="w-4 h-4" /> Dispatch Test OTP
          </button>
        </div>

        {otpLog && (
          <div className={styles.logBox}>
            <span>{otpLog}</span>
          </div>
        )}
      </div>
    </div>
  );
}
