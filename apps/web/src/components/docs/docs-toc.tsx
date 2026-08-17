"use client";

import React, { useEffect, useState } from "react";
import type { DocSection } from "@/lib/docs/types";
import styles from "./docs-components.module.css";

interface DocsTocProps {
  sections: DocSection[];
}

export function DocsToc({ sections }: DocsTocProps) {
  const [activeId, setActiveId] = useState<string>(sections[0]?.id || "");

  useEffect(() => {
    const handleScroll = () => {
      const scrollPosition = window.scrollY + 100;
      for (const section of sections) {
        const element = document.getElementById(section.id);
        if (element) {
          const top = element.offsetTop;
          const height = element.offsetHeight;
          if (scrollPosition >= top && scrollPosition < top + height) {
            setActiveId(section.id);
            break;
          }
        }
      }
    };

    window.addEventListener("scroll", handleScroll, { passive: true });
    return () => window.removeEventListener("scroll", handleScroll);
  }, [sections]);

  if (!sections || sections.length === 0) return null;

  return (
    <nav className={styles.toc} aria-label="On this page navigation">
      <div className={styles.tocTitle}>On this page</div>
      <ul className={styles.tocList}>
        {sections.map((section) => (
          <li key={section.id} className={styles.tocItem}>
            <a
              href={`#${section.id}`}
              className={`${styles.tocLink} ${activeId === section.id ? styles.tocLinkActive : ""}`}
              onClick={(e) => {
                e.preventDefault();
                const el = document.getElementById(section.id);
                if (el) {
                  el.scrollIntoView({ behavior: "smooth" });
                  setActiveId(section.id);
                }
              }}
            >
              {section.title}
            </a>
          </li>
        ))}
      </ul>
    </nav>
  );
}
