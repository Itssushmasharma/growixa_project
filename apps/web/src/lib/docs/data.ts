import compiledDocs from "@/content/docs/generated-docs.json";
import type { DocCategory, DocArticle } from "./types";

export const DOC_CATEGORIES: DocCategory[] = compiledDocs as DocCategory[];

export function getAllArticles(): DocArticle[] {
  return DOC_CATEGORIES.flatMap((c) => c.articles);
}

export function getCategoryById(id: string): DocCategory | undefined {
  return DOC_CATEGORIES.find((c) => c.id === id);
}

export function getArticleBySlug(
  category: string,
  slug: string,
): { article: DocArticle; category: DocCategory } | undefined {
  const cat = getCategoryById(category);
  if (!cat) return undefined;
  const art = cat.articles.find((a) => a.slug === slug);
  if (!art) return undefined;
  return { article: art, category: cat };
}
