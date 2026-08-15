import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ToastProvider } from "@/components/toast/toast-context";
import { apiFetch } from "@/lib/api-client";

import { ContactsPage } from "./contacts-page";
import type { ConsentRecord, Contact, MeResponse, Tag } from "./types";

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

function isTagsGet(path: string, init?: RequestInit): boolean {
  return path === "/contacts/tags" && (!init || init.method === undefined);
}

function isConsentGet(path: string, init?: RequestInit): boolean {
  return /^\/contacts\/[^/]+\/consent$/.test(path) && (!init || init.method === undefined);
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

beforeEach(() => {
  mockedApiFetch.mockReset();
});

describe("ContactsPage", () => {
  it("renders the contact list with status and suppressed badges", async () => {
    mockedApiFetch.mockImplementation((path: string, init?: RequestInit) => {
      if (path === "/auth/me") {
        return Promise.resolve(meWithPermissions(["contacts.view", "contacts.manage"]));
      }
      if (path === "/contacts") return Promise.resolve([ACTIVE_CONTACT, SUPPRESSED_CONTACT]);
      if (isTagsGet(path, init)) return Promise.resolve([]);
      throw new Error(`unexpected path: ${path}`);
    });

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

  it("shows an access-denied message for a user without contacts.view", async () => {
    mockedApiFetch.mockImplementation((path: string, init?: RequestInit) => {
      if (path === "/auth/me") return Promise.resolve(meWithPermissions([]));
      if (path === "/contacts") return Promise.resolve([]);
      if (isTagsGet(path, init)) return Promise.resolve([]);
      throw new Error(`unexpected path: ${path}`);
    });

    renderContactsPage();

    expect(await screen.findByText("You don't have access to view contacts.")).toBeInTheDocument();
  });

  it("hides write controls for a view-only user", async () => {
    mockedApiFetch.mockImplementation((path: string, init?: RequestInit) => {
      if (path === "/auth/me") return Promise.resolve(meWithPermissions(["contacts.view"]));
      if (path === "/contacts") return Promise.resolve([ACTIVE_CONTACT]);
      if (isTagsGet(path, init)) return Promise.resolve([]);
      if (isConsentGet(path, init)) return Promise.resolve([]);
      throw new Error(`unexpected path: ${path}`);
    });

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
    const created: Contact = { ...ACTIVE_CONTACT, id: "contact-3", email: "new@example.com" };
    mockedApiFetch.mockImplementation((path: string, init?: RequestInit) => {
      if (path === "/auth/me") {
        return Promise.resolve(meWithPermissions(["contacts.view", "contacts.manage"]));
      }
      if (path === "/contacts" && (!init || init.method === undefined)) {
        return Promise.resolve([]);
      }
      if (isTagsGet(path, init)) return Promise.resolve([]);
      if (path === "/contacts" && init?.method === "POST") {
        return Promise.resolve(created);
      }
      throw new Error(`unexpected call: ${path}`);
    });

    const user = userEvent.setup();
    renderContactsPage();

    await screen.findByText("No contacts yet.");
    await user.click(screen.getByRole("button", { name: "+ Add contact" }));
    await user.type(screen.getByLabelText("Email"), "new@example.com");
    await user.click(screen.getByRole("button", { name: "Create contact" }));

    await waitFor(() => expect(screen.getByText("new@example.com")).toBeInTheDocument());
  });

  it("edits a contact via the inline detail panel", async () => {
    mockedApiFetch.mockImplementation((path: string, init?: RequestInit) => {
      if (path === "/auth/me") {
        return Promise.resolve(meWithPermissions(["contacts.view", "contacts.manage"]));
      }
      if (path === "/contacts" && (!init || init.method === undefined)) {
        return Promise.resolve([ACTIVE_CONTACT]);
      }
      if (isTagsGet(path, init)) return Promise.resolve([]);
      if (isConsentGet(path, init)) return Promise.resolve([]);
      if (path === "/contacts/contact-1" && init?.method === "PATCH") {
        return Promise.resolve({ ...ACTIVE_CONTACT, first_name: "Alicia" });
      }
      throw new Error(`unexpected call: ${path}`);
    });

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
    mockedApiFetch.mockImplementation((path: string, init?: RequestInit) => {
      if (path === "/auth/me") {
        return Promise.resolve(meWithPermissions(["contacts.view", "contacts.manage"]));
      }
      if (path === "/contacts" && (!init || init.method === undefined)) {
        return Promise.resolve([ACTIVE_CONTACT]);
      }
      if (isTagsGet(path, init)) return Promise.resolve([]);
      if (isConsentGet(path, init)) return Promise.resolve([]);
      if (path === "/contacts/contact-1/status" && init?.method === "PATCH") {
        return Promise.resolve({ ...ACTIVE_CONTACT, status: "ARCHIVED" });
      }
      throw new Error(`unexpected call: ${path}`);
    });

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
    mockedApiFetch.mockImplementation((path: string, init?: RequestInit) => {
      if (path === "/auth/me") {
        return Promise.resolve(meWithPermissions(["contacts.view", "contacts.manage"]));
      }
      if (path === "/contacts" && (!init || init.method === undefined)) {
        return Promise.resolve([ACTIVE_CONTACT]);
      }
      if (isTagsGet(path, init)) return Promise.resolve([VIP_TAG]);
      if (isConsentGet(path, init)) return Promise.resolve([]);
      if (path === "/contacts/contact-1/tags" && init?.method === "POST") {
        return Promise.resolve({ ...ACTIVE_CONTACT, tags: ["VIP"] });
      }
      throw new Error(`unexpected call: ${path}`);
    });

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
    mockedApiFetch.mockImplementation((path: string, init?: RequestInit) => {
      if (path === "/auth/me") {
        return Promise.resolve(meWithPermissions(["contacts.view", "contacts.manage"]));
      }
      if (path === "/contacts" && (!init || init.method === undefined)) {
        return Promise.resolve([tagged]);
      }
      if (isTagsGet(path, init)) return Promise.resolve([VIP_TAG]);
      if (isConsentGet(path, init)) return Promise.resolve([]);
      if (path === "/contacts/contact-1/tags/tag-1" && init?.method === "DELETE") {
        return Promise.resolve({ ...ACTIVE_CONTACT, tags: [] });
      }
      throw new Error(`unexpected call: ${path}`);
    });

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
    mockedApiFetch.mockImplementation((path: string, init?: RequestInit) => {
      if (path === "/auth/me") {
        return Promise.resolve(meWithPermissions(["contacts.view", "contacts.manage"]));
      }
      if (path === "/contacts" && (!init || init.method === undefined)) {
        return Promise.resolve([ACTIVE_CONTACT]);
      }
      if (isTagsGet(path, init)) return Promise.resolve([]);
      if (isConsentGet(path, init)) return Promise.resolve([]);
      if (path === "/contacts/tags" && init?.method === "POST") {
        return Promise.resolve(createdTag);
      }
      if (path === "/contacts/contact-1/tags" && init?.method === "POST") {
        return Promise.resolve({ ...ACTIVE_CONTACT, tags: ["Newsletter"] });
      }
      throw new Error(`unexpected call: ${path}`);
    });

    const user = userEvent.setup();
    renderContactsPage();

    await screen.findByText("Alice Anderson");
    await user.click(screen.getByRole("button", { name: "View" }));
    await user.type(screen.getByLabelText("New tag name"), "Newsletter");
    await user.click(screen.getByRole("button", { name: "+ New tag" }));

    await waitFor(() => expect(screen.getByText("Newsletter")).toBeInTheDocument());
  });

  it("loads and displays a contact's consent history", async () => {
    mockedApiFetch.mockImplementation((path: string, init?: RequestInit) => {
      if (path === "/auth/me") {
        return Promise.resolve(meWithPermissions(["contacts.view", "contacts.manage"]));
      }
      if (path === "/contacts" && (!init || init.method === undefined)) {
        return Promise.resolve([ACTIVE_CONTACT]);
      }
      if (isTagsGet(path, init)) return Promise.resolve([]);
      if (isConsentGet(path, init)) return Promise.resolve([GRANTED_CONSENT]);
      throw new Error(`unexpected call: ${path}`);
    });

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
    mockedApiFetch.mockImplementation((path: string, init?: RequestInit) => {
      if (path === "/auth/me") {
        return Promise.resolve(meWithPermissions(["contacts.view", "contacts.manage"]));
      }
      if (path === "/contacts" && (!init || init.method === undefined)) {
        return Promise.resolve([ACTIVE_CONTACT]);
      }
      if (isTagsGet(path, init)) return Promise.resolve([]);
      if (isConsentGet(path, init)) return Promise.resolve([]);
      if (path === "/contacts/contact-1/consent" && init?.method === "POST") {
        return Promise.resolve(newRecord);
      }
      throw new Error(`unexpected call: ${path}`);
    });

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
});
