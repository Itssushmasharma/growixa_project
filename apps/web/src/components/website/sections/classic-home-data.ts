export interface FeatureItem {
  icon: string;
  tag: string;
  title: string;
  copy: string;
}

export const FEATURES: FeatureItem[] = [
  {
    icon: "◎",
    tag: "Audience AI",
    title: "Audience intelligence",
    copy: "Organize contacts, custom properties, and behavioral segments with zero data friction.",
  },
  {
    icon: "✉",
    tag: "Sequences",
    title: "Email campaigns",
    copy: "Create, review, schedule and measure multi-step campaigns with suppression protection built in.",
  },
  {
    icon: "✦",
    tag: "Brand Voice",
    title: "AI Content Studio",
    copy: "Generate brand-aware drafts, then edit and approve before anything goes out.",
  },
  {
    icon: "◫",
    tag: "Timeline",
    title: "Marketing calendar",
    copy: "See campaigns and scheduled social content together on one calendar before you publish.",
  },
  {
    icon: "✓",
    tag: "Safety Gate",
    title: "Human approvals",
    copy: "Keep consequential actions under team control with clear deterministic review states.",
  },
  {
    icon: "↗",
    tag: "Telemetry",
    title: "Actionable analytics",
    copy: "Move from what happened to why it matters, conversion depth, and what to improve next.",
  },
];

export const FAQS = [
  [
    "Can I start without a credit card?",
    "Yes. Create a workspace and explore the available free plan before choosing a paid plan.",
  ],
  [
    "Does AI publish automatically?",
    "No. Growixa keeps a human review and approval step before consequential external actions.",
  ],
  [
    "Can I import my existing contacts?",
    "Yes. Growixa supports CSV contact import, field mapping, lists, segments and suppression handling.",
  ],
  [
    "Which marketing channels are available?",
    "Email campaign workflows are available now. Social publishing depends on the integrations enabled for your workspace.",
  ],
] as const;
