"use client";

import styles from "./floating-3d.module.css";

export function Floating3DObjects() {
  return (
    <div className={styles.floatingContainer} aria-hidden="true">
      {/* 3D Floating Cube Left */}
      <div className={`${styles.object} ${styles.cubeLeft}`}>
        <div className={styles.cube}>
          <div className={`${styles.face} ${styles.front}`} />
          <div className={`${styles.face} ${styles.back}`} />
          <div className={`${styles.face} ${styles.right}`} />
          <div className={`${styles.face} ${styles.left}`} />
          <div className={`${styles.face} ${styles.top}`} />
          <div className={`${styles.face} ${styles.bottom}`} />
        </div>
      </div>

      {/* 3D Floating Prism Right */}
      <div className={`${styles.object} ${styles.prismRight}`}>
        <div className={styles.pyramid}>
          <div className={`${styles.pface} ${styles.p1}`} />
          <div className={`${styles.pface} ${styles.p2}`} />
          <div className={`${styles.pface} ${styles.p3}`} />
          <div className={`${styles.pface} ${styles.p4}`} />
        </div>
      </div>

      {/* Glowing 3D Orb */}
      <div className={styles.glowingOrb} />
    </div>
  );
}
