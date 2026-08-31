import styles from "./marquee.module.css";

const ROW_A = [
  "Apollo",
  "Mailchimp",
  "Clay",
  "Lemlist",
  "Hunter.io",
  "ZoomInfo",
  "Klaviyo",
  "Outreach",
  "Smartlead",
  "Instantly",
  "Clearbit",
  "Brevo",
];

const ROW_B = [
  "NeverBounce",
  "Copy.ai",
  "Jasper",
  "Woodpecker",
  "Warmbox",
  "HubSpot Starter",
  "Zapier",
  "RB2B",
  "Common Room",
  "Factors.ai",
  "Sendgrid",
  "Buffer",
];

interface RowProps {
  items: string[];
  className?: string;
}

function Row({ items, className = "" }: RowProps) {
  // Duplicate for seamless infinite loop
  const list = [...items, ...items];
  return (
    <div className={className} aria-hidden="true">
      {list.map((name, i) => (
        <span key={`${name}-${i}`} className={styles.tool}>
          {name}
        </span>
      ))}
    </div>
  );
}

export default function Marquee() {
  return (
    <div className={styles.marquee}>
      <span className={styles.label}>Cancel these</span>
      <Row items={ROW_A} className={`${styles.row} ${styles.left}`} />
      <Row items={ROW_B} className={`${styles.row} ${styles.right}`} />
      <p className={styles.sr}>
        Growixa replaces tools including Apollo, Mailchimp, Clay, Lemlist, Hunter.io, ZoomInfo,
        Klaviyo, Outreach and Zapier.
      </p>
    </div>
  );
}
