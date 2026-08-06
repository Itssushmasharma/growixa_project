const VOID_ELEMENTS = new Set([
  "area",
  "base",
  "br",
  "col",
  "embed",
  "hr",
  "img",
  "input",
  "link",
  "meta",
  "param",
  "source",
  "track",
  "wbr",
]);

export function formatHtml(html: string): string {
  const tokens = html
    .replace(/>\s*</g, "><")
    .match(/<!--[\s\S]*?-->|<!DOCTYPE[^>]*>|<\/?[^>]+>|[^<]+/gi);
  if (!tokens) return html;

  let indent = 0;
  const lines: string[] = [];

  for (const raw of tokens) {
    const token = raw.trim();
    if (!token) continue;

    if (token.startsWith("<!--") || token.startsWith("<!DOCTYPE")) {
      lines.push("  ".repeat(indent) + token);
      continue;
    }

    if (token.startsWith("</")) {
      indent = Math.max(indent - 1, 0);
      lines.push("  ".repeat(indent) + token);
      continue;
    }

    if (token.startsWith("<")) {
      lines.push("  ".repeat(indent) + token);
      const tagName = token.match(/^<([a-zA-Z0-9-]+)/)?.[1]?.toLowerCase();
      const selfClosing = token.endsWith("/>") || (!!tagName && VOID_ELEMENTS.has(tagName));
      if (!selfClosing) indent += 1;
      continue;
    }

    lines.push("  ".repeat(indent) + token);
  }

  return lines.join("\n");
}
