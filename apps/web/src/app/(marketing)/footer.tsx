import Link from "next/link";
import { BrandLogo } from "@/components/brand-logo";
import styles from "./marketing.module.css";

export function Footer() {
  return (
    <footer className={styles.footer}>
      <div className={styles.footerGrid}>
        <div>
          <Link href="/" className={styles.brand} style={{ color: "white", marginBottom: "1rem" }}>
            <BrandLogo width={28} height={28} />
            <span>Growixa</span>
          </Link>
          <p style={{ fontSize: "0.875rem", lineHeight: 1.6, color: "#94a3b8", maxWidth: "280px" }}>
            The AI Growth Platform for modern businesses. Automate marketing, AI copy generation,
            audience segmentation, and social publishing.
          </p>
        </div>

        <div>
          <div className={styles.footerColTitle}>Platform</div>
          <ul className={styles.footerLinks}>
            <li className={styles.footerLink}>
              <Link href="/features">Email Campaigns</Link>
            </li>
            <li className={styles.footerLink}>
              <Link href="/features">AI Marketing Team</Link>
            </li>
            <li className={styles.footerLink}>
              <Link href="/features">Audience Builder</Link>
            </li>
            <li className={styles.footerLink}>
              <Link href="/features">Social Scheduler</Link>
            </li>
          </ul>
        </div>

        <div>
          <div className={styles.footerColTitle}>Solutions</div>
          <ul className={styles.footerLinks}>
            <li className={styles.footerLink}>
              <Link href="/solutions">Growth Marketers</Link>
            </li>
            <li className={styles.footerLink}>
              <Link href="/solutions">Agencies</Link>
            </li>
            <li className={styles.footerLink}>
              <Link href="/solutions">SaaS Startups</Link>
            </li>
            <li className={styles.footerLink}>
              <Link href="/solutions">E-Commerce</Link>
            </li>
          </ul>
        </div>

        <div>
          <div className={styles.footerColTitle}>Resources</div>
          <ul className={styles.footerLinks}>
            <li className={styles.footerLink}>
              <Link href="/docs">API Documentation</Link>
            </li>
            <li className={styles.footerLink}>
              <Link href="/security">Security & Compliance</Link>
            </li>
            <li className={styles.footerLink}>
              <Link href="/pricing">Pricing Matrix</Link>
            </li>
          </ul>
        </div>

        <div>
          <div className={styles.footerColTitle}>Legal</div>
          <ul className={styles.footerLinks}>
            <li className={styles.footerLink}>
              <Link href="/security">Privacy Policy</Link>
            </li>
            <li className={styles.footerLink}>
              <Link href="/security">Terms of Service</Link>
            </li>
            <li className={styles.footerLink}>
              <Link href="/security">GDPR Opt-Out</Link>
            </li>
          </ul>
        </div>
      </div>

      <div className={styles.footerBottom}>
        <div>© {new Date().getFullYear()} Growixa Inc. All rights reserved.</div>
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: "0.5rem",
            color: "#10b981",
            fontWeight: 600,
          }}
        >
          <span
            style={{ width: "8px", height: "8px", borderRadius: "50%", background: "#10b981" }}
          />
          <span>All Systems Operational (99.99%)</span>
        </div>
      </div>
    </footer>
  );
}
