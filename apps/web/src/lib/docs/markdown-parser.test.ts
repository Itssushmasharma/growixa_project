import { describe, expect, it } from "vitest";
import { parseDocMarkdown } from "./markdown-parser";

describe("Markdown Parser for Docs", () => {
  it("parses YAML frontmatter and markdown sections correctly", () => {
    const raw = `---
slug: "test-guide"
category: "getting-started"
title: "Testing Guide"
excerpt: "A guide for testing."
icon: "🧪"
readingTimeMinutes: 3
lastUpdated: "2026-08-17"
tags: ["test", "guide"]
relatedSlugs: ["welcome"]
---

## First Step
This is paragraph 1.

## Second Step
This is paragraph 2 with **bold** text.
`;

    const article = parseDocMarkdown(raw);
    expect(article.slug).toBe("test-guide");
    expect(article.category).toBe("getting-started");
    expect(article.title).toBe("Testing Guide");
    expect(article.icon).toBe("🧪");
    expect(article.readingTimeMinutes).toBe(3);
    expect(article.tags).toEqual(["test", "guide"]);
    expect(article.relatedSlugs).toEqual(["welcome"]);
    expect(article.sections.length).toBe(2);
    expect(article.sections[0]?.title).toBe("First Step");
    expect(article.sections[0]?.id).toBe("first-step");
    expect(article.sections[0]?.content).toBe("This is paragraph 1.");
    expect(article.sections[1]?.title).toBe("Second Step");
    expect(article.sections[1]?.id).toBe("second-step");
  });

  it("handles markdown without frontmatter gracefully", () => {
    const raw = `## Quick Overview\nJust some text.`;
    const article = parseDocMarkdown(raw);

    expect(article.slug).toBe("untitled");
    expect(article.sections.length).toBe(1);
    expect(article.sections[0]?.title).toBe("Quick Overview");
  });
});
