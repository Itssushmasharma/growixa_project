import React from "react";
import styles from "./client-list.module.css";
import { ClientOut } from "../../lib/api/agency";

interface ClientListProps {
  clients: ClientOut[];
}

export function ClientList({ clients }: ClientListProps) {
  if (clients.length === 0) {
    return (
      <div className={styles.tableWrapper}>
        <div className={styles.emptyState}>No clients onboarded yet.</div>
      </div>
    );
  }

  return (
    <div className={styles.tableWrapper}>
      <table className={styles.table}>
        <thead>
          <tr>
            <th className={styles.th}>Company Name</th>
            <th className={styles.th}>Industry</th>
            <th className={styles.th}>Website</th>
            <th className={styles.th}>Joined</th>
          </tr>
        </thead>
        <tbody>
          {clients.map((client) => (
            <tr key={client.id} className={styles.tr}>
              <td className={styles.td}>{client.company_name}</td>
              <td className={styles.td}>{client.industry || "-"}</td>
              <td className={styles.td}>
                {client.website_url ? (
                  <a href={client.website_url} target="_blank" rel="noreferrer">
                    {client.website_url}
                  </a>
                ) : (
                  "-"
                )}
              </td>
              <td className={styles.td}>
                {new Date(client.created_at).toLocaleDateString()}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
