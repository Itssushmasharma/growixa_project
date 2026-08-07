import Image from "next/image";
import type { ReactNode } from "react";

import iconMark from "@/assets/icon/growixa-icon-mark.png";

import { PlatformLogoutButton } from "./platform-logout-button";
import styles from "./platform-shell.module.css";

export function PlatformShell({ fullName, children }: { fullName: string; children: ReactNode }) {
  return (
    <div className={styles.shell}>
      <header className={styles.topbar}>
        <div className={styles.brand}>
          <Image src={iconMark} alt="" width={28} height={28} />
          <div>
            <div className={styles.brandName}>Growixa</div>
            <div className={styles.brandCaption}>PLATFORM ADMIN</div>
          </div>
        </div>
        <div className={styles.userArea}>
          <span className={styles.userName}>{fullName}</span>
          <PlatformLogoutButton />
        </div>
      </header>
      <div className={styles.content}>{children}</div>
    </div>
  );
}
