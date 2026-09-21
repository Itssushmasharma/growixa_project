import React from "react";
import styles from "./ecosystem.module.css";
import { 
  Mail, 
  Cpu, 
  CreditCard, 
  Share2, 
  Globe, 
  Zap, 
  ZapIcon 
} from "lucide-react";

interface StepNode {
  step: string;
  category: string;
  name: string;
  desc: string;
  icon: React.ReactNode;
  pos: { left: string; top: string };
  isRightSide?: boolean;
}

const NODES: StepNode[] = [
  {
    step: "01",
    category: "Email Relay",
    name: "Postmark Relay",
    desc: "Transactional SMTP delivery with real-time open & bounce webhooks.",
    icon: <Mail className="w-5 h-5 text-rose-700" />,
    pos: { left: "18%", top: "20%" },
  },
  {
    step: "02",
    category: "LLM Provider",
    name: "OpenAI & Claude",
    desc: "GPT-4o & Claude Sonnet models for AI copy generation.",
    icon: <Cpu className="w-5 h-5 text-rose-700" />,
    pos: { left: "14%", top: "50%" },
  },
  {
    step: "03",
    category: "Payment Gateway",
    name: "Razorpay & Stripe",
    desc: "Global INR & USD subscription checkout & credit orders.",
    icon: <CreditCard className="w-5 h-5 text-rose-700" />,
    pos: { left: "18%", top: "80%" },
  },
  {
    step: "04",
    category: "Social Media",
    name: "Meta Ads & Instagram",
    desc: "Direct post publishing, scheduling & engagement analytics.",
    icon: <Share2 className="w-5 h-5 text-rose-700" />,
    pos: { left: "82%", top: "20%" },
    isRightSide: true,
  },
  {
    step: "05",
    category: "Identity & Alerts",
    name: "Google & Slack",
    desc: "OAuth 2.0 SSO ready & instant channel lead notifications.",
    icon: <Globe className="w-5 h-5 text-rose-700" />,
    pos: { left: "86%", top: "50%" },
    isRightSide: true,
  },
  {
    step: "06",
    category: "Automation",
    name: "Zapier & Webhooks",
    desc: "2,000+ app triggers to sync contacts & trigger workflows.",
    icon: <Zap className="w-5 h-5 text-rose-700" />,
    pos: { left: "82%", top: "80%" },
    isRightSide: true,
  },
];

export function EcosystemSection() {
  return (
    <section className={styles.section} id="ecosystem">
      <div className={styles.header}>
        <div className={styles.eyebrow}>
          <ZapIcon className="w-4 h-4" /> Native Integrations
        </div>
        <h2 className={styles.title}>
          Ecosystem — Connects With Your <span>Tech Stack</span>
        </h2>
        <p className={styles.subtitle}>
          Native integrations with leading email relays, payment gateways, LLMs, and social platforms.
        </p>
      </div>

      {/* Radial Sunburst Orbit Infographic Stage (Reference Image Layout) */}
      <div className={styles.orbitStage}>
        {/* SVG Concentric Orbit Rings & Radial Connector Spokes */}
        <svg className={styles.orbitSvg} viewBox="0 0 1100 650">
          {/* Inner Orbit Circle */}
          <circle cx="550" cy="325" r="220" className={styles.orbitRingPath1} />
          {/* Outer Orbit Circle */}
          <circle cx="550" cy="325" r="340" className={styles.orbitRingPath2} />

          {/* Spoke Lines from Center Hub to 6 Radial Nodes */}
          <line x1="550" y1="325" x2="200" y2="130" className={styles.spokeLine} />
          <line x1="550" y1="325" x2="160" y2="325" className={styles.spokeLine} />
          <line x1="550" y1="325" x2="200" y2="520" className={styles.spokeLine} />

          <line x1="550" y1="325" x2="900" y2="130" className={styles.spokeLine} />
          <line x1="550" y1="325" x2="940" y2="325" className={styles.spokeLine} />
          <line x1="550" y1="325" x2="900" y2="520" className={styles.spokeLine} />

          {/* Dot Pins at Ends */}
          <circle cx="200" cy="130" r="5" className={styles.spokeDot} />
          <circle cx="160" cy="325" r="5" className={styles.spokeDot} />
          <circle cx="200" cy="520" r="5" className={styles.spokeDot} />

          <circle cx="900" cy="130" r="5" className={styles.spokeDot} />
          <circle cx="940" cy="325" r="5" className={styles.spokeDot} />
          <circle cx="900" cy="520" r="5" className={styles.spokeDot} />
        </svg>

        {/* Central Multi-Ring Orbit Hub */}
        <div className={styles.centerOrbitHub}>
          <span className={styles.hubTag}>GROWIXA CORE</span>
          <h3 className={styles.hubTitle}>NATIVE ENGINE</h3>
          <span className={styles.hubSub}>Unified Tech Stack</span>
        </div>

        {/* 6 Radial Step Node Badges & Info Blocks */}
        {NODES.map((n) => (
          <div
            key={n.step}
            className={styles.radialNodeWrapper}
            style={{
              left: n.pos.left,
              top: n.pos.top,
              flexDirection: n.isRightSide ? "row-reverse" : "row",
            }}
          >
            <div className={styles.stepCircleNode}>
              <span className={styles.stepNum}>STEP</span>
              <span className={styles.stepVal}>{n.step}</span>
            </div>

            <div className={styles.infoBlock}>
              <div className={styles.infoCategory}>{n.category}</div>
              <h4 className={styles.infoTitle}>{n.name}</h4>
              <p className={styles.infoDesc}>{n.desc}</p>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
