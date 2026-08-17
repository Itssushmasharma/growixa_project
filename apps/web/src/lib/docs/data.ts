import type { DocCategory, DocArticle } from "./types";

export const DOC_CATEGORIES: DocCategory[] = [
  {
    id: "getting-started",
    name: "Getting Started",
    description: "Essential setup guides to start sending automated campaigns with Growixa.",
    icon: "🚀",
    color: "#3b82f6",
    articles: [
      {
        slug: "welcome",
        category: "getting-started",
        title: "Welcome to Growixa & Core Concepts",
        excerpt:
          "Learn how Growixa combines contact management, AI content generation, and email automation into a single growth platform.",
        icon: "🌟",
        readingTimeMinutes: 3,
        lastUpdated: "2026-08-17",
        tags: ["welcome", "overview", "architecture", "concepts"],
        sections: [
          {
            id: "what-is-growixa",
            title: "What is Growixa?",
            content:
              "Growixa is an AI-powered marketing and customer engagement platform built for modern businesses, creators, and growth teams. It unifies high-deliverability email campaigns, intelligent audience segmentation, AI marketing copy generation with mandatory human approval, and multichannel automation into a fast, intuitive dashboard.",
          },
          {
            id: "core-pillars",
            title: "The 3 Core Pillars",
            content:
              "Growixa is structured around three foundational pillars that work seamlessly together:\n\n1. **Audience & Contact Engine**: Manage contacts, custom attributes, static lists, dynamic real-time segments, and compliance-first suppression lists.\n2. **AI Marketing Studio**: Generate engaging, high-converting subject lines, social posts, and email bodies with built-in human-in-the-loop safety.\n3. **Campaign Delivery & Scheduling**: Build campaigns with a 5-step wizard, schedule sends, track delivery analytics, and route via Postmark or custom SMTP.",
          },
          {
            id: "next-steps",
            title: "Next Steps",
            content:
              "To get started right away, follow our [Quickstart Guide](/docs/getting-started/quickstart) to add your audience, connect an email sender, and launch your first campaign in under 5 minutes.",
          },
        ],
        relatedSlugs: ["quickstart", "domain-verification"],
      },
      {
        slug: "quickstart",
        category: "getting-started",
        title: "Quickstart: Launch Your First Campaign in 5 Minutes",
        excerpt:
          "A step-by-step walkthrough to import contacts, configure sender identity, and schedule your first email blast.",
        icon: "⚡",
        readingTimeMinutes: 4,
        lastUpdated: "2026-08-17",
        tags: ["quickstart", "tutorial", "first-campaign", "setup"],
        sections: [
          {
            id: "step-1-audience",
            title: "Step 1: Add Your Contacts",
            content:
              "Navigate to **Audience > Contacts** in your dashboard. You can add individual contacts manually or click **Import Contacts** to upload a CSV file. Growixa automatically validates email formats and maps custom fields like First Name, Company, and Phone.",
          },
          {
            id: "step-2-sender",
            title: "Step 2: Connect a Sender Identity",
            content:
              "Go to **Settings > Integrations**. Connect a **Postmark** API token or your **Custom SMTP / Amazon SES** credentials. Ensure you have added your verified sender email (e.g. `newsletter@yourcompany.com`).",
          },
          {
            id: "step-3-create-campaign",
            title: "Step 3: Build & Launch Your Campaign",
            content:
              "Head to **Campaigns > + New Campaign** to launch the 5-step campaign wizard:\n\n1. **Setup**: Name your campaign and write a compelling subject line (or click **'✨ Ask AI'** for subject ideas).\n2. **Audience**: Select 'All Contacts', a static list, or a dynamic segment.\n3. **Template**: Choose a pre-designed responsive template or write custom HTML/Markdown.\n4. **AI Review**: Tune the tone, length, and call-to-action.\n5. **Review & Send**: Choose **Send Now** for immediate delivery or **Schedule** for a future date and time.",
          },
        ],
        relatedSlugs: ["welcome", "campaign-wizard"],
      },
      {
        slug: "domain-verification",
        category: "getting-started",
        title: "Domain Verification, SPF & DKIM Setup",
        excerpt:
          "Configure DNS records to achieve 99%+ email inbox delivery and protect your brand domain reputation.",
        icon: "🛡️",
        readingTimeMinutes: 5,
        lastUpdated: "2026-08-17",
        tags: ["dns", "spf", "dkim", "dmarc", "deliverability", "inbox"],
        sections: [
          {
            id: "why-dns-matters",
            title: "Why DNS Authentication is Critical",
            content:
              "Major email providers like Gmail, Yahoo, and Outlook enforce strict SPF, DKIM, and DMARC authentication policies. Unauthenticated emails are frequently routed to the spam folder or rejected entirely.",
          },
          {
            id: "required-dns-records",
            title: "Required DNS Records",
            content:
              "Add the following records at your DNS host (Cloudflare, GoDaddy, Namecheap, Route53):\n\n- **SPF (TXT)**: `v=spf1 include:spf.mtasv.net ~all` (when using Postmark) or your provider's SPF include.\n- **DKIM (CNAME or TXT)**: Add the 2 DKIM keys provided in your sender settings.\n- **DMARC (TXT)**: `v=DMARC1; p=none; rua=mailto:dmarc-reports@yourdomain.com` at `_dmarc.yourdomain.com`.\n- **Custom Tracking Domain (CNAME)**: Point `links.yourdomain.com` to track open rates and click analytics under your own branded domain.",
          },
        ],
        relatedSlugs: ["quickstart", "postmark-setup"],
      },
    ],
  },
  {
    id: "contacts",
    name: "Audience & Contacts",
    description:
      "Manage subscribers, custom fields, dynamic segments, suppression lists, and contact recovery.",
    icon: "👥",
    color: "#10b981",
    articles: [
      {
        slug: "contact-management",
        category: "contacts",
        title: "Contact Management & Custom Attributes",
        excerpt:
          "Learn how to view, search, tag, and attach custom metadata to your audience contacts.",
        icon: "📇",
        readingTimeMinutes: 4,
        lastUpdated: "2026-08-17",
        tags: ["contacts", "custom-fields", "tags", "attributes"],
        sections: [
          {
            id: "managing-contacts",
            title: "Viewing and Filtering Contacts",
            content:
              "The **Contacts Dashboard** (`/dashboard/contacts`) gives you a single overview of your entire audience. You can filter by status (**All**, **Active**, **Archived**, **Deleted**), search across names, emails, and sources, and paginate across large contact databases.",
          },
          {
            id: "custom-fields",
            title: "Custom Field Attributes",
            content:
              "You can define flexible custom fields such as `company_name`, `plan_type`, `industry`, or `signup_date`. Custom fields can be populated during CSV imports or updated via API, and can be used directly in dynamic segment rules and email template personalization tags.",
          },
          {
            id: "tags",
            title: "Tagging Contacts",
            content:
              "Tags provide lightweight labels (e.g. `VIP`, `Webinar-2026`, `Beta-Tester`) to categorize contacts on the fly. You can attach multiple tags to any contact and filter campaigns accordingly.",
          },
        ],
        relatedSlugs: ["importing-contacts", "segments-and-lists"],
      },
      {
        slug: "importing-contacts",
        category: "contacts",
        title: "Importing Contacts via CSV & Field Mapping",
        excerpt:
          "How to prepare CSV files, map columns, handle duplicates, and inspect import error reports.",
        icon: "📥",
        readingTimeMinutes: 4,
        lastUpdated: "2026-08-17",
        tags: ["import", "csv", "mapping", "subscribers"],
        sections: [
          {
            id: "csv-format",
            title: "Preparing Your CSV File",
            content:
              "Your CSV file should have a header row with columns like `email`, `first_name`, `last_name`, `phone`, and any custom fields. UTF-8 encoding is recommended.",
          },
          {
            id: "column-mapping-step",
            title: "3-Step Import Workflow",
            content:
              "1. **Upload**: Drag and drop your `.csv` file in the Import Hub (`/dashboard/contacts/imports`).\n2. **Map Columns**: Match your CSV header columns to Growixa contact fields (`Email`, `First Name`, `Last Name`, `Phone`, `Source`, `Custom Fields`).\n3. **Process & Inspect**: Growixa processes rows in the background, updating existing contacts and flagging invalid rows with detailed error messages.",
          },
        ],
        relatedSlugs: ["contact-management", "suppression-and-consent"],
      },
      {
        slug: "segments-and-lists",
        category: "contacts",
        title: "Dynamic Rule-Based Segments vs Static Lists",
        excerpt:
          "Target the right audience with real-time dynamic segments and curated static lists.",
        icon: "🎯",
        readingTimeMinutes: 5,
        lastUpdated: "2026-08-17",
        tags: ["segments", "dynamic-rules", "lists", "targeting"],
        sections: [
          {
            id: "dynamic-vs-static",
            title: "Dynamic Segments vs Static Lists",
            content:
              "- **Dynamic Segments**: Automatically recalculate membership in real time based on filter rules (e.g. `status == 'ACTIVE'` AND `created_at > 30 days ago` AND `tag == 'VIP'`). As new contacts join or change attributes, they automatically enter or leave the segment.\n- **Static Lists**: Fixed subscriber groups (e.g. 'Newsletter Subscribers May 2026') where members are added or removed manually.",
          },
          {
            id: "rule-operators",
            title: "Supported Rule Operators",
            content:
              "When building dynamic segments, you can combine rules using operators:\n\n- `EQUALS` / `NOT_EQUALS`\n- `CONTAINS` / `NOT_CONTAINS`\n- `GREATER_THAN` / `LESS_THAN` (for numbers and dates)\n- `IS_SET` / `IS_NOT_SET`",
          },
        ],
        relatedSlugs: ["contact-management", "campaign-wizard"],
      },
      {
        slug: "suppression-and-consent",
        category: "contacts",
        title: "Suppression Lists, Bounces & Consent Compliance",
        excerpt:
          "Comply with GDPR, CAN-SPAM, and CASL regulations with automatic unsubscribe suppression and audit trails.",
        icon: "🚫",
        readingTimeMinutes: 4,
        lastUpdated: "2026-08-17",
        tags: ["suppression", "unsubscribes", "bounces", "consent", "gdpr"],
        sections: [
          {
            id: "suppression-principles",
            title: "How Suppression Works in Growixa",
            content:
              "Growixa maintains an immutable suppression list per tenant. When an email is suppressed (via unsubscribe link, spam complaint, hard bounce, or manual addition):\n\n1. It is permanently blocked from receiving campaign emails.\n2. Even if the email is re-imported from a CSV, it remains suppressed.\n3. Deleting or archiving a contact never removes their suppression status.",
          },
          {
            id: "domain-blocking",
            title: "Domain-Level Suppression",
            content:
              "You can also suppress entire domains (e.g. `@competitor.com` or `@disposable-inbox.net`) to prevent sending to specific organizations or temporary email services.",
          },
        ],
        relatedSlugs: ["contact-management", "restoring-deleted-contacts"],
      },
      {
        slug: "restoring-deleted-contacts",
        category: "contacts",
        title: "Contact Soft Deletes & Audience Restoration",
        excerpt:
          "Recover accidentally deleted contacts individually or in bulk while preserving campaign delivery metrics.",
        icon: "🔄",
        readingTimeMinutes: 4,
        lastUpdated: "2026-08-17",
        tags: ["restore", "soft-delete", "recovery", "retention"],
        sections: [
          {
            id: "soft-delete-architecture",
            title: "Soft Delete Architecture (DEC-GRX-034)",
            content:
              "When a contact is deleted, it is soft-deleted with a timestamp rather than destroyed. This ensures that past campaign delivery reports and historical performance statistics remain referentially valid.",
          },
          {
            id: "how-to-restore",
            title: "Restoring Deleted Contacts",
            content:
              "1. Go to **Audience > Contacts** and click the **'Deleted'** tab.\n2. Click **'🔄 Restore'** on any single contact row, or select multiple contacts with checkboxes and click **'🔄 Restore Selected'**.\n3. Growixa checks your active contact quota (`max_contacts`) and prevents duplicate active email conflicts before restoring.",
          },
        ],
        relatedSlugs: ["contact-management", "suppression-and-consent"],
      },
    ],
  },
  {
    id: "campaigns",
    name: "Campaigns & Email Marketing",
    description:
      "Build responsive emails, schedule automated blasts, and track deliverability metrics.",
    icon: "✉️",
    color: "#8b5cf6",
    articles: [
      {
        slug: "campaign-wizard",
        category: "campaigns",
        title: "5-Step Campaign Creation Wizard",
        excerpt:
          "Walkthrough of the full campaign builder from subject line formulation to audience selection and delivery review.",
        icon: "🪄",
        readingTimeMinutes: 5,
        lastUpdated: "2026-08-17",
        tags: ["campaigns", "wizard", "email-builder", "templates"],
        sections: [
          {
            id: "wizard-steps",
            title: "The 5 Steps Explained",
            content:
              "1. **Campaign Setup**: Specify campaign name, from-address, reply-to, and subject line. Use **'✨ Ask AI'** to generate high-performing variations.\n2. **Audience Selection**: Target your entire audience, specific contact lists, or targeted dynamic segments.\n3. **Template & Content**: Choose responsive email templates or edit rich HTML copy.\n4. **AI Optimization**: Fine-tune tone, urgency, and reading level.\n5. **Review & Schedule**: Send a test email to your inbox, then choose immediate send or schedule for a future date.",
          },
        ],
        relatedSlugs: ["scheduling-and-delivery", "analytics-and-reports"],
      },
      {
        slug: "scheduling-and-delivery",
        category: "campaigns",
        title: "Campaign Scheduling, Queue Throttling & Cancellation",
        excerpt:
          "How Growixa schedules future sends, processes background queues, and allows cancelling queued jobs.",
        icon: "⏱️",
        readingTimeMinutes: 4,
        lastUpdated: "2026-08-17",
        tags: ["scheduler", "queues", "delivery", "rabbitmq"],
        sections: [
          {
            id: "scheduling-workflow",
            title: "Scheduling Future Campaigns",
            content:
              "You can schedule campaigns up to 1 year in advance in your local timezone. Scheduled campaigns appear under the **'Scheduled'** tab with countdown indicators.",
          },
          {
            id: "cancelling-scheduled",
            title: "Cancelling a Scheduled Campaign",
            content:
              "As long as a campaign has not entered the active sending state, you can click **'Cancel Campaign'** to abort the scheduled send and return it to draft status.",
          },
        ],
        relatedSlugs: ["campaign-wizard", "analytics-and-reports"],
      },
      {
        slug: "analytics-and-reports",
        category: "campaigns",
        title: "Campaign Analytics & Deliverability Metrics",
        excerpt:
          "Understand open rates, click-through rates (CTR), bounce classifications, and delivery logs.",
        icon: "📊",
        readingTimeMinutes: 4,
        lastUpdated: "2026-08-17",
        tags: ["analytics", "open-rate", "ctr", "metrics", "reports"],
        sections: [
          {
            id: "key-metrics",
            title: "Understanding Your Metrics",
            content:
              "- **Sent**: Total recipients queued and dispatched.\n- **Delivered**: Messages confirmed received by destination mail servers.\n- **Opens**: Total and unique open counts tracked via invisible tracking pixel.\n- **Clicks**: Unique link clicks across email body CTAs.\n- **Bounces**: Hard bounces (invalid mailbox) and soft bounces (mailbox full / temporary reject).",
          },
        ],
        relatedSlugs: ["campaign-wizard", "scheduling-and-delivery"],
      },
    ],
  },
  {
    id: "ai-assistant",
    name: "AI Marketing Copilot",
    description: "Generate high-converting marketing copy with mandatory human review safeguards.",
    icon: "✨",
    color: "#ec4899",
    articles: [
      {
        slug: "ai-content-studio",
        category: "ai-assistant",
        title: "AI Marketing Studio & Multi-Variation Generation",
        excerpt:
          "Generate subject lines, social media captions, and email bodies tailored by tone, audience, and intent.",
        icon: "🎨",
        readingTimeMinutes: 4,
        lastUpdated: "2026-08-17",
        tags: ["ai", "copilot", "variations", "copywriting", "openai"],
        sections: [
          {
            id: "studio-features",
            title: "The AI Copilot Studio",
            content:
              "Located under `/dashboard/ai`, the AI Marketing Studio allows you to generate content across three primary formats:\n\n1. **Subject Lines**: Punchy, high-open-rate subject ideas.\n2. **Social Captions**: Optimized for Twitter, LinkedIn, and Instagram with hashtags.\n3. **Email Bodies**: Full promotional announcements, newsletter blurbs, and product launch letters.",
          },
          {
            id: "parameter-tuning",
            title: "Tuning AI Parameters",
            content:
              "Customize tone (Professional, Conversational, Urgent, Friendly), target audience description, and temperature to generate 3 distinct creative variations simultaneously.",
          },
        ],
        relatedSlugs: ["human-in-the-loop", "campaign-wizard"],
      },
      {
        slug: "human-in-the-loop",
        category: "ai-assistant",
        title: "Human-in-the-Loop Review & Approval Safety",
        excerpt:
          "Growixa's core safety principle: AI content is always drafted for review and never sent autonomously.",
        icon: "🛡️",
        readingTimeMinutes: 3,
        lastUpdated: "2026-08-17",
        tags: ["safety", "human-in-the-loop", "approval", "compliance"],
        sections: [
          {
            id: "safety-model",
            title: "The Human-in-the-Loop Guarantee",
            content:
              "Growixa strictly enforces human approval for all AI outputs. The AI assistant functions as a creative accelerator, but every generated draft must be reviewed, edited, and explicitly approved by a team member before entering any campaign dispatch queue.",
          },
        ],
        relatedSlugs: ["ai-content-studio", "campaign-wizard"],
      },
    ],
  },
  {
    id: "integrations",
    name: "Integrations & SMTP",
    description: "Connect email delivery providers and custom AI API credentials.",
    icon: "🔌",
    color: "#f59e0b",
    articles: [
      {
        slug: "postmark-setup",
        category: "integrations",
        title: "Connecting Postmark for Email Delivery",
        excerpt:
          "Configure Postmark Server API tokens and message streams for transaction and broadcast delivery.",
        icon: "📨",
        readingTimeMinutes: 4,
        lastUpdated: "2026-08-17",
        tags: ["postmark", "smtp", "integrations", "email-delivery"],
        sections: [
          {
            id: "postmark-configuration",
            title: "Configuring Postmark",
            content:
              "1. Log into your Postmark account and copy your **Server API Token**.\n2. In Growixa, navigate to **Settings > Integrations > Postmark**.\n3. Paste the token and specify your default Broadcast Message Stream ID (`broadcast` or `outbound`).\n4. Click **'Test Connection'** to verify credentials before saving.",
          },
        ],
        relatedSlugs: ["smtp-setup", "domain-verification"],
      },
      {
        slug: "smtp-setup",
        category: "integrations",
        title: "Custom SMTP & Amazon SES Configuration",
        excerpt:
          "Connect your own mail server, SendGrid, Mailgun, or Amazon SES using standard SMTP credentials.",
        icon: "⚙️",
        readingTimeMinutes: 4,
        lastUpdated: "2026-08-17",
        tags: ["smtp", "ses", "sendgrid", "mailgun"],
        sections: [
          {
            id: "smtp-fields",
            title: "SMTP Parameters",
            content:
              "- **Host**: SMTP server host (e.g. `email-smtp.us-east-1.amazonaws.com`).\n- **Port**: Typically `587` (STARTTLS) or `465` (SSL/TLS).\n- **Username & Password**: Mail authentication credentials.\n- **Use TLS**: Check this box for encrypted transport.",
          },
        ],
        relatedSlugs: ["postmark-setup", "domain-verification"],
      },
      {
        slug: "ai-keys",
        category: "integrations",
        title: "Bring Your Own Key (OpenAI & Anthropic)",
        excerpt:
          "Use your own custom OpenAI GPT-4o or Anthropic Claude API keys for unlimited generation.",
        icon: "🔑",
        readingTimeMinutes: 3,
        lastUpdated: "2026-08-17",
        tags: ["openai", "anthropic", "api-keys", "byok"],
        sections: [
          {
            id: "byok-overview",
            title: "Custom AI Provider Keys",
            content:
              "While Growixa provides platform AI credits out of the box, high-volume teams can configure their own OpenAI or Anthropic API keys under **Settings > Integrations > AI Providers** to eliminate rate limits.",
          },
        ],
        relatedSlugs: ["ai-content-studio", "postmark-setup"],
      },
    ],
  },
  {
    id: "billing",
    name: "Billing & Subscriptions",
    description: "Manage subscription tiers, contact quotas, send limits, and Razorpay billing.",
    icon: "💳",
    color: "#06b6d4",
    articles: [
      {
        slug: "plans-and-quotas",
        category: "billing",
        title: "Subscription Plans & Quota Limits",
        excerpt:
          "Understand how contact quotas (max_contacts) and email send allowances work across plan tiers.",
        icon: "📊",
        readingTimeMinutes: 4,
        lastUpdated: "2026-08-17",
        tags: ["billing", "plans", "quotas", "limits", "pricing"],
        sections: [
          {
            id: "quota-rules",
            title: "How Quotas Are Enforced",
            content:
              "- **Active Contacts Quota**: Only contacts with `status == 'ACTIVE'` count toward your plan limit. Soft-deleted and archived contacts do not consume quota.\n- **Email Send Limits**: Monthly send allowances reset at each billing cycle rollover.\n- **Real-Time Warning**: Reaching your quota prevents new contact creations or restorations with a clear upgrade prompt (`HTTP 402`).",
          },
        ],
        relatedSlugs: ["upgrading-plan", "restoring-deleted-contacts"],
      },
      {
        slug: "upgrading-plan",
        category: "billing",
        title: "Upgrading Your Plan & Payment Methods",
        excerpt:
          "Upgrade to Starter, Growth, or Pro plans using international credit cards, net banking, or UPI.",
        icon: "💎",
        readingTimeMinutes: 3,
        lastUpdated: "2026-08-17",
        tags: ["upgrade", "razorpay", "invoices", "payment"],
        sections: [
          {
            id: "upgrade-flow",
            title: "1-Click Plan Upgrades",
            content:
              "Go to **Settings > Billing** (`/dashboard/billing`) to view your current usage, compare plan tiers, and upgrade instantly via Razorpay checkout with instant account quota elevation.",
          },
        ],
        relatedSlugs: ["plans-and-quotas", "welcome"],
      },
    ],
  },
];

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
