"use client";

import React, { useEffect, useState } from "react";
import styles from "./agencies.module.css";
import { AgencyCard } from "@/components/agency/AgencyCard";
import { CreateAgencyModal } from "@/components/agency/CreateAgencyModal";
import { fetchAgencies, AgencyOut } from "@/lib/api/agency";

export default function AgenciesPage() {
  const [agencies, setAgencies] = useState<AgencyOut[]>([]);
  const [loading, setLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);

  const loadAgencies = async () => {
    try {
      setLoading(true);
      const data = await fetchAgencies();
      setAgencies(data);
    } catch (err) {
      console.error("Failed to load agencies:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAgencies();
  }, []);

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h1 className={styles.title}>My Agencies</h1>
        <button className={styles.button} onClick={() => setIsModalOpen(true)}>
          + Create Agency
        </button>
      </div>

      {loading ? (
        <div>Loading agencies...</div>
      ) : agencies.length > 0 ? (
        <div className={styles.grid}>
          {agencies.map((agency) => (
            <AgencyCard key={agency.id} agency={agency} />
          ))}
        </div>
      ) : (
        <div className={styles.emptyState}>
          <h3 className={styles.emptyTitle}>No Agencies Found</h3>
          <p className={styles.emptyDesc}>
            Get started by creating your first agency workspace to manage clients.
          </p>
          <button
            className={styles.button}
            onClick={() => setIsModalOpen(true)}
          >
            Create Agency
          </button>
        </div>
      )}

      <CreateAgencyModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onSuccess={loadAgencies}
      />
    </div>
  );
}
