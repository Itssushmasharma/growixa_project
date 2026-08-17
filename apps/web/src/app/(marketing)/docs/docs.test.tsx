import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";

import { DocsCallout } from "@/components/docs/docs-callout";
import { DocsSearch } from "@/components/docs/docs-search";
import { DocsSidebar } from "@/components/docs/docs-sidebar";
import { DocsToc } from "@/components/docs/docs-toc";
import { HelpDrawer } from "@/components/help/help-drawer";
import { HelpTooltip } from "@/components/help/help-tooltip";
import { DOC_CATEGORIES, getArticleBySlug } from "@/lib/docs/data";
import DocArticlePage from "./[category]/[slug]/page";
import DocsLandingPage from "./page";

describe("Documentation & Help Center", () => {
  it("renders DocsLandingPage with hero, categories, and quick links", () => {
    render(<DocsLandingPage />);

    expect(screen.getByRole("heading", { name: "How can we help you grow?" })).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/Search guides, SMTP/)).toBeInTheDocument();
    expect(screen.getByText("⚡ 5-Min Quickstart")).toBeInTheDocument();

    // Check all categories are present
    for (const cat of DOC_CATEGORIES) {
      expect(screen.getByText(cat.name)).toBeInTheDocument();
    }
  });

  it("renders DocArticlePage with sections, callout, breadcrumbs, and TOC", async () => {
    const page = await DocArticlePage({
      params: Promise.resolve({
        category: "contacts",
        slug: "restoring-deleted-contacts",
      }),
    });

    render(page);

    expect(
      screen.getByRole("heading", { name: /Contact Soft Deletes & Audience Restoration/ }),
    ).toBeInTheDocument();
    expect(screen.getByText("Quota Limit Protection")).toBeInTheDocument();
    expect(screen.getAllByText("Restoring Deleted Contacts").length).toBeGreaterThanOrEqual(2);
    expect(screen.getByLabelText("Breadcrumbs")).toBeInTheDocument();
    expect(screen.getByLabelText("On this page navigation")).toBeInTheDocument();
  });

  it("renders DocsSidebar with category accordion and active article", () => {
    render(<DocsSidebar currentCategory="getting-started" currentSlug="quickstart" />);

    expect(screen.getByText("Documentation Hub")).toBeInTheDocument();
    expect(
      screen.getByText("Quickstart: Launch Your First Campaign in 5 Minutes"),
    ).toBeInTheDocument();
    expect(screen.getByText("Audience & Contacts")).toBeInTheDocument();
  });

  it("handles live search filtering in DocsSearch", async () => {
    const user = userEvent.setup();
    render(<DocsSearch />);

    const searchInput = screen.getByPlaceholderText(/Search guides/);
    await user.type(searchInput, "Postmark");

    expect(await screen.findByText(/Found \d+ result/)).toBeInTheDocument();
    expect(screen.getByText(/Connecting Postmark for Email Delivery/)).toBeInTheDocument();

    // Clear search
    const clearBtn = screen.getByLabelText("Clear search");
    await user.click(clearBtn);

    expect(searchInput).toHaveValue("");
  });

  it("renders DocsCallout variants correctly", () => {
    const { rerender } = render(
      <DocsCallout type="tip" title="Custom Tip Title">
        Helpful advice here.
      </DocsCallout>,
    );

    expect(screen.getByText("Custom Tip Title")).toBeInTheDocument();
    expect(screen.getByText("Helpful advice here.")).toBeInTheDocument();

    rerender(<DocsCallout type="warning">Careful with deletions!</DocsCallout>);

    expect(screen.getByText("Warning")).toBeInTheDocument();
    expect(screen.getByText("Careful with deletions!")).toBeInTheDocument();
  });

  it("renders HelpTooltip and shows popover on hover/focus", async () => {
    const user = userEvent.setup();
    render(
      <HelpTooltip
        text="Suppression protects your sender reputation."
        docPath="/docs/contacts/suppression-and-consent"
        docTitle="Suppression Guide"
      />,
    );

    const tooltip = screen.getByRole("tooltip");
    await user.hover(tooltip);

    expect(
      await screen.findByText("Suppression protects your sender reputation."),
    ).toBeInTheDocument();
    expect(screen.getByText("📖 Suppression Guide →")).toBeInTheDocument();
  });

  it("renders HelpDrawer, supports searching and article reading inside drawer", async () => {
    const user = userEvent.setup();
    let closed = false;

    const { rerender } = render(
      <HelpDrawer
        isOpen={true}
        onClose={() => {
          closed = true;
        }}
      />,
    );

    expect(
      screen.getByRole("dialog", { name: "Growixa Help & Documentation" }),
    ).toBeInTheDocument();
    expect(screen.getByText("Popular Guide Categories")).toBeInTheDocument();

    // Search inside drawer
    const searchInput = screen.getByPlaceholderText(/Search help articles/);
    await user.type(searchInput, "SPF");

    expect(await screen.findByText(/Domain Verification, SPF & DKIM Setup/)).toBeInTheDocument();

    // Click result to open article reader
    await user.click(screen.getByText(/Domain Verification, SPF & DKIM Setup/));

    expect(await screen.findByText("Why DNS Authentication is Critical")).toBeInTheDocument();
    expect(screen.getByText("← Back to all guides")).toBeInTheDocument();

    // Click close button
    await user.click(screen.getByLabelText("Close help drawer"));
    expect(closed).toBe(true);

    // Rerender as closed
    rerender(<HelpDrawer isOpen={false} onClose={() => {}} />);
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
  });
});
