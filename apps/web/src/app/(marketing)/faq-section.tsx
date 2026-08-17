"use client";

import { useState } from "react";
import styles from "./marketing.module.css";

interface FAQItem {
  question: string;
  answer: string;
}

const faqs: FAQItem[] = [
  {
    question: "What exactly is Growixa?",
    answer: "Growixa is an AI-powered growth and marketing automation platform. It allows businesses to import contacts, build dynamic segments, draft campaigns using top AI models, run approvals, and dispatch newsletters or social posts—all from a single, unified interface.",
  },
  {
    question: "Can I connect my own Custom SMTP and AI provider keys?",
    answer: "Yes! While Growixa offers built-in sending relays via Postmark, you can connect your own SMTP relay (Starter plan and above) or Bring Your Own (BYO) AI keys for OpenAI, Anthropic, Azure, or Ollama (Pro plan) to keep total control of your costs and limits.",
  },
  {
    question: "How is my account data isolated from other customers?",
    answer: "Growixa operates a secure multi-tenant architecture. Every single database table is keyed with a tenant account ID, and all queries enforce strict account-level isolation. No data is ever shared or visible across tenants.",
  },
  {
    question: "How do one-time credit top-ups work?",
    answer: "If you exceed your plan's monthly quota (contacts, emails, AI runs, or social posts), you don't need to upgrade your subscription. You can purchase one-time top-up packs directly from your dashboard. These credits never expire and remain in your account until consumed.",
  },
  {
    question: "Are there any onboarding fees or lock-in contracts?",
    answer: "No. Growixa features transparent monthly billing with a 14-day free trial (no credit card required). You can scale your plan up or down, or cancel at any time directly from your billing panel with no penalties or hidden fees.",
  },
];

export function FaqSection() {
  const [openIndex, setOpenIndex] = useState<number | null>(null);

  const toggleFaq = (index: number) => {
    setOpenIndex(openIndex === index ? null : index);
  };

  return (
    <section className={styles.faqSection} id="faq">
      <div className={styles.faqHeader}>
        <span className={styles.faqTag}>Got Questions?</span>
        <h2 className={styles.faqTitle}>Frequently Asked Questions</h2>
        <p className={styles.faqSubtitle}>
          Everything you need to know about plans, credits, and integrations.
        </p>
      </div>

      <div className={styles.faqAccordionContainer}>
        {faqs.map((faq, index) => {
          const isOpen = openIndex === index;
          return (
            <div
              key={index}
              className={`${styles.faqItem} ${isOpen ? styles.faqItemActive : ""}`}
            >
              <button
                type="button"
                className={styles.faqQuestionButton}
                onClick={() => toggleFaq(index)}
                aria-expanded={isOpen}
              >
                <span
                  className={`${styles.faqQuestionText} ${isOpen ? styles.faqQuestionTextActive : ""}`}
                >
                  {faq.question}
                </span>
                <span
                  className={`${styles.faqChevron} ${isOpen ? styles.faqChevronOpen : ""}`}
                >
                  ↓
                </span>
              </button>
              <div
                className={`${styles.faqAnswerContainer} ${
                  isOpen ? styles.faqAnswerContainerOpen : ""
                }`}
              >
                <div className={styles.faqAnswerInner}>
                  <div
                    className={`${styles.faqAnswerText} ${isOpen ? styles.faqAnswerTextVisible : ""}`}
                  >
                    {faq.answer}
                  </div>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}
