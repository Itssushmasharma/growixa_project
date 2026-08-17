export type DocCalloutType = "note" | "tip" | "warning" | "important";

export interface DocSection {
  id: string;
  title: string;
  content: string;
  subsections?: {
    id: string;
    title: string;
    content: string;
  }[];
}

export interface DocArticle {
  slug: string;
  category: string;
  title: string;
  excerpt: string;
  icon?: string;
  readingTimeMinutes: number;
  lastUpdated: string;
  tags: string[];
  sections: DocSection[];
  relatedSlugs?: string[];
}

export interface DocCategory {
  id: string;
  name: string;
  description: string;
  icon: string;
  color: string;
  articles: DocArticle[];
}

export interface DocSearchResult {
  article: DocArticle;
  category: DocCategory;
  matchScore: number;
  matchedField: "title" | "excerpt" | "tag" | "content";
  snippet: string;
}

export interface TableOfContentsItem {
  id: string;
  title: string;
  level: number;
}
