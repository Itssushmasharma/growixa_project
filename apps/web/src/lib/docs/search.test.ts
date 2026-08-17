import { describe, expect, it } from "vitest";
import { DOC_CATEGORIES, getAllArticles, getArticleBySlug, getCategoryById } from "./data";
import { searchDocs } from "./search";

describe("Docs Data & Search Engine", () => {
  it("loads all categories with articles and valid fields", () => {
    expect(DOC_CATEGORIES.length).toBeGreaterThanOrEqual(6);
    const allArticles = getAllArticles();
    expect(allArticles.length).toBeGreaterThanOrEqual(15);

    for (const article of allArticles) {
      expect(article.slug).toBeTruthy();
      expect(article.title).toBeTruthy();
      expect(article.excerpt).toBeTruthy();
      expect(article.sections.length).toBeGreaterThan(0);
      expect(article.tags.length).toBeGreaterThan(0);
    }
  });

  it("finds specific article by category and slug", () => {
    const res = getArticleBySlug("contacts", "contact-lifecycle");
    expect(res).toBeDefined();
    expect(res?.article.title).toContain("Lifecycle");
    expect(res?.category.name).toBe("Audience & Contacts");
  });

  it("returns undefined for non-existent slug", () => {
    expect(getArticleBySlug("contacts", "non-existent-article")).toBeUndefined();
    expect(getArticleBySlug("unknown-cat", "welcome")).toBeUndefined();
  });

  it("finds category by ID", () => {
    const cat = getCategoryById("ai-assistant");
    expect(cat).toBeDefined();
    expect(cat?.name).toBe("AI Marketing Copilot");
  });

  it("searches articles by keyword and returns relevant matches ranked by score", () => {
    const results = searchDocs("Postmark");
    expect(results.length).toBeGreaterThan(0);
    expect(results[0]?.article.slug).toBe("postmark-setup");
    expect(results[0]?.category.id).toBe("integrations");
  });

  it("matches contact archiving and quota lifecycle keywords", () => {
    const results = searchDocs("archiving contacts quota");
    expect(results.length).toBeGreaterThan(0);
    const match = results.find((r) => r.article.slug === "contact-lifecycle");
    expect(match).toBeDefined();
  });

  it("returns empty array for empty or whitespace-only queries", () => {
    expect(searchDocs("")).toEqual([]);
    expect(searchDocs("   ")).toEqual([]);
  });
});
