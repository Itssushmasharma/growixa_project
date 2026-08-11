import type { ReactNode } from "react";

import { PlatformLogoutButton } from "./platform-logout-button";
import styles from "./platform-shell.module.css";
import { Sidebar } from "./sidebar";

export function PlatformShell({
  fullName,
  permissions,
  children,
}: {
  fullName: string;
  permissions: string[];
  children: ReactNode;
}) {
  return (
    <div className={styles.shell}>
      <Sidebar permissions={permissions} />
      <div className={styles.main}>
        <header className={styles.topbar}>
          <div className={styles.userArea}>
            <span className={styles.userName}>{fullName}</span>
            <PlatformLogoutButton />
          </div>
        </header>
        <div className={styles.content}>{children}</div>
      </div>
    </div>
  );
}
