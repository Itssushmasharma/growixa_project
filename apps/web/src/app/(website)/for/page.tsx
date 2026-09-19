import React from "react";
import Link from "next/link";
import { Building2, ShoppingCart, Rocket, Users } from "lucide-react";
import styles from "./for.module.css";

export default function SolutionsPage() {
  return (
    <main className={styles.page}>
      <header className={styles.header}>
        <span className={styles.eyebrow}>Solutions</span>
        <h1 className={styles.title}>Growixa for Every Team</h1>
        <p className={styles.subtitle}>
          Whether you&apos;re a fast-growing startup or an established enterprise, Growixa adapts to your specific marketing needs and workflows.
        </p>
      </header>

      <div className={styles.grid}>
        {/* Agencies */}
        <Link href="/for/agencies" className={styles.card}>
          <div className={styles.cardIcon}>
            <Building2 size={36} />
          </div>
          <h2 className={styles.cardTitle}>For Agencies</h2>
          <p className={styles.cardDesc}>
            Manage multiple client accounts from a single dashboard. Utilize built-in approval workflows, white-labeled reporting, and team roles to scale your agency operations efficiently.
          </p>
          <div className={styles.cardLink}>
            Explore Agency Solutions <span>→</span>
          </div>
        </Link>

        {/* E-commerce */}
        <Link href="/for/ecommerce" className={styles.card}>
          <div className={styles.cardIcon}>
            <ShoppingCart size={36} />
          </div>
          <h2 className={styles.cardTitle}>For E-Commerce</h2>
          <p className={styles.cardDesc}>
            Drive more sales with automated abandoned cart recovery, dynamic product retargeting, and highly personalized email & SMS campaigns based on purchase history.
          </p>
          <div className={styles.cardLink}>
            Explore E-Commerce Solutions <span>→</span>
          </div>
        </Link>

        {/* Startups */}
        <Link href="/for/startups" className={styles.card}>
          <div className={styles.cardIcon}>
            <Rocket size={36} />
          </div>
          <h2 className={styles.cardTitle}>For Startups</h2>
          <p className={styles.cardDesc}>
            Maximize your marketing ROI with limited resources. Automate your growth engine and reach the right audience without needing a massive marketing team.
          </p>
          <div className={styles.cardLink}>
            Explore Startup Solutions <span>→</span>
          </div>
        </Link>

        {/* Enterprise */}
        <Link href="/for/enterprise" className={styles.card}>
          <div className={styles.cardIcon}>
            <Users size={36} />
          </div>
          <h2 className={styles.cardTitle}>For Enterprise</h2>
          <p className={styles.cardDesc}>
            Secure, compliant, and scalable. Leverage advanced custom APIs, dedicated support, and strict role-based access controls designed for large organizations.
          </p>
          <div className={styles.cardLink}>
            Explore Enterprise Solutions <span>→</span>
          </div>
        </Link>
      </div>
    </main>
  );
}
