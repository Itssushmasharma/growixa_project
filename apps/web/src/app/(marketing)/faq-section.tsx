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
    answer:
      "Growixa is an AI-powered growth and marketing automation platform. It allows businesses to import contacts, build dynamic segments, draft campaigns using top AI models, run approvals, and dispatch newsletters or social posts—all from a single, unified interface.",
  },
  {
    question: "Can I connect my own Custom SMTP and AI provider keys?",
    answer:
      "Yes! While Growixa offers built-in sending relays via Postmark, you can connect your own SMTP relay (Starter plan and above) or Bring Your Own (BYO) AI keys for OpenAI, Anthropic, Azure, or Ollama (Pro plan) to keep total control of your costs and limits.",
  },
  {
    question: "How is my account data isolated from other customers?",
    answer:
      "Every customer-data table is keyed to your account ID, and all queries enforce strict account-level isolation. Cross-tenant isolation is enforced in code and covered by automated tests. No customer data is ever shared or visible across tenants.",
  },
  {
    question: "How do one-time credit top-ups work?",
    answer:
      "If you exceed your plan's monthly quota (contacts, emails, AI runs, or social posts), you don't need to upgrade your subscription. You can purchase one-time top-up packs directly from your dashboard. These credits never expire and remain in your account until consumed.",
  },
  {
    question: "Are there any onboarding fees or lock-in contracts?",
    answer:
      "No. Growixa features transparent monthly billing with a free tier and no credit card required to get started. You can scale your plan up or down, or manage your subscription at any time with no lock-in contracts or hidden fees.",
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
          const answerId = `faq-answer-${index}`;
          return (
            <div key={index} className={`${styles.faqItem} ${isOpen ? styles.faqItemActive : ""}`}>
              <button
                type="button"
                className={styles.faqQuestionButton}
                onClick={() => toggleFaq(index)}
                aria-expanded={isOpen}
                aria-controls={answerId}
              >
                <span
                  className={`${styles.faqQuestionText} ${isOpen ? styles.faqQuestionTextActive : ""}`}
                >
                  {faq.question}
                </span>
                <span className={`${styles.faqChevron} ${isOpen ? styles.faqChevronOpen : ""}`}>
                  ↓
                </span>
              </button>
              <div
                id={answerId}
                role="region"
                aria-labelledby={`faq-question-${index}`}
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
