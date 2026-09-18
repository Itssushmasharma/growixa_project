"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import styles from "./agency-detail.module.css";
import { getAgency, fetchAgencyClients, AgencyOut, ClientOut } from "@/lib/api/agency";
import { ClientList } from "@/components/agency/ClientList";

export default function AgencyDetailPage({ params }: { params: { agencyId: string } }) {
  const [agency, setAgency] = useState<AgencyOut | null>(null);
  const [clients, setClients] = useState<ClientOut[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<"clients" | "team">("clients");

  useEffect(() => {
    async function loadData() {
      try {
        setLoading(true);
        const [agencyData, clientsData] = await Promise.all([
          getAgency(params.agencyId),
          fetchAgencyClients(params.agencyId),
        ]);
        setAgency(agencyData);
        setClients(clientsData);
      } catch (err) {
        console.error("Failed to load agency details", err);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, [params.agencyId]);

  if (loading) return <div className={styles.container}>Loading agency details...</div>;
  if (!agency) return <div className={styles.container}>Agency not found.</div>;

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <Link href="/dashboard/agencies" className={styles.backLink}>
          &larr; Back to Agencies
        </Link>
        <h1 className={styles.title}>{agency.name}</h1>
        <div className={styles.meta}>
          {agency.custom_domain || agency.subdomain || "No domain set"} &bull; Created {new Date(agency.created_at).toLocaleDateString()}
        </div>
      </div>

      <div className={styles.tabs}>
        <div
          className={`${styles.tab} ${activeTab === "clients" ? styles.tabActive : ""}`}
          onClick={() => setActiveTab("clients")}
        >
          Clients
        </div>
        <div
          className={`${styles.tab} ${activeTab === "team" ? styles.tabActive : ""}`}
          onClick={() => setActiveTab("team")}
        >
          Team Members
        </div>
      </div>

      {activeTab === "clients" && (
        <div className={styles.section}>
          <div className={styles.sectionHeader}>
            <h2 className={styles.sectionTitle}>Onboarded Clients</h2>
            <Link href={`/dashboard/agencies/${agency.id}/white-label`} className={styles.linkButton}>
              White-label Settings
            </Link>
          </div>
          <ClientList clients={clients} />
        </div>
      )}

      {activeTab === "team" && (
        <div className={styles.section}>
          <div className={styles.sectionHeader}>
            <h2 className={styles.sectionTitle}>Team Members</h2>
            <button className={styles.linkButton} style={{ border: 'none', cursor: 'pointer' }}>+ Invite</button>
          </div>
          <p style={{ color: '#6b7280' }}>Team management coming soon.</p>
        </div>
      )}
    </div>
  );
}
