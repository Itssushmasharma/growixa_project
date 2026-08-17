"use client";

import React from "react";
import Link from "next/link";
import { DOC_CATEGORIES } from "@/lib/docs/data";
import styles from "./docs-components.module.css";

interface DocsSidebarProps {
  currentCategory?: string;
  currentSlug?: string;
  onLinkClick?: () => void;
}

export function DocsSidebar({ currentCategory, currentSlug, onLinkClick }: DocsSidebarProps) {
  return (
    <aside className={styles.sidebar} aria-label="Documentation Categories">
      <div className={styles.sidebarHeader}>
        <Link href="/docs" className={styles.sidebarHomeLink} onClick={onLinkClick}>
          📖 <span>Documentation Hub</span>
        </Link>
      </div>

      <nav className={styles.sidebarNav}>
        {DOC_CATEGORIES.map((category) => {
          const isCurrentCat = currentCategory === category.id;

          return (
            <div key={category.id} className={styles.categoryBlock}>
              <div className={styles.categoryTitle}>
                <span className={styles.categoryIcon}>{category.icon}</span>
                <span>{category.name}</span>
              </div>

              <ul className={styles.articleList}>
                {category.articles.map((article) => {
                  const isActive = isCurrentCat && currentSlug === article.slug;

                  return (
                    <li key={article.slug}>
                      <Link
                        href={`/docs/${category.id}/${article.slug}`}
                        className={`${styles.articleLink} ${isActive ? styles.articleLinkActive : ""}`}
                        onClick={onLinkClick}
                      >
                        {article.icon && <span className={styles.articleIcon}>{article.icon}</span>}
                        <span className={styles.articleLinkText}>{article.title}</span>
                      </Link>
                    </li>
                  );
                })}
              </ul>
            </div>
          );
        })}
      </nav>
    </aside>
  );
}
