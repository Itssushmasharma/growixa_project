import type { DocArticle, DocSection } from "./types";

/**
 * Parses markdown file content containing YAML-like frontmatter:
 * ---
 * key: value
 * ---
 * ## Heading
 * Body content...
 */
export function parseDocMarkdown(rawContent: string): DocArticle {
  const frontmatterRegex = /^---\r?\n([\s\S]*?)\r?\n---\r?\n([\s\S]*)$/;
  const match = rawContent.match(frontmatterRegex);

  const frontmatter: Record<string, string | number | string[]> = {};
  let body = rawContent;

  if (match && match[1] !== undefined && match[2] !== undefined) {
    const rawYaml = match[1];
    body = match[2];

    for (const line of rawYaml.split("\n")) {
      const colonIndex = line.indexOf(":");
      if (colonIndex > 0) {
        const key = line.slice(0, colonIndex).trim();
        let value = line.slice(colonIndex + 1).trim();

        // Strip quotes
        if (
          (value.startsWith('"') && value.endsWith('"')) ||
          (value.startsWith("'") && value.endsWith("'"))
        ) {
          value = value.slice(1, -1);
        }

        // Parse JSON array if array format: ["a", "b"]
        if (value.startsWith("[") && value.endsWith("]")) {
          try {
            frontmatter[key] = JSON.parse(value);
            continue;
          } catch {
            // fallback
          }
        }

        // Parse numbers
        if (/^\d+$/.test(value)) {
          frontmatter[key] = parseInt(value, 10);
          continue;
        }

        frontmatter[key] = value;
      }
    }
  }

  // Parse Sections by "## Heading"
  const sections: DocSection[] = [];
  const headingRegex = /^##\s+(.+)$/gm;
  const headings: { title: string; index: number }[] = [];

  let hMatch: RegExpExecArray | null;
  while ((hMatch = headingRegex.exec(body)) !== null) {
    if (hMatch[1]) {
      headings.push({ title: hMatch[1].trim(), index: hMatch.index });
    }
  }

  if (headings.length === 0) {
    sections.push({
      id: "overview",
      title: "Overview",
      content: body.trim(),
    });
  } else {
    for (let i = 0; i < headings.length; i++) {
      const heading = headings[i];
      if (!heading) continue;

      const nextHeading = headings[i + 1];
      const startContentIndex = heading.index + `## ${heading.title}`.length;
      const endContentIndex = nextHeading ? nextHeading.index : body.length;

      const sectionBody = body.slice(startContentIndex, endContentIndex).trim();
      const id = heading.title
        .toLowerCase()
        .replace(/[^a-z0-9]+/g, "-")
        .replace(/(^-|-$)/g, "");

      sections.push({
        id: id || `section-${i + 1}`,
        title: heading.title,
        content: sectionBody,
      });
    }
  }

  const slug = (frontmatter.slug as string) || "untitled";
  const category = (frontmatter.category as string) || "general";
  const title = (frontmatter.title as string) || slug;
  const excerpt = (frontmatter.excerpt as string) || "";
  const icon = (frontmatter.icon as string) || "📄";
  const readingTimeMinutes =
    (frontmatter.readingTimeMinutes as number) ||
    Math.max(1, Math.ceil(body.split(/\s+/).length / 200));
  const lastUpdated = (frontmatter.lastUpdated as string) || "2026-08-17";
  const tags = (frontmatter.tags as string[]) || [];
  const relatedSlugs = (frontmatter.relatedSlugs as string[]) || [];

  return {
    slug,
    category,
    title,
    excerpt,
    icon,
    readingTimeMinutes,
    lastUpdated,
    tags,
    sections,
    relatedSlugs,
  };
}
