import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ToastProvider } from "@/components/toast/toast-context";
import { apiFetch } from "@/lib/api-client";

import { ContactsPage } from "./contacts-page";
import type { ConsentRecord, Contact, ContactStats, MeResponse, Tag } from "./types";

vi.mock("@/lib/api-client", async () => {
  const actual = await vi.importActual<typeof import("@/lib/api-client")>("@/lib/api-client");
  return { ...actual, apiFetch: vi.fn() };
});

const mockedApiFetch = vi.mocked(apiFetch);

function renderContactsPage() {
  return render(
    <ToastProvider>
      <ContactsPage />
    </ToastProvider>,
  );
}

function meWithPermissions(permissions: string[]): MeResponse {
  return { id: "user-1", email: "admin@example.com", full_name: "Admin User", permissions };
}

function isConsentGet(path: string, init?: RequestInit): boolean {
  return /^\/contacts\/[^/]+\/consent$/.test(path) && (!init || init.method === undefined);
}

// GRX-PERF-001 follow-up: `/contacts` is now server-paginated, and the Contacts page gets
// its stat badges/tab counts and "total pages" figure from the dedicated `/contacts/stats`
// and `/contacts/count` endpoints instead of `.length` on a fully-fetched array. This fake
// backend mirrors that shape: `store.active`/`store.deleted` hold the current fixture data,
// and `/contacts`, `/contacts/stats`, `/contacts/count` are all derived live from the store
// so a test's own mutation handler (`extra`) can update the store and have every
// subsequent fetch (triggered by the component's own refetch-after-mutation) reflect it --
// exactly like a real backend, without re-deriving numbers from a stale full-array fetch.
interface ContactsMockStore {
  active: Contact[];
  deleted: Contact[];
}

function createStore(initial: Partial<ContactsMockStore> = {}): ContactsMockStore {
  return { active: initial.active ?? [], deleted: initial.deleted ?? [] };
}

function computeStats(active: Contact[]): ContactStats {
  const now = new Date();
  return {
    total: active.length,
    active: active.filter((c) => c.status === "ACTIVE").length,
    archived: active.filter((c) => c.status === "ARCHIVED").length,
    suppressed: active.filter((c) => c.is_suppressed).length,
    new_this_month: active.filter((c) => {
      if (!c.created_at) return false;
      const created = new Date(c.created_at);
      return created.getFullYear() === now.getFullYear() && created.getMonth() === now.getMonth();
    }).length,
  };
}

function baseContactsMock(
  store: ContactsMockStore,
  opts: {
    permissions: string[];
    tags?: Tag[];
    lists?: unknown[];
    customFields?: unknown[];
    extra?: (path: string, init?: RequestInit) => unknown;
  },
) {
  return (path: string, init?: RequestInit): Promise<unknown> => {
    if (opts.extra) {
      const result = opts.extra(path, init);
      if (result !== undefined) return Promise.resolve(result);
    }
    if (path === "/auth/me") return Promise.resolve(meWithPermissions(opts.permissions));
    if (path === "/contacts/tags" && (!init || init.method === undefined)) {
      return Promise.resolve(opts.tags ?? []);
    }
    if (path === "/contacts/lists" && (!init || init.method === undefined)) {
      return Promise.resolve(opts.lists ?? []);
    }
    if (path === "/contacts/custom-fields" && (!init || init.method === undefined)) {
      return Promise.resolve(opts.customFields ?? []);
    }
    if (path === "/contacts/stats") {
      return Promise.resolve(computeStats(store.active));
    }
    if (path.startsWith("/contacts/count")) {
      return Promise.resolve({
        total: path.includes("deleted_only=true") ? store.deleted.length : store.active.length,
      });
    }
    if (path.startsWith("/contacts?") && (!init || init.method === undefined)) {
      return Promise.resolve(path.includes("deleted_only=true") ? store.deleted : store.active);
    }
    throw new Error(`unexpected call: ${path}`);
  };
}

const ACTIVE_CONTACT: Contact = {
  id: "contact-1",
  email: "alice@example.com",
  first_name: "Alice",
  last_name: "Anderson",
  phone: null,
  status: "ACTIVE",
  source: null,
  created_at: "2026-07-01T00:00:00Z",
  updated_at: "2026-07-01T00:00:00Z",
  custom_fields: {},
  tags: [],
  is_suppressed: false,
};

const SUPPRESSED_CONTACT: Contact = {
  id: "contact-2",
  email: "bob@example.com",
  first_name: "Bob",
  last_name: null,
  phone: null,
  status: "ACTIVE",
  source: null,
  created_at: "2026-07-01T00:00:00Z",
  updated_at: "2026-07-01T00:00:00Z",
  custom_fields: {},
  tags: [],
  is_suppressed: true,
};

const VIP_TAG: Tag = {
  id: "tag-1",
  name: "VIP",
};

const GRANTED_CONSENT: ConsentRecord = {
  id: "consent-1",
  channel: "EMAIL",
  status: "GRANTED",
  source: "signup_form",
  recorded_at: "2026-07-01T00:00:00Z",
};

const DELETED_CONTACT: Contact = {
  id: "contact-3",
  email: "charlie@example.com",
  first_name: "Charlie",
  last_name: "Chaplin",
  phone: null,
  status: "ACTIVE",
  source: null,
  created_at: "2026-07-01T00:00:00Z",
  updated_at: "2026-07-01T00:00:00Z",
  deleted_at: "2026-08-01T00:00:00Z",
  custom_fields: {},
  tags: [],
  is_suppressed: false,
};

beforeEach(() => {
  mockedApiFetch.mockReset();
});

describe("ContactsPage", () => {
  it("renders the contact list with status and suppressed badges", async () => {
    const store = createStore({ active: [ACTIVE_CONTACT, SUPPRESSED_CONTACT] });
    mockedApiFetch.mockImplementation(
      baseContactsMock(store, { permissions: ["contacts.view", "contacts.manage"] }),
    );

    renderContactsPage();

    expect(await screen.findByText("Alice Anderson")).toBeInTheDocument();
    expect(screen.getByText("Bob")).toBeInTheDocument();
    const aliceBlock = screen
      .getByText("Alice Anderson")
      .closest("div[class*='contactBlock']") as HTMLElement;
    const bobBlock = screen.getByText("Bob").closest("div[class*='contactBlock']") as HTMLElement;
    expect(within(aliceBlock).getByText("Active")).toBeInTheDocument();
    expect(within(bobBlock).getByText("Active")).toBeInTheDocument();
    expect(within(bobBlock).getByText("Suppressed")).toBeInTheDocument();
  });

  it("shows account-wide stat badges independent of the current page", async () => {
    // Regression test for the GRX-PERF-001 review finding: badges must come from
    // `/contacts/stats`, not `.length` on whatever page happened to be fetched.
    const manyActive = Array.from({ length: 60 }, (_, i) => ({
      ...ACTIVE_CONTACT,
      id: `contact-${i}`,
      email: `contact-${i}@example.com`,
      status: i < 5 ? ("ARCHIVED" as const) : ("ACTIVE" as const),
    }));
    const store = createStore({ active: manyActive });
    mockedApiFetch.mockImplementation(
      baseContactsMock(store, { permissions: ["contacts.view", "contacts.manage"] }),
    );

    renderContactsPage();

    await screen.findByText("Total Contacts");
    const totalCard = screen
      .getByText("Total Contacts")
      .closest("div[class*='statCard']") as HTMLElement;
    const activeCard = screen
      .getAllByText("Active Contacts")
      .map((el) => el.closest("div[class*='statCard']"))
      .find((el): el is HTMLElement => el !== null) as HTMLElement;
    const archivedCard = screen
      .getAllByText("Archived")
      .map((el) => el.closest("div[class*='statCard']"))
      .find((el): el is HTMLElement => el !== null) as HTMLElement;
    expect(within(totalCard).getByText("60")).toBeInTheDocument();
    expect(within(activeCard).getByText("55")).toBeInTheDocument();
    expect(within(archivedCard).getByText("5")).toBeInTheDocument();
  });

  it("shows an access-denied message for a user without contacts.view", async () => {
    const store = createStore();
    mockedApiFetch.mockImplementation(baseContactsMock(store, { permissions: [] }));

    renderContactsPage();

    expect(await screen.findByText("You don't have access to view contacts.")).toBeInTheDocument();
  });

  it("hides write controls for a view-only user", async () => {
    const store = createStore({ active: [ACTIVE_CONTACT] });
    mockedApiFetch.mockImplementation(
      baseContactsMock(store, {
        permissions: ["contacts.view"],
        extra: (path, init) => (isConsentGet(path, init) ? [] : undefined),
      }),
    );

    const user = userEvent.setup();
    renderContactsPage();

    expect(await screen.findByText("Alice Anderson")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "+ Add contact" })).not.toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "View" }));
    expect(screen.getByText("You have view-only access to contacts.")).toBeInTheDocument();
    expect(screen.queryByLabelText("Attach an existing tag")).not.toBeInTheDocument();
    expect(screen.queryByLabelText("Consent channel")).not.toBeInTheDocument();
  });

  it("creates a contact via the add form", async () => {
    const store = createStore({ active: [] });
    const created: Contact = { ...ACTIVE_CONTACT, id: "contact-new", email: "new@example.com" };
    mockedApiFetch.mockImplementation(
      baseContactsMock(store, {
        permissions: ["contacts.view", "contacts.manage"],
        extra: (path, init) => {
          if (path === "/contacts" && init?.method === "POST") {
            store.active = [created, ...store.active];
            return created;
          }
          return undefined;
        },
      }),
    );

    const user = userEvent.setup();
    renderContactsPage();

    await screen.findByText("No contacts yet.");
    await user.click(screen.getByRole("button", { name: "+ Add contact" }));
    await user.type(screen.getByLabelText("Email"), "new@example.com");
    await user.click(screen.getByRole("button", { name: "Create contact" }));

    await waitFor(() => expect(screen.getByText("new@example.com")).toBeInTheDocument());
  });

  it("edits a contact via the inline detail panel", async () => {
    const store = createStore({ active: [ACTIVE_CONTACT] });
    mockedApiFetch.mockImplementation(
      baseContactsMock(store, {
        permissions: ["contacts.view", "contacts.manage"],
        extra: (path, init) => {
          if (isConsentGet(path, init)) return [];
          if (path === "/contacts/contact-1" && init?.method === "PATCH") {
            const updated = { ...ACTIVE_CONTACT, first_name: "Alicia" };
            store.active = store.active.map((c) => (c.id === "contact-1" ? updated : c));
            return updated;
          }
          return undefined;
        },
      }),
    );

    const user = userEvent.setup();
    renderContactsPage();

    await screen.findByText("Alice Anderson");
    await user.click(screen.getByRole("button", { name: "View" }));

    const firstNameInput = screen.getByLabelText("First name");
    await user.clear(firstNameInput);
    await user.type(firstNameInput, "Alicia");
    await user.click(screen.getByRole("button", { name: "Save changes" }));

    await waitFor(() => {
      const [, patchCall] =
        mockedApiFetch.mock.calls.find(
          ([path, init]) => path === "/contacts/contact-1" && init?.method === "PATCH",
        ) ?? [];
      expect(patchCall).toBeDefined();
    });
  });

  it("archives a contact via the toggle button", async () => {
    const store = createStore({ active: [ACTIVE_CONTACT] });
    mockedApiFetch.mockImplementation(
      baseContactsMock(store, {
        permissions: ["contacts.view", "contacts.manage"],
        extra: (path, init) => {
          if (isConsentGet(path, init)) return [];
          if (path === "/contacts/contact-1/status" && init?.method === "PATCH") {
            const updated = { ...ACTIVE_CONTACT, status: "ARCHIVED" as const };
            store.active = store.active.map((c) => (c.id === "contact-1" ? updated : c));
            return updated;
          }
          return undefined;
        },
      }),
    );

    const user = userEvent.setup();
    renderContactsPage();

    await screen.findByText("Alice Anderson");
    await user.click(screen.getByRole("button", { name: "View" }));
    await user.click(screen.getByRole("button", { name: "Archive" }));
    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Unarchive" })).toBeInTheDocument();
    });
  });

  it("attaches an existing tag to a contact", async () => {
    const store = createStore({ active: [ACTIVE_CONTACT] });
    mockedApiFetch.mockImplementation(
      baseContactsMock(store, {
        permissions: ["contacts.view", "contacts.manage"],
        tags: [VIP_TAG],
        extra: (path, init) => {
          if (isConsentGet(path, init)) return [];
          if (path === "/contacts/contact-1/tags" && init?.method === "POST") {
            const updated = { ...ACTIVE_CONTACT, tags: ["VIP"] };
            store.active = store.active.map((c) => (c.id === "contact-1" ? updated : c));
            return updated;
          }
          return undefined;
        },
      }),
    );

    const user = userEvent.setup();
    renderContactsPage();

    await screen.findByText("Alice Anderson");
    await user.click(screen.getByRole("button", { name: "View" }));
    await user.selectOptions(screen.getByLabelText("Attach an existing tag"), "tag-1");
    await user.click(screen.getByRole("button", { name: "Attach" }));

    await waitFor(() => expect(screen.getByText("VIP")).toBeInTheDocument());
  });

  it("removes a tag from a contact", async () => {
    const tagged: Contact = { ...ACTIVE_CONTACT, tags: ["VIP"] };
    const store = createStore({ active: [tagged] });
    mockedApiFetch.mockImplementation(
      baseContactsMock(store, {
        permissions: ["contacts.view", "contacts.manage"],
        tags: [VIP_TAG],
        extra: (path, init) => {
          if (isConsentGet(path, init)) return [];
          if (path === "/contacts/contact-1/tags/tag-1" && init?.method === "DELETE") {
            const updated = { ...ACTIVE_CONTACT, tags: [] };
            store.active = store.active.map((c) => (c.id === "contact-1" ? updated : c));
            return updated;
          }
          return undefined;
        },
      }),
    );

    const user = userEvent.setup();
    renderContactsPage();

    await screen.findByText("Alice Anderson");
    await user.click(screen.getByRole("button", { name: "View" }));
    expect(screen.getByText("VIP")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Remove tag VIP" }));

    await waitFor(() =>
      expect(screen.queryByRole("button", { name: "Remove tag VIP" })).not.toBeInTheDocument(),
    );
  });

  it("creates a new tag and attaches it to a contact", async () => {
    const createdTag: Tag = { id: "tag-2", name: "Newsletter" };
    const store = createStore({ active: [ACTIVE_CONTACT] });
    mockedApiFetch.mockImplementation(
      baseContactsMock(store, {
        permissions: ["contacts.view", "contacts.manage"],
        extra: (path, init) => {
          if (isConsentGet(path, init)) return [];
          if (path === "/contacts/tags" && init?.method === "POST") return createdTag;
          if (path === "/contacts/contact-1/tags" && init?.method === "POST") {
            const updated = { ...ACTIVE_CONTACT, tags: ["Newsletter"] };
            store.active = store.active.map((c) => (c.id === "contact-1" ? updated : c));
            return updated;
          }
          return undefined;
        },
      }),
    );

    const user = userEvent.setup();
    renderContactsPage();

    await screen.findByText("Alice Anderson");
    await user.click(screen.getByRole("button", { name: "View" }));
    await user.type(screen.getByLabelText("New tag name"), "Newsletter");
    await user.click(screen.getByRole("button", { name: "+ New tag" }));

    await waitFor(() => expect(screen.getByText("Newsletter")).toBeInTheDocument());
  });

  it("loads and displays a contact's consent history", async () => {
    const store = createStore({ active: [ACTIVE_CONTACT] });
    mockedApiFetch.mockImplementation(
      baseContactsMock(store, {
        permissions: ["contacts.view", "contacts.manage"],
        extra: (path, init) => (isConsentGet(path, init) ? [GRANTED_CONSENT] : undefined),
      }),
    );

    const user = userEvent.setup();
    renderContactsPage();

    await screen.findByText("Alice Anderson");
    await user.click(screen.getByRole("button", { name: "View" }));

    await waitFor(() =>
      expect(screen.getByText(/EMAIL: GRANTED \(signup_form\)/)).toBeInTheDocument(),
    );
  });

  it("records new consent via the inline form", async () => {
    const newRecord: ConsentRecord = {
      id: "consent-2",
      channel: "SMS",
      status: "WITHDRAWN",
      source: null,
      recorded_at: "2026-07-02T00:00:00Z",
    };
    const store = createStore({ active: [ACTIVE_CONTACT] });
    mockedApiFetch.mockImplementation(
      baseContactsMock(store, {
        permissions: ["contacts.view", "contacts.manage"],
        extra: (path, init) => {
          if (isConsentGet(path, init)) return [];
          if (path === "/contacts/contact-1/consent" && init?.method === "POST") return newRecord;
          return undefined;
        },
      }),
    );

    const user = userEvent.setup();
    renderContactsPage();

    await screen.findByText("Alice Anderson");
    await user.click(screen.getByRole("button", { name: "View" }));
    await screen.findByText("No consent recorded yet.");

    await user.selectOptions(screen.getByLabelText("Consent channel"), "SMS");
    await user.selectOptions(screen.getByLabelText("Consent status"), "WITHDRAWN");
    await user.click(screen.getByRole("button", { name: "Record consent" }));

    await waitFor(() => expect(screen.getByText(/SMS: WITHDRAWN/)).toBeInTheDocument());
  });

  it("selects contacts, toggles select all, and displays bulk action bar", async () => {
    const store = createStore({ active: [ACTIVE_CONTACT, SUPPRESSED_CONTACT] });
    mockedApiFetch.mockImplementation(
      baseContactsMock(store, { permissions: ["contacts.view", "contacts.manage"] }),
    );

    const user = userEvent.setup();
    renderContactsPage();

    await screen.findByText("Alice Anderson");

    // Initially bulk action bar is not visible
    expect(screen.queryByTestId("bulk-action-bar")).not.toBeInTheDocument();

    // Select Alice
    const aliceCheckbox = screen.getByLabelText("Select Alice Anderson");
    await user.click(aliceCheckbox);

    // Bulk action bar appears
    expect(screen.getByTestId("bulk-action-bar")).toBeInTheDocument();
    expect(screen.getByText("1 selected")).toBeInTheDocument();

    // Click select all on page
    const selectAllCheckbox = screen.getByLabelText("Select all contacts on this page");
    await user.click(selectAllCheckbox);
    expect(screen.getByText("2 selected")).toBeInTheDocument();

    // Click clear selection
    await user.click(screen.getByRole("button", { name: "✕ Clear Selection" }));
    expect(screen.queryByTestId("bulk-action-bar")).not.toBeInTheDocument();
  });

  it("performs bulk delete of selected contacts", async () => {
    let bulkDeletedIds: string[] = [];
    const store = createStore({ active: [ACTIVE_CONTACT, SUPPRESSED_CONTACT] });
    mockedApiFetch.mockImplementation(
      baseContactsMock(store, {
        permissions: ["contacts.view", "contacts.manage"],
        extra: (path, init) => {
          if (path === "/contacts/bulk-delete" && init?.method === "POST") {
            const body = JSON.parse(init.body as string);
            bulkDeletedIds = body.contact_ids;
            store.active = store.active.filter((c) => !bulkDeletedIds.includes(c.id));
            return { deleted_count: bulkDeletedIds.length };
          }
          return undefined;
        },
      }),
    );

    const user = userEvent.setup();
    renderContactsPage();

    await screen.findByText("Alice Anderson");

    // Select Alice
    await user.click(screen.getByLabelText("Select Alice Anderson"));

    // Click Delete Selected in bulk bar
    await user.click(screen.getByRole("button", { name: /Delete Selected/ }));

    // Confirmation modal appears
    expect(screen.getByTestId("delete-confirm-modal")).toBeInTheDocument();
    expect(screen.getByText(/Delete 1 Contacts/)).toBeInTheDocument();

    // Confirm delete
    await user.click(screen.getByRole("button", { name: "Confirm Delete" }));

    await waitFor(() => {
      expect(bulkDeletedIds).toEqual(["contact-1"]);
      expect(screen.queryByText("Alice Anderson")).not.toBeInTheDocument();
      expect(screen.getByText("Bob")).toBeInTheDocument();
    });
  });

  it("performs bulk delete with optional suppression checkbox", async () => {
    const suppressedEmails: string[] = [];
    const store = createStore({ active: [ACTIVE_CONTACT] });
    mockedApiFetch.mockImplementation(
      baseContactsMock(store, {
        permissions: ["contacts.view", "contacts.manage"],
        extra: (path, init) => {
          if (path === "/contacts/suppression" && init?.method === "POST") {
            const body = JSON.parse(init.body as string);
            suppressedEmails.push(body.email);
            return { id: "supp-1", email: body.email };
          }
          if (path === "/contacts/bulk-delete" && init?.method === "POST") {
            store.active = [];
            return { deleted_count: 1 };
          }
          return undefined;
        },
      }),
    );

    const user = userEvent.setup();
    renderContactsPage();

    await screen.findByText("Alice Anderson");
    await user.click(screen.getByLabelText("Select Alice Anderson"));
    await user.click(screen.getByRole("button", { name: /Delete Selected/ }));

    // Check "Also add to suppression list"
    const suppressCheckbox = screen.getByLabelText(/Also add to suppression list/);
    await user.click(suppressCheckbox);

    // Confirm delete
    await user.click(screen.getByRole("button", { name: "Confirm Delete" }));

    await waitFor(() => {
      expect(suppressedEmails).toContain("alice@example.com");
      expect(screen.queryByText("Alice Anderson")).not.toBeInTheDocument();
    });
  });

  it("moves selected contacts to suppression list in bulk", async () => {
    const suppressedEmails: string[] = [];
    const store = createStore({ active: [ACTIVE_CONTACT] });
    mockedApiFetch.mockImplementation(
      baseContactsMock(store, {
        permissions: ["contacts.view", "contacts.manage"],
        extra: (path, init) => {
          if (path === "/contacts/suppression" && init?.method === "POST") {
            const body = JSON.parse(init.body as string);
            suppressedEmails.push(body.email);
            store.active = store.active.map((c) =>
              c.email === body.email ? { ...c, is_suppressed: true } : c,
            );
            return { id: "supp-1", email: body.email };
          }
          return undefined;
        },
      }),
    );

    const user = userEvent.setup();
    renderContactsPage();

    await screen.findByText("Alice Anderson");
    await user.click(screen.getByLabelText("Select Alice Anderson"));

    // Click Move to Suppression
    await user.click(screen.getByRole("button", { name: /Move to Suppression/ }));

    await waitFor(() => {
      expect(suppressedEmails).toContain("alice@example.com");
      expect(screen.getAllByText("Suppressed").length).toBeGreaterThanOrEqual(2);
    });
  });

  it("deletes a single contact from the detail modal with optional suppression", async () => {
    let deletedId: string | null = null;
    const suppressedEmails: string[] = [];
    const store = createStore({ active: [ACTIVE_CONTACT] });

    mockedApiFetch.mockImplementation(
      baseContactsMock(store, {
        permissions: ["contacts.view", "contacts.manage"],
        extra: (path, init) => {
          if (isConsentGet(path, init)) return [];
          if (path === "/contacts/suppression" && init?.method === "POST") {
            const body = JSON.parse(init.body as string);
            suppressedEmails.push(body.email);
            return { id: "supp-1", email: body.email };
          }
          if (path === "/contacts/contact-1" && init?.method === "DELETE") {
            deletedId = "contact-1";
            store.active = store.active.filter((c) => c.id !== "contact-1");
            // DELETE returns a 204 (no body) -- `null` here is the actual response,
            // distinct from `undefined`, which `baseContactsMock` treats as "not handled,
            // fall through to the generic matchers".
            return null;
          }
          return undefined;
        },
      }),
    );

    const user = userEvent.setup();
    renderContactsPage();

    await screen.findByText("Alice Anderson");
    await user.click(screen.getByRole("button", { name: "View" }));

    // Click Delete Contact button inside details modal
    await user.click(screen.getByRole("button", { name: /Delete contact/ }));

    expect(screen.getByTestId("delete-confirm-modal")).toBeInTheDocument();

    // Also check suppression checkbox
    await user.click(screen.getByLabelText(/Also add to suppression list/));
    await user.click(screen.getByRole("button", { name: "Confirm Delete" }));

    await waitFor(() => {
      expect(deletedId).toBe("contact-1");
      expect(suppressedEmails).toContain("alice@example.com");
      expect(screen.queryByText("Alice Anderson")).not.toBeInTheDocument();
    });
  });

  it("purges entire audience when purge button is confirmed", async () => {
    let purgeCalled = false;
    const store = createStore({ active: [ACTIVE_CONTACT, SUPPRESSED_CONTACT] });
    mockedApiFetch.mockImplementation(
      baseContactsMock(store, {
        permissions: ["contacts.view", "contacts.manage"],
        extra: (path, init) => {
          if (path === "/contacts/all" && init?.method === "DELETE") {
            purgeCalled = true;
            store.active = [];
            return { deleted_count: 2 };
          }
          return undefined;
        },
      }),
    );

    const user = userEvent.setup();
    renderContactsPage();

    await screen.findByText("Alice Anderson");

    // Click Purge Audience button
    await user.click(screen.getByRole("button", { name: /Purge Audience/ }));

    expect(screen.getByTestId("delete-confirm-modal")).toBeInTheDocument();
    // Confirm delete is disabled until PURGE is typed
    expect(screen.getByRole("button", { name: "Confirm Delete" })).toBeDisabled();
    await user.type(screen.getByLabelText("Type PURGE to confirm"), "PURGE");
    expect(screen.getByRole("button", { name: "Confirm Delete" })).not.toBeDisabled();

    await user.click(screen.getByRole("button", { name: "Confirm Delete" }));

    await waitFor(() => {
      expect(purgeCalled).toBe(true);
      expect(screen.getByText("No contacts yet.")).toBeInTheDocument();
    });
  });

  it("hides checkboxes and bulk toolbar for view-only users", async () => {
    const store = createStore({ active: [ACTIVE_CONTACT] });
    mockedApiFetch.mockImplementation(baseContactsMock(store, { permissions: ["contacts.view"] }));

    renderContactsPage();

    await screen.findByText("Alice Anderson");
    expect(screen.queryByLabelText("Select all contacts on this page")).not.toBeInTheDocument();
    expect(screen.queryByLabelText("Select Alice Anderson")).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /Purge Audience/ })).not.toBeInTheDocument();
  });

  it("renders deleted tab, fetches deleted contacts, and restores single contact", async () => {
    let restoreCalled = false;
    const store = createStore({ active: [ACTIVE_CONTACT], deleted: [DELETED_CONTACT] });
    mockedApiFetch.mockImplementation(
      baseContactsMock(store, {
        permissions: ["contacts.view", "contacts.manage"],
        extra: (path, init) => {
          if (path === "/contacts/contact-3/restore" && init?.method === "POST") {
            restoreCalled = true;
            store.deleted = store.deleted.filter((c) => c.id !== "contact-3");
            return { ...DELETED_CONTACT, deleted_at: null };
          }
          return undefined;
        },
      }),
    );

    const user = userEvent.setup();
    renderContactsPage();

    await screen.findByText("Alice Anderson");

    // Click Deleted tab
    await user.click(screen.getByRole("button", { name: /Deleted/ }));

    // Charlie Chaplin should appear with Deleted badge
    expect(await screen.findByText("Charlie Chaplin")).toBeInTheDocument();
    expect(screen.getAllByText("Deleted").length).toBeGreaterThanOrEqual(2);

    // Click Restore button
    const restoreBtn = screen.getByRole("button", { name: "🔄 Restore" });
    expect(restoreBtn).toBeInTheDocument();
    await user.click(restoreBtn);

    await waitFor(() => {
      expect(restoreCalled).toBe(true);
      expect(screen.queryByText("Charlie Chaplin")).not.toBeInTheDocument();
    });
  });

  it("supports bulk restore in deleted contacts tab", async () => {
    let bulkRestoreCalled = false;
    const store = createStore({ active: [ACTIVE_CONTACT], deleted: [DELETED_CONTACT] });
    mockedApiFetch.mockImplementation(
      baseContactsMock(store, {
        permissions: ["contacts.view", "contacts.manage"],
        extra: (path, init) => {
          if (path === "/contacts/bulk-restore" && init?.method === "POST") {
            bulkRestoreCalled = true;
            store.deleted = [];
            return { restored_count: 1 };
          }
          return undefined;
        },
      }),
    );

    const user = userEvent.setup();
    renderContactsPage();

    await screen.findByText("Alice Anderson");

    // Switch to Deleted tab
    await user.click(screen.getByRole("button", { name: /Deleted/ }));
    await screen.findByText("Charlie Chaplin");

    // Select Charlie
    await user.click(screen.getByLabelText("Select Charlie Chaplin"));

    // Bulk bar appears with Restore Selected
    const bulkBar = screen.getByTestId("bulk-action-bar");
    expect(within(bulkBar).getByText("1 selected")).toBeInTheDocument();
    const bulkRestoreBtn = within(bulkBar).getByRole("button", { name: "🔄 Restore Selected" });
    await user.click(bulkRestoreBtn);

    await waitFor(() => {
      expect(bulkRestoreCalled).toBe(true);
    });
  });

  it("renders deleted contact notice and restore button inside details modal", async () => {
    let restoreCalled = false;
    const store = createStore({ active: [ACTIVE_CONTACT], deleted: [DELETED_CONTACT] });
    mockedApiFetch.mockImplementation(
      baseContactsMock(store, {
        permissions: ["contacts.view", "contacts.manage"],
        extra: (path, init) => {
          if (isConsentGet(path, init)) return [];
          if (path === "/contacts/contact-3/restore" && init?.method === "POST") {
            restoreCalled = true;
            store.deleted = store.deleted.filter((c) => c.id !== "contact-3");
            return { ...DELETED_CONTACT, deleted_at: null };
          }
          return undefined;
        },
      }),
    );

    const user = userEvent.setup();
    renderContactsPage();

    await screen.findByText("Alice Anderson");

    // Switch to Deleted tab
    await user.click(screen.getByRole("button", { name: /Deleted/ }));
    await screen.findByText("Charlie Chaplin");

    // Open modal
    await user.click(screen.getByRole("button", { name: "View" }));

    expect(await screen.findByText("Soft-deleted Contact:")).toBeInTheDocument();
    const modalRestoreBtn = screen.getByRole("button", { name: "🔄 Restore Contact" });
    expect(modalRestoreBtn).toBeInTheDocument();
    await user.click(modalRestoreBtn);

    await waitFor(() => {
      expect(restoreCalled).toBe(true);
    });
  });

  it("moves selected contacts to tag in bulk", async () => {
    let bulkTagAttached = false;
    const store = createStore({ active: [ACTIVE_CONTACT] });
    mockedApiFetch.mockImplementation(
      baseContactsMock(store, {
        permissions: ["contacts.view", "contacts.manage"],
        tags: [VIP_TAG],
        extra: (path, init) => {
          if (path === "/contacts/contact-1/tags" && init?.method === "POST") {
            bulkTagAttached = true;
            return { ...ACTIVE_CONTACT, tags: [VIP_TAG] };
          }
          return undefined;
        },
      }),
    );

    const user = userEvent.setup();
    renderContactsPage();

    await screen.findByText("Alice Anderson");

    // Select Alice
    const checkbox = screen.getByLabelText("Select Alice Anderson");
    await user.click(checkbox);

    // Bulk bar appears with Move to Tag
    const bulkBar = screen.getByTestId("bulk-action-bar");
    const bulkTagBtn = within(bulkBar).getByRole("button", { name: "🏷️ Move to Tag" });
    await user.click(bulkTagBtn);

    // Modal appears
    expect(await screen.findByText("🏷️ Bulk Move to Tag")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Apply Tag" }));

    await waitFor(() => {
      expect(bulkTagAttached).toBe(true);
    });
  });

  it("adds selected contacts to a list in bulk", async () => {
    let bulkListAttached = false;
    const store = createStore({ active: [ACTIVE_CONTACT] });
    mockedApiFetch.mockImplementation(
      baseContactsMock(store, {
        permissions: ["contacts.view", "contacts.manage"],
        lists: [
          {
            id: "list-1",
            name: "Newsletter",
            description: null,
            member_count: 0,
            created_at: "2026-07-01T00:00:00Z",
            updated_at: "2026-07-01T00:00:00Z",
          },
        ],
        extra: (path, init) => {
          if (path === "/contacts/lists/list-1/members" && init?.method === "POST") {
            bulkListAttached = true;
            return {
              id: "list-1",
              name: "Newsletter",
              description: null,
              member_count: 1,
              created_at: "2026-07-01T00:00:00Z",
              updated_at: "2026-07-01T00:00:00Z",
            };
          }
          return undefined;
        },
      }),
    );

    const user = userEvent.setup();
    renderContactsPage();

    await screen.findByText("Alice Anderson");

    // Select Alice
    const checkbox = screen.getByLabelText("Select Alice Anderson");
    await user.click(checkbox);

    // Bulk bar appears with Add to List
    const bulkBar = screen.getByTestId("bulk-action-bar");
    const bulkListBtn = within(bulkBar).getByRole("button", { name: "📋 Add to List" });
    await user.click(bulkListBtn);

    // Modal appears
    expect(await screen.findByText("📋 Bulk Add to List")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Add to List" }));

    await waitFor(() => {
      expect(bulkListAttached).toBe(true);
    });
  });

  it("searches contacts server-side with a debounced request", async () => {
    // GRX-PERF-001 follow-up: search must hit the backend with a `search` param (not
    // filter a client-held array), and only after the debounce window.
    const store = createStore({ active: [ACTIVE_CONTACT, SUPPRESSED_CONTACT] });
    mockedApiFetch.mockImplementation(
      baseContactsMock(store, { permissions: ["contacts.view", "contacts.manage"] }),
    );

    const user = userEvent.setup();
    renderContactsPage();

    await screen.findByText("Alice Anderson");
    mockedApiFetch.mockClear();

    await user.type(screen.getByPlaceholderText("Search by name, email, or source..."), "alice");

    await waitFor(
      () => {
        const searchCall = mockedApiFetch.mock.calls.find(([path]) =>
          typeof path === "string" ? path.includes("search=alice") : false,
        );
        expect(searchCall).toBeDefined();
      },
      { timeout: 2000 },
    );
  });

  it("shows the account-wide total in the pagination footer, not the page length", async () => {
    // Regression test: "Showing X-Y of Z" and total pages must come from
    // `/contacts/count`, not `pagedContacts.length`.
    const manyActive = Array.from({ length: 30 }, (_, i) => ({
      ...ACTIVE_CONTACT,
      id: `contact-${i}`,
      email: `contact-${i}@example.com`,
      first_name: `Person${i}`,
    }));
    const store = createStore({ active: manyActive });
    mockedApiFetch.mockImplementation(
      baseContactsMock(store, { permissions: ["contacts.view", "contacts.manage"] }),
    );

    renderContactsPage();

    await screen.findByText(/Person0/);
    // 30 matching contacts at the default page size (25) means 2 pages -- if the total
    // pages figure were derived from the fetched page's own length (25), this would
    // wrongly read "Page 1 of 1".
    function hasPageOneOfTwoText(node: Element | null) {
      return node?.textContent === "Page 1 of 2";
    }
    await waitFor(() => {
      expect(
        screen.getByText((_content, element) => {
          if (!hasPageOneOfTwoText(element)) return false;
          return Array.from(element?.children ?? []).every((child) => !hasPageOneOfTwoText(child));
        }),
      ).toBeInTheDocument();
    });
  });
});
