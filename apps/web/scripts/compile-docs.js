/* eslint-disable @typescript-eslint/no-require-imports */
const fs = require("fs");
const path = require("path");

function parseDocMarkdown(rawContent) {
  const frontmatterRegex = /^---\r?\n([\s\S]*?)\r?\n---\r?\n([\s\S]*)$/;
  const match = rawContent.match(frontmatterRegex);

  let frontmatter = {};
  let body = rawContent;

  if (match && match[1] !== undefined && match[2] !== undefined) {
    const rawYaml = match[1];
    body = match[2];

    for (const line of rawYaml.split("\n")) {
      const colonIndex = line.indexOf(":");
      if (colonIndex > 0) {
        const key = line.slice(0, colonIndex).trim();
        let value = line.slice(colonIndex + 1).trim();

        if (
          (value.startsWith('"') && value.endsWith('"')) ||
          (value.startsWith("'") && value.endsWith("'"))
        ) {
          value = value.slice(1, -1);
        }

        if (value.startsWith("[") && value.endsWith("]")) {
          try {
            frontmatter[key] = JSON.parse(value);
            continue;
          } catch {
            // fallback
          }
        }

        if (/^\d+$/.test(value)) {
          frontmatter[key] = parseInt(value, 10);
          continue;
        }

        frontmatter[key] = value;
      }
    }
  }

  const sections = [];
  const headingRegex = /^##\s+(.+)$/gm;
  const headings = [];

  let hMatch;
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

  const slug = frontmatter.slug || "untitled";
  const category = frontmatter.category || "general";
  const title = frontmatter.title || slug;
  const excerpt = frontmatter.excerpt || "";
  const icon = frontmatter.icon || "📄";
  const readingTimeMinutes =
    frontmatter.readingTimeMinutes || Math.max(1, Math.ceil(body.split(/\s+/).length / 200));
  const lastUpdated = frontmatter.lastUpdated || "2026-08-17";
  const tags = frontmatter.tags || [];
  const relatedSlugs = frontmatter.relatedSlugs || [];

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

function compileDocs() {
  const contentDir = path.join(__dirname, "../src/content/docs");
  const categoriesFile = path.join(contentDir, "categories.json");
  const outputFile = path.join(contentDir, "generated-docs.json");

  if (!fs.existsSync(categoriesFile)) {
    console.error("categories.json not found in", contentDir);
    return;
  }

  const categories = JSON.parse(fs.readFileSync(categoriesFile, "utf-8"));
  const compiledCategories = [];

  for (const cat of categories) {
    const catDir = path.join(contentDir, cat.id);
    const articles = [];

    if (fs.existsSync(catDir)) {
      const files = fs.readdirSync(catDir).filter((f) => f.endsWith(".md"));
      for (const file of files) {
        const filePath = path.join(catDir, file);
        const rawContent = fs.readFileSync(filePath, "utf-8");
        const article = parseDocMarkdown(rawContent);
        articles.push(article);
      }
    }

    compiledCategories.push({
      ...cat,
      articles,
    });
  }

  fs.writeFileSync(outputFile, JSON.stringify(compiledCategories, null, 2), "utf-8");
  console.log(
    `[Growixa Docs] Successfully compiled ${compiledCategories.reduce((acc, c) => acc + c.articles.length, 0)} markdown articles from src/content/docs into generated-docs.json`,
  );
}

compileDocs();
