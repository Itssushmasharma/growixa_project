import React from "react";
import Link from "next/link";
import styles from "./agency-card.module.css";
import { AgencyOut } from "../../lib/api/agency";

interface AgencyCardProps {
  agency: AgencyOut;
}

export function AgencyCard({ agency }: AgencyCardProps) {
  const domain = agency.custom_domain || agency.subdomain || "No domain set";

  return (
    <Link href={`/dashboard/agencies/${agency.id}`} className={styles.card}>
      <div className={styles.header}>
        <h3 className={styles.name}>{agency.name}</h3>
        {domain && <span className={styles.domain}>{domain}</span>}
      </div>
      
      <div className={styles.meta}>
        <span>Created: {new Date(agency.created_at).toLocaleDateString()}</span>
      </div>

      <div className={styles.footer}>
        <span className={styles.button}>Manage Agency &rarr;</span>
      </div>
    </Link>
  );
}
