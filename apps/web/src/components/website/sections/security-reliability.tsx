import React from "react";
import styles from "./security-reliability.module.css";
import { Shield, Lock, FileCheck, CheckCircle2 } from "lucide-react";

export function SecurityReliabilitySection() {
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

      <div className={styles.grid}>
        {/* Card 1: SOC2 */}
        <div className={styles.card}>
          <div className={styles.iconShield}>
            <Shield className="w-7 h-7" />
          </div>
          <h3 className={styles.cardTitle}>SOC2 Ready Architecture</h3>
          <p className={styles.cardDesc}>
            Built adhering to strict B2B security and operational compliance controls with isolated tenant data keys.
          </p>
          <div className={styles.bulletList}>
            <div className={styles.bulletItem}>
              <CheckCircle2 className={`w-4 h-4 ${styles.bulletIcon}`} />
              Account-level data isolation (`account_id` enforced)
            </div>
            <div className={styles.bulletItem}>
              <CheckCircle2 className={`w-4 h-4 ${styles.bulletIcon}`} />
              Strict RBAC permission checks on every route
            </div>
            <div className={styles.bulletItem}>
              <CheckCircle2 className={`w-4 h-4 ${styles.bulletIcon}`} />
              Zero hardcoded secrets & automated CI security scanning
            </div>
          </div>
        </div>

        {/* Card 2: GDPR */}
        <div className={styles.card}>
          <div className={styles.iconShield}>
            <FileCheck className="w-7 h-7" />
          </div>
          <h3 className={styles.cardTitle}>GDPR & Opt-Out Handling</h3>
          <p className={styles.cardDesc}>
            Automated compliance tools for contact privacy, instant unsubscribe headers, and suppression lists.
          </p>
          <div className={styles.bulletList}>
            <div className={styles.bulletItem}>
              <CheckCircle2 className={`w-4 h-4 ${styles.bulletIcon}`} />
              RFC 8058 one-click inbox `List-Unsubscribe`
            </div>
            <div className={styles.bulletItem}>
              <CheckCircle2 className={`w-4 h-4 ${styles.bulletIcon}`} />
              Wildcard domain blocklists (`*@competitor.com`)
            </div>
            <div className={styles.bulletItem}>
              <CheckCircle2 className={`w-4 h-4 ${styles.bulletIcon}`} />
              CSV import/export & soft-deletion data rights
            </div>
          </div>
        </div>

        {/* Card 3: Bank Grade Encryption */}
        <div className={styles.card}>
          <div className={styles.iconShield}>
            <Lock className="w-7 h-7" />
          </div>
          <h3 className={styles.cardTitle}>Encryption & Audit Logging</h3>
          <p className={styles.cardDesc}>
            Cryptographic token protection, argon2id password hashing, and append-only audit event trails.
          </p>
          <div className={styles.bulletList}>
            <div className={styles.bulletItem}>
              <CheckCircle2 className={`w-4 h-4 ${styles.bulletIcon}`} />
              Fernet symmetric payload encryption at rest
            </div>
            <div className={styles.bulletItem}>
              <CheckCircle2 className={`w-4 h-4 ${styles.bulletIcon}`} />
              Argon2id password hashing with salt protection
            </div>
            <div className={styles.bulletItem}>
              <CheckCircle2 className={`w-4 h-4 ${styles.bulletIcon}`} />
              Immutable insert-only audit trail logging
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
