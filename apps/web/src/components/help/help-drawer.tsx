"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { DOC_CATEGORIES, getArticleBySlug } from "@/lib/docs/data";
import { searchDocs } from "@/lib/docs/search";
import type { DocArticle, DocCategory } from "@/lib/docs/types";
import styles from "./help-components.module.css";

interface HelpDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  initialCategory?: string;
  initialSlug?: string;
}

export function HelpDrawer({ isOpen, onClose, initialCategory, initialSlug }: HelpDrawerProps) {
  const [searchQuery, setSearchQuery] = useState("");
  const [activeArticle, setActiveArticle] = useState<{
    article: DocArticle;
    category: DocCategory;
  } | null>(null);

  useEffect(() => {
    if (initialCategory && initialSlug) {
      const match = getArticleBySlug(initialCategory, initialSlug);
      if (match) setActiveArticle(match);
    }
  }, [initialCategory, initialSlug]);

  useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      if (e.key === "Escape" && isOpen) {
        onClose();
      }
    }
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const searchResults = searchQuery.trim() ? searchDocs(searchQuery, 6) : [];

  return (
    <div className={styles.drawerBackdrop} onClick={onClose} data-testid="help-drawer-backdrop">
      <div
        className={styles.drawerContainer}
        onClick={(e) => e.stopPropagation()}
        role="dialog"
        aria-label="Growixa Help & Documentation"
      >
        {/* Drawer Header */}
        <div className={styles.drawerHeader}>
          <div className={styles.drawerTitleRow}>
            <div className={styles.drawerTitle}>
              <span className={styles.drawerIcon}>📖</span>
              <span>Help & Documentation</span>
            </div>
            <div className={styles.drawerActions}>
              <Link
                href="/docs"
                target="_blank"
                rel="noopener noreferrer"
                className={styles.expandDocsBtn}
                title="Open full documentation portal in new tab"
              >
                ↗ Full Docs
              </Link>
              <button
                type="button"
                className={styles.closeDrawerBtn}
                onClick={onClose}
                aria-label="Close help drawer"
              >
                ✕
              </button>
            </div>
          </div>

          {/* Search Input */}
          <div className={styles.drawerSearchBox}>
            <span className={styles.searchIcon}>🔍</span>
            <input
              type="text"
              placeholder="Search help articles, SPF, Postmark, Segments..."
              value={searchQuery}
              onChange={(e) => {
                setSearchQuery(e.target.value);
                if (activeArticle) setActiveArticle(null);
              }}
              className={styles.drawerSearchInput}
              autoFocus
            />
            {searchQuery && (
              <button type="button" className={styles.clearBtn} onClick={() => setSearchQuery("")}>
                ✕
              </button>
            )}
          </div>
        </div>

        {/* Drawer Body */}
        <div className={styles.drawerBody}>
          {activeArticle ? (
            /* Active Article View */
            <div className={styles.articleReader}>
              <button
                type="button"
                className={styles.backBtn}
                onClick={() => setActiveArticle(null)}
              >
                ← Back to all guides
              </button>

              <div className={styles.articleHeader}>
                <div className={styles.articleCategoryBadge}>
                  {activeArticle.category.icon} {activeArticle.category.name}
                </div>
                <h2 className={styles.articleTitle}>
                  {activeArticle.article.icon} {activeArticle.article.title}
                </h2>
                <div className={styles.articleMeta}>
                  <span>⏱️ {activeArticle.article.readingTimeMinutes} min read</span>
                  <span>•</span>
                  <span>Updated {activeArticle.article.lastUpdated}</span>
                </div>
              </div>

              <p className={styles.articleExcerpt}>{activeArticle.article.excerpt}</p>

              <div className={styles.articleSections}>
                {activeArticle.article.sections.map((section) => (
                  <div key={section.id} className={styles.sectionBlock}>
                    <h3 className={styles.sectionTitle}>{section.title}</h3>
                    <div className={styles.sectionContent}>
                      {section.content.split("\n\n").map((para, idx) => (
                        <p key={idx}>{para}</p>
                      ))}
                    </div>
                  </div>
                ))}
              </div>

              <div className={styles.articleFooter}>
                <Link
                  href={`/docs/${activeArticle.category.id}/${activeArticle.article.slug}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className={styles.fullPageLink}
                >
                  Open in full docs view ↗
                </Link>
              </div>
            </div>
          ) : searchQuery.trim() ? (
            /* Search Results View */
            <div className={styles.searchResults}>
              {searchResults.length === 0 ? (
                <div className={styles.emptyState}>
                  No articles found for &ldquo;{searchQuery}&rdquo;.
                </div>
              ) : (
                searchResults.map(({ article, category, snippet }) => (
                  <div
                    key={`${category.id}-${article.slug}`}
                    className={styles.searchResultCard}
                    onClick={() => setActiveArticle({ article, category })}
                  >
                    <div className={styles.resultMeta}>
                      <span>{category.name}</span>
                      <span>{article.readingTimeMinutes} min read</span>
                    </div>
                    <div className={styles.cardTitle}>
                      {article.icon} {article.title}
                    </div>
                    <div className={styles.cardSnippet}>{snippet}</div>
                  </div>
                ))
              )}
            </div>
          ) : (
            /* Default Category Browser */
            <div className={styles.categoryBrowser}>
              <div className={styles.browserHeader}>Popular Guide Categories</div>
              <div className={styles.categoryGrid}>
                {DOC_CATEGORIES.map((category) => (
                  <div key={category.id} className={styles.categoryCard}>
                    <div className={styles.catHeader}>
                      <span className={styles.catIcon}>{category.icon}</span>
                      <span className={styles.catName}>{category.name}</span>
                    </div>
                    <ul className={styles.catArticleList}>
                      {category.articles.map((article) => (
                        <li key={article.slug}>
                          <button
                            type="button"
                            className={styles.articleNavBtn}
                            onClick={() => setActiveArticle({ article, category })}
                          >
                            <span>{article.title}</span>
                          </button>
                        </li>
                      ))}
                    </ul>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
