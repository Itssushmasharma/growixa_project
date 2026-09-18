"use client";

import React from 'react';
import styles from './socialpilot-home.module.css';

export function SocialPilotFeaturesGrid() {
  const features = [
    {
      title: 'Publishing & Scheduling',
      description: 'Create, schedule, and publish posts to all major social platforms from a single intuitive dashboard. Customize for each network.',
      icon: '📝',
    },
    {
      title: 'Analytics & Reporting',
      description: 'Prove your ROI with beautiful, white-label analytics reports. Track engagement, audience growth, and campaign performance automatically.',
      icon: '📊',
    },
    {
      title: 'Social Inbox',
      description: 'Never miss a comment, message, or mention. Engage with your audience across all platforms from one unified inbox.',
      icon: '📥',
    },
    {
      title: 'Collaboration workflows',
      description: 'Streamline team approvals and invite clients to review content without sharing passwords. Setup custom roles and permissions.',
      icon: '👥',
    }
  ];

  return (
    <section className={styles.section} style={{ paddingTop: '5rem', paddingBottom: '5rem' }}>
      <div className={styles.textCenter} style={{ marginBottom: '4rem' }}>
        <h2 className={styles.h2}>Everything you need to hit your social media goals</h2>
        <p className={styles.subtitle}>
          Stop switching between tabs. Manage your entire social media presence from one powerful, intuitive platform built for growth.
        </p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '2rem' }}>
        {features.map((feature, index) => (
          <div key={index} style={{ 
            padding: '2rem', 
            borderRadius: '12px', 
            border: '1px solid var(--color-border)', 
            backgroundColor: 'white',
            boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.05)',
            transition: 'transform 0.2s ease, box-shadow 0.2s ease',
            cursor: 'pointer'
          }}
          className="hover:-translate-y-1 hover:shadow-lg"
          >
            <div style={{ fontSize: '2.5rem', marginBottom: '1.5rem', background: 'var(--color-bg-light)', display: 'inline-flex', padding: '1rem', borderRadius: '12px' }}>
              {feature.icon}
            </div>
            <h3 style={{ fontSize: '1.25rem', fontWeight: 700, marginBottom: '1rem', color: 'var(--color-text-main)' }}>{feature.title}</h3>
            <p style={{ color: 'var(--color-text-muted)', lineHeight: '1.6', marginBottom: '1.5rem' }}>{feature.description}</p>
            <a href="#" style={{ color: 'var(--color-brand-blue)', fontWeight: 600, textDecoration: 'none', display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
              Learn more <span style={{ fontSize: '1.2rem' }}>→</span>
            </a>
          </div>
        ))}
      </div>
    </section>
  );
}
