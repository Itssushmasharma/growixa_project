import Image from "next/image";

import iconMark from "@/assets/icon/growixa-icon-mark.png";

import styles from "./sidebar.module.css";

// Sprint 1 wires up only the nav items that have a real page behind them (per
// DESIGN_REFERENCES.md's scope caveat) — Dashboard is the only one so far, so this is a
// static list rather than a route-driven nav until Company Settings / User Management land.
export function Sidebar() {
  return (
    <nav className={styles.sidebar}>
      <div className={styles.brand}>
        <Image src={iconMark} alt="" width={28} height={28} />
        <div>
          <div className={styles.brandName}>Growixa</div>
          <div className={styles.brandCaption}>BY IITDEVELOPER</div>
        </div>
      </div>

      <span className={styles.sectionLabel}>OVERVIEW</span>
      <span className={styles.navItemActive}>Dashboard</span>
    </nav>
  );
}
