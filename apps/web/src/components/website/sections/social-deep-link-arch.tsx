import React from "react";
import styles from "./social-deep-link-arch.module.css";
import { 
  Link2, 
  Share2, 
  MessageCircle, 
  Globe, 
  Sparkles,
  ExternalLink
} from "lucide-react";

export function SocialDeepLinkArchSection() {
  return (
    <section className={styles.section} id="omnichannel">
      <div className={styles.header}>
        <div className={styles.eyebrow}>
          <Link2 className="w-4 h-4" /> Omnichannel Deep Link Engine
        </div>
        <h2 className={styles.title}>
          Drive Audience To The Right Channel, <span>Every Time</span>
        </h2>
        <p className={styles.subtitle}>
          Omnichannel deep links ensure every campaign click lands exactly where it converts best — Instagram, LinkedIn, or Email.
        </p>
      </div>

      {/* Arch of Social Icons matching Image 3 */}
      <div className={styles.archWrapper}>
        <div className={styles.iconArch}>
          <div className={styles.archIconPill} style={{ marginBottom: "0px" }}>
            <Share2 className="w-6 h-6 text-pink-400" />
          </div>
          <div className={styles.archIconPill} style={{ marginBottom: "25px" }}>
            <Share2 className="w-6 h-6 text-sky-400" />
          </div>
          <div className={styles.archIconPill} style={{ marginBottom: "45px" }}>
            <Globe className="w-6 h-6 text-rose-500" />
          </div>
          <div className={styles.archIconPill} style={{ marginBottom: "55px" }}>
            <MessageCircle className="w-6 h-6 text-emerald-400" />
          </div>
          <div className={styles.archIconPill} style={{ marginBottom: "45px" }}>
            <Share2 className="w-6 h-6 text-blue-400" />
          </div>
          <div className={styles.archIconPill} style={{ marginBottom: "25px" }}>
            <Globe className="w-6 h-6 text-purple-400" />
          </div>
          <div className={styles.archIconPill} style={{ marginBottom: "0px" }}>
            <Sparkles className="w-6 h-6 text-amber-400" />
          </div>
        </div>
      </div>

      {/* Deep Link Preview Card matching Image 3 */}
      <div className={styles.previewCard}>
        <div className={styles.cardHeader}>
          <div className={styles.platformTitle}>
            <Share2 className="w-5 h-5 text-pink-400" /> Social Business Direct Dispatch
          </div>
          <span className={styles.badgeDeepLink}>Deep Link Active</span>
        </div>
        <div className={styles.urlBar}>
          <span>co.growixa.link/campaign/launch-2026</span>
          <ExternalLink className="w-4 h-4 text-emerald-400" />
        </div>
      </div>
    </section>
  );
}
