import React, { type ReactNode } from "react";
import Link from "next/link";
import styles from "./formatted-content.module.css";

/**
 * Parses inline markdown tokens:
 * - **bold** or __bold__
 * - `code`
 * - [text](url)
 * - *italic*
 */
export function formatInlineText(text: string): ReactNode[] {
  // Regex to match markdown links [text](url), bold **text**, code `text`, and italic *text*
  const tokenRegex = /(\[.*?\]\(.*?\)|\*\*.*?\*\*|`.*?`|\*.*?\*)/g;
  const parts = text.split(tokenRegex);

  return parts.map((part, index) => {
    if (!part) return null;

    // Link: [label](url)
    const linkMatch = part.match(/^\[(.*?)\]\((.*?)\)$/);
    if (linkMatch && linkMatch[1] && linkMatch[2]) {
      const isExternal = linkMatch[2].startsWith("http");
      if (isExternal) {
        return (
          <a
            key={index}
            href={linkMatch[2]}
            target="_blank"
            rel="noopener noreferrer"
            className={styles.docLink}
          >
            {linkMatch[1]}
          </a>
        );
      }
      return (
        <Link key={index} href={linkMatch[2]} className={styles.docLink}>
          {linkMatch[1]}
        </Link>
      );
    }

    // Bold: **text**
    if (part.startsWith("**") && part.endsWith("**") && part.length >= 4) {
      const inner = part.slice(2, -2);
      return (
        <strong key={index} className={styles.docBold}>
          {inner}
        </strong>
      );
    }

    // Inline Code: `text`
    if (part.startsWith("`") && part.endsWith("`") && part.length >= 2) {
      const inner = part.slice(1, -1);
      return (
        <code key={index} className={styles.docCode}>
          {inner}
        </code>
      );
    }

    // Italic: *text*
    if (part.startsWith("*") && part.endsWith("*") && part.length >= 2) {
      const inner = part.slice(1, -1);
      return <em key={index}>{inner}</em>;
    }

    // Plain text
    return <React.Fragment key={index}>{part}</React.Fragment>;
  });
}

interface FormattedContentProps {
  content: string;
}

export function FormattedContent({ content }: FormattedContentProps) {
  const paragraphs = content.split("\n\n");

  return (
    <div className={styles.formattedWrapper}>
      {paragraphs.map((block, pIdx) => {
        const trimmed = block.trim();
        if (!trimmed) return null;

        // Numbered list: 1. item, 2. item
        if (/^\d+\.\s+/.test(trimmed)) {
          const items = trimmed.split("\n");
          return (
            <ol key={pIdx} className={styles.orderedList}>
              {items.map((item, iIdx) => {
                const clean = item.replace(/^\d+\.\s+/, "");
                return <li key={iIdx}>{formatInlineText(clean)}</li>;
              })}
            </ol>
          );
        }

        // Bullet list: - item or * item
        if (/^[-*]\s+/.test(trimmed)) {
          const items = trimmed.split("\n");
          return (
            <ul key={pIdx} className={styles.unorderedList}>
              {items.map((item, iIdx) => {
                const clean = item.replace(/^[-*]\s+/, "");
                return <li key={iIdx}>{formatInlineText(clean)}</li>;
              })}
            </ul>
          );
        }

        // Standard paragraph
        return (
          <p key={pIdx} className={styles.paragraph}>
            {formatInlineText(trimmed)}
          </p>
        );
      })}
    </div>
  );
}
