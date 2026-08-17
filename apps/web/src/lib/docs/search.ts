import { DOC_CATEGORIES } from "./data";
import type { DocSearchResult } from "./types";

export function searchDocs(query: string, maxResults = 10): DocSearchResult[] {
  const trimmed = query.trim().toLowerCase();
  if (!trimmed) return [];

  const terms = trimmed.split(/\s+/).filter(Boolean);
  const results: DocSearchResult[] = [];

  for (const category of DOC_CATEGORIES) {
    for (const article of category.articles) {
      let score = 0;
      let matchedField: DocSearchResult["matchedField"] = "content";
      let snippet = article.excerpt;

      const titleLower = article.title.toLowerCase();
      const excerptLower = article.excerpt.toLowerCase();
      const tagsLower = article.tags.map((t) => t.toLowerCase());

      // Exact title match gets highest score
      if (titleLower.includes(trimmed)) {
        score += 100;
        matchedField = "title";
      }

      // Individual term matching in title
      for (const term of terms) {
        if (titleLower.includes(term)) {
          score += 30;
          matchedField = "title";
        }
      }

      // Tag matches
      for (const tag of tagsLower) {
        if (tag.includes(trimmed)) {
          score += 40;
          matchedField = "tag";
        }
        for (const term of terms) {
          if (tag.includes(term)) {
            score += 20;
            if (matchedField !== "title") matchedField = "tag";
          }
        }
      }

      // Excerpt match
      if (excerptLower.includes(trimmed)) {
        score += 25;
        if (matchedField === "content") matchedField = "excerpt";
      }

      // Content section matches
      for (const section of article.sections) {
        const secTitleLower = section.title.toLowerCase();
        const secContentLower = section.content.toLowerCase();

        if (secTitleLower.includes(trimmed)) {
          score += 35;
          snippet = section.content.slice(0, 140) + "...";
        }

        for (const term of terms) {
          if (secContentLower.includes(term)) {
            score += 10;
            if (score <= 35) {
              const idx = secContentLower.indexOf(term);
              const start = Math.max(0, idx - 40);
              const end = Math.min(section.content.length, idx + 100);
              snippet =
                (start > 0 ? "..." : "") +
                section.content.slice(start, end) +
                (end < section.content.length ? "..." : "");
            }
          }
        }
      }

      if (score > 0) {
        results.push({
          article,
          category,
          matchScore: score,
          matchedField,
          snippet,
        });
      }
    }
  }

  return results.sort((a, b) => b.matchScore - a.matchScore).slice(0, maxResults);
}
