import React from "react";
import styles from "./security-reliability.module.css";
import { Shield, Lock, FileCheck, CheckCircle2, ChevronRight } from "lucide-react";

export function SecurityReliabilitySection() {
  const NODES = [
    {
      num: "01",
      title: "SOC2 Ready Architecture",
      subtitle: "B2B TENANT CONTROLS",
      icon: <Shield className="w-8 h-8 text-rose-800" />,
      desc: "Adheres to strict enterprise security standards with multi-tenant data isolation and key segregation.",
      bullets: [
        "Account-level tenant data isolation",
        "Strict RBAC permission enforcement",
        "Zero hardcoded API credentials scan"
      ]
    },
    {
      num: "02",
      title: "GDPR & Privacy Guard",
      subtitle: "COMPLIANCE ENGINE",
      icon: <FileCheck className="w-8 h-8 text-rose-800" />,
      desc: "Automated compliance mechanisms for list opt-outs, data rights, and domain suppression.",
      bullets: [
        "RFC 8058 one-click List-Unsubscribe headers",
        "Wildcard domain blocklist filters",
        "CSV import/export & soft-delete rights"
      ]
    },
    {
      num: "03",
      title: "Encryption & Audit Logs",
      subtitle: "CRYPTOGRAPHIC AUDIT",
      icon: <Lock className="w-8 h-8 text-rose-800" />,
      desc: "End-to-end payload protection with immutable insert-only event audit trails.",
      bullets: [
        "Fernet symmetric payload encryption at rest",
        "Argon2id password hashing with salt",
        "Append-only immutable audit logging"
      ]
    }
  ];

  return (
    <section className={styles.section} id="security">
      <div className={styles.header}>
        <div className={styles.eyebrow}>
          <Shield className="w-4 h-4" /> Enterprise Security
        </div>
        <h2 className={styles.title}>
          Enterprise Reliability — <span>Built with Bank-Grade Security</span>
        </h2>
        <p className={styles.subtitle}>
          Protect your customer data and ensure delivery compliance with end-to-end encryption and audit logging.
        </p>
      </div>

      {/* 3D Rectangular Process Cards with Interlocking 3D Tabs (Reference Image 2) */}
      <div className={styles.processContainer}>
        {NODES.map((node, idx) => (
          <React.Fragment key={node.num}>
            <div className={styles.processCard}>
              {/* Top Step Number Badge */}
              <div className={styles.numBadge}>{node.num}</div>

              {/* Icon Container */}
              <div className={styles.iconBox}>{node.icon}</div>

              {/* Title & Subtitle */}
              <span className={styles.cardSubtitle}>{node.subtitle}</span>
              <h3 className={styles.cardTitle}>{node.title}</h3>

              {/* Description */}
              <p className={styles.cardDesc}>{node.desc}</p>

              {/* Feature Bullet Items */}
              <div className={styles.bulletList}>
                {node.bullets.map((b, bIdx) => (
                  <div key={bIdx} className={styles.bulletItem}>
                    <CheckCircle2 className="w-4 h-4 text-rose-700 flex-shrink-0" />
                    <span>{b}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Interlocking 3D Arrow Connector Tab (Between cards 01-02 and 02-03) */}
            {idx < NODES.length - 1 && (
              <div className={styles.tabConnector} aria-hidden="true">
                <div className={styles.tabInner}>
                  <ChevronRight className="w-6 h-6 text-white" />
                </div>
              </div>
            )}
          </React.Fragment>
        ))}
      </div>
    </section>
  );
}
