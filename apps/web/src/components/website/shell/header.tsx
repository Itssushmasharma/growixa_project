"use client";

import React, { useState } from "react";
import Link from "next/link";
import MegaMenu from "./mega-menu";
import MobileNav from "./mobile-nav";
import Button from "../primitives/button";
import Wrap from "../layout/wrap";
import { Phone, Mail, MessageSquare, Sparkles, ChevronDown } from "lucide-react";
import styles from "./header.module.css";

const SMS_SERVICES = [
  {
    id: "trans-sms",
    name: "Transactional SMS",
    blurb: "Instant 99.99% deliverability OTPs & transaction notifications.",
    hue: "send",
    path: "/services/sms",
  },
  {
    id: "whatsapp-api",
    name: "WhatsApp Business API",
    blurb: "Rich media messages, catalog sync, and interactive reply buttons.",
    hue: "create",
    path: "/dashboard/communications",
  },
  {
    id: "bulk-sms",
    name: "Bulk SMS Broadcast",
    blurb: "High-volume DLT approved promotional & transactional messaging.",
    hue: "find",
    path: "/services/bulk-sms",
  },
  {
    id: "otp-verify",
    name: "OTP Verification",
    blurb: "Sub-second 2FA authentication & phone verification engine.",
    hue: "qualify",
    path: "/services/otp",
  },
];

const DIGITAL_SERVICES = [
  {
    id: "creative-studio",
    name: "Creative Studio",
    blurb: "AI social creatives, banners, flyers, posters, and ad stories.",
    hue: "create",
    path: "/dashboard/creative-studio",
  },
  {
    id: "ads-hub",
    name: "Ads Hub (Google & Meta)",
    blurb: "Unified ad campaign workspace, audience builder, and ROAS telemetry.",
    hue: "find",
    path: "/dashboard/ads-hub",
  },
  {
    id: "lead-gen",
    name: "Lead Generation Engine",
    blurb: "Landing page forms, lead capture, source UTM attribution, and CRM routing.",
    hue: "qualify",
    path: "/dashboard/lead-gen",
  },
  {
    id: "marketing-planner",
    name: "AI Marketing Planner",
    blurb: "Automated GTM plans, content calendar, and channel strategy.",
    hue: "manage",
    path: "/dashboard/planner",
  },
  {
    id: "unified-analytics",
    name: "Unified Analytics",
    blurb: "Full GTM funnel metrics, campaign attribution, and conversion telemetry.",
    hue: "send",
    path: "/dashboard/analytics",
  },
];

const WEBSITE_SEO_SERVICES = [
  {
    id: "landing-builder",
    name: "Landing Page Builder",
    blurb: "High-converting responsive landing page builder & form studio.",
    hue: "create",
    path: "/dashboard/business-presence",
  },
  {
    id: "seo-audit",
    name: "SEO Health Audit",
    blurb: "Real-time BeautifulSoup crawler for technical & on-page checks.",
    hue: "qualify",
    path: "/dashboard/seo",
  },
  {
    id: "keyword-explorer",
    name: "Keyword Explorer & Planner",
    blurb: "Identify high-intent search terms and content suggestions.",
    hue: "find",
    path: "/dashboard/seo",
  },
  {
    id: "local-gbp",
    name: "Local SEO & Google Business",
    blurb: "Optimize local citations, reviews, and Google Business Profile.",
    hue: "manage",
    path: "/dashboard/seo",
  },
];

const ENTERPRISE_SERVICES = [
  {
    id: "smtp-relay",
    name: "Custom Postmark Relays",
    blurb: "Dedicated IP pools, RFC 8058 headers, and inbox warmup.",
    hue: "send",
    path: "/dashboard/company-settings",
  },
  {
    id: "audit-logging",
    name: "Bank-Grade Security",
    blurb: "SOC2 ready, Argon2id hashing, and append-only audit trail logs.",
    hue: "qualify",
    path: "/dashboard/audit",
  },
  {
    id: "agency-reseller",
    name: "Agency & Reseller Portal",
    blurb: "Multi-tenant workspace management, custom domain branding, and sub-accounts.",
    hue: "create",
    path: "/dashboard/agencies",
  },
];

export default function Header() {
  return (
    <header className={styles.hdrWrapper}>
      {/* Top Utility Bar (Contact info, WhatsApp support, Quick links) */}
      <div className={styles.topBar}>
        <Wrap className={styles.topBarWrap}>
          <div className={styles.topBarLeft}>
            <a href="tel:+919205067380" className={styles.topContactItem}>
              <Phone className="w-3.5 h-3.5 text-rose-700" />
              <span>+91-9205067380</span>
            </a>
            <span className={styles.topDivider}>|</span>
            <a href="mailto:info@growixa.com" className={styles.topContactItem}>
              <Mail className="w-3.5 h-3.5 text-rose-700" />
              <span>info@growixa.com</span>
            </a>
          </div>

          <div className={styles.topBarRight}>
            <Link href="/login" className={styles.topLink}>
              Sign In
            </Link>
            <span className={styles.topDivider}>|</span>
            <Link href="/pricing" className={styles.topLink}>
              Pay Now
            </Link>
            <span className={styles.topDivider}>|</span>
            <Link href="/dashboard/agencies" className={styles.topLink}>
              Reseller / Agency
            </Link>
            <a
              href="https://wa.me/919205067380"
              target="_blank"
              rel="noopener noreferrer"
              className={styles.topWhatsappBtn}
              title="Chat on WhatsApp"
            >
              <MessageSquare className="w-3.5 h-3.5 fill-current" />
              <span>WhatsApp Us</span>
            </a>
          </div>
        </Wrap>
      </div>

      {/* Main Navigation Header Bar */}
      <div className={styles.mainHdr}>
        <Wrap>
          <nav className={styles.nav} aria-label="Main Navigation">
            {/* Crisp High-Contrast Growixa Logo */}
            <Link href="/" className={styles.brand}>
              <span className={styles.mark} aria-hidden="true">
                <svg width="18" height="18" viewBox="0 0 14 14">
                  <path d="M7.6 1 2.6 8h3.1l-.5 5 5-7H7.1z" fill="#6D0626" />
                </svg>
              </span>
              <div className={styles.brandTextGroup}>
                <span className={styles.brandName}>Growixa<sup>®</sup></span>
                <span className={styles.brandTagline}>Growth Engine</span>
              </div>
            </Link>

            {/* Navigation Menu Items */}
            <div className={styles.links}>
              <Link href="/" className={styles.link}>
                Home
              </Link>
              <MegaMenu label="SMS & WhatsApp" items={SMS_SERVICES} />
              <MegaMenu label="Digital Services" items={DIGITAL_SERVICES} />
              <MegaMenu label="Website & SEO" items={WEBSITE_SEO_SERVICES} />
              <MegaMenu label="Enterprise" items={ENTERPRISE_SERVICES} />
              <Link href="/pricing" className={styles.link}>
                Pricing
              </Link>
              <Link href="/roadmap" className={styles.link}>
                Roadmap
              </Link>
              <Link href="/contact" className={styles.link}>
                Contact Us
              </Link>
            </div>

            {/* Right Action Buttons */}
            <div className={styles.cta}>
              <Link href="/login" className={styles.login}>
                Log in
              </Link>
              <Button as={Link} href="/register" size="sm">
                Start free
              </Button>
              <MobileNav />
            </div>
          </nav>
        </Wrap>
      </div>
    </header>
  );
}
