import React from "react";
import styles from "./why-choose-growixa.module.css";
import { Zap } from "lucide-react";

export function WhyChooseGrowixaSection() {
  const CARDS = [
    {
      num: "1",
      title: "Simple to set up and manage without needing technical skills.",
      desc: "Intuitive visual campaign builder and pre-built audience templates get you launched in minutes.",
      isDark: true,
      align: "left",
    },
    {
      num: "2",
      title: "Secure, reliable, and trusted by growing digital businesses.",
      desc: "Bank-grade data isolation, encrypted token storage, and high-deliverability Postmark SMTP relays.",
      isDark: false,
      align: "right",
    },
    {
      num: "3",
      title: "Offers built-in tools for marketing, AI copy, SEO, and sales optimization.",
      desc: "All-in-one suite combining AI content generation, multi-channel social scheduling, and live CRM telemetry.",
      isDark: true,
      align: "left",
    },
    {
      num: "4",
      title: "Easily scalable to support your business as it grows.",
      desc: "Flexible tenant quotas, multi-domain sending capabilities, and team role permissions that scale effortlessly.",
      isDark: false,
      align: "right",
    },
  ];

  return (
    <section className={styles.section} id="why-growixa">
      {/* Background Brand Watermark */}
      <div className={styles.watermarkText} aria-hidden="true">
        GROWIXA
      </div>

      <div className={styles.header}>
        <div className={styles.eyebrow}>
          <Zap className="w-4 h-4" /> Why Choose Growixa
        </div>
        <h2 className={styles.title}>
          Why <span>GROWIXA PLATFORM</span> is Essential for Growing Your Business
        </h2>
        <p className={styles.subtitle}>
          One connected workspace designed to replace fragmented tools and accelerate audience conversion.
        </p>
      </div>

      {/* Staggered Card Flow Container (Matching Reference Layout) */}
      <div className={styles.staggerContainer}>
        {CARDS.map((card) => (
          <div
            key={card.num}
            className={`${styles.staggerCard} ${
              card.isDark ? styles.darkCard : styles.lightCard
            } ${card.align === "left" ? styles.shiftLeft : styles.shiftRight}`}
          >
            <div
              className={`${styles.badgeCircle} ${
                card.align === "left" ? styles.badgeLeft : styles.badgeRight
              }`}
            >
              {card.num}
            </div>

            <div className={styles.cardContent}>
              <h3 className={styles.cardTitle}>{card.title}</h3>
              <p className={styles.cardDesc}>{card.desc}</p>
            </div>
          </div>
        ))}
      </div>

      <div className={styles.hashtagFooter}>#growwithgrowixa</div>
    </section>
  );
}
