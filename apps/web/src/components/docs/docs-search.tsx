"use client";

import React, { useState, useEffect, useRef } from "react";
import Link from "next/link";
import { searchDocs } from "@/lib/docs/search";
import type { DocSearchResult } from "@/lib/docs/types";
import styles from "./docs-components.module.css";

interface DocsSearchProps {
  placeholder?: string;
  autoFocus?: boolean;
  onSelectResult?: () => void;
  className?: string;
}

export function DocsSearch({
  placeholder = "Search guides, integrations, terms (e.g. 'Postmark', 'Restore', 'SPF')...",
  autoFocus = false,
  onSelectResult,
  className = "",
}: DocsSearchProps) {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<DocSearchResult[]>([]);
  const [isOpen, setIsOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!query.trim()) {
      setResults([]);
      setIsOpen(false);
      return;
    }

    const matches = searchDocs(query, 8);
    setResults(matches);
    setIsOpen(true);
  }, [query]);

  // Click outside to close dropdown
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  return (
    <div ref={containerRef} className={`${styles.searchWrapper} ${className}`}>
      <div className={styles.searchInputBox}>
        <span className={styles.searchIcon}>🔍</span>
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder={placeholder}
          className={styles.searchInput}
          autoFocus={autoFocus}
          aria-label="Search documentation"
        />
        {query && (
          <button
            type="button"
            className={styles.clearSearchBtn}
            onClick={() => setQuery("")}
            aria-label="Clear search"
          >
            ✕
          </button>
        )}
      </div>

      {isOpen && (
        <div className={styles.searchResultsDropdown} role="listbox">
          {results.length === 0 ? (
            <div className={styles.noResults}>
              No articles match &ldquo;<strong>{query}</strong>&rdquo;. Try searching for{" "}
              <em>campaigns</em>, <em>import</em>, or <em>SMTP</em>.
            </div>
          ) : (
            <div className={styles.resultsList}>
              <div className={styles.resultsCount}>
                Found {results.length} result{results.length === 1 ? "" : "s"}
              </div>
              {results.map(({ article, category, snippet }) => (
                <Link
                  key={`${category.id}-${article.slug}`}
                  href={`/docs/${category.id}/${article.slug}`}
                  className={styles.resultItem}
                  onClick={() => {
                    setIsOpen(false);
                    setQuery("");
                    onSelectResult?.();
                  }}
                >
                  <div className={styles.resultHeader}>
                    <span className={styles.resultCategory}>
                      {category.icon} {category.name}
                    </span>
                    <span className={styles.resultTime}>{article.readingTimeMinutes} min read</span>
                  </div>
                  <div className={styles.resultTitle}>
                    {article.icon} {article.title}
                  </div>
                  <div className={styles.resultSnippet}>{snippet}</div>
                </Link>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
