"use client";

import React, { useEffect, useState } from 'react';
import Image from 'next/image';
import Link from 'next/link';
import styles from './home.module.css';

export function SocialPilotCloneHome() {
  const [isMounted, setIsMounted] = useState(false);
  useEffect(() => setIsMounted(true), []);

  return (
    <div className={styles.container}>
      {/* Soft Radial Glows - MotionGenie Style */}
      <div className={styles.glowTopLeft} aria-hidden="true" />
      <div className={styles.glowTopRight} aria-hidden="true" />

      <main className={styles.mainContent}>
        
        {/* =========================================
            1. MOTIONGENIE HERO SECTION
            ========================================= */}
        <section className={styles.heroSection}>
          <div className={styles.pillBadge}>
            🏆 #1 Product of the Day
          </div>
          
          <h1 className={styles.heroHeading}>
            AI-Powered Growth & <br />
            <span className={styles.gradientTextPrimary}>Marketing OS</span>
          </h1>
          
          <p className={styles.heroSub}>
            Unify Social, Email, CRM, Automation & AI Analytics. A production-ready Operating System for businesses and agencies.
          </p>
          
          <div className={styles.heroActions}>
            <Link href="/register" className={styles.btnPrimaryLg}>
              Start Free <span className={styles.btnIcon}>🚀</span>
            </Link>
            <Link href="/features" className={styles.btnOutlineLg}>
              Explore Features ✨
            </Link>
          </div>

          <div className={styles.heroShowcase}>
            <div className={styles.mockDashboardContainer}>
              <div className={styles.glassBrowserHeader}>
                <span className={styles.glassDotRed} />
                <span className={styles.glassDotYellow} />
                <span className={styles.glassDotGreen} />
                <div className={styles.browserUrl}>growixa.com/dashboard</div>
              </div>
              <div className={styles.mockDashboardBody}>
                {/* Fake Dashboard Layout */}
                <div className={styles.fakeSidebar}></div>
                <div className={styles.fakeMain}>
                  <div className={styles.fakeHeader}>Hello Sarah!</div>
                  <div className={styles.fakeGrid}>
                    <div className={styles.fakeCard}></div>
                    <div className={styles.fakeCard}></div>
                    <div className={styles.fakeCard}></div>
                  </div>
                </div>
              </div>
            </div>

            {/* Floating Glassmorphic Cards (MotionGenie Style) */}
            <div className={`${styles.glassWidget} ${styles.widgetVoice}`}>
              <div className={styles.widgetOrbVoice}></div>
              <h4>Unified CRM</h4>
              <p>Contacts, leads, companies, and powerful dynamic segments.</p>
            </div>

            <div className={`${styles.glassWidget} ${styles.widgetAgents}`}>
              <div className={styles.widgetHeader}>
                <h4>AI Intelligence</h4>
                <span className={styles.badgeTrend}>Core Engine</span>
              </div>
              <p>Content assistant, brand voice, and campaign optimization.</p>
            </div>

            <div className={`${styles.glassWidget} ${styles.widgetAutomation}`}>
              <h4>Marketing Automation</h4>
              <div className={styles.miniAutomationGraph}>
                <div className={styles.magCenter}>Λ</div>
                <div className={styles.magNode} style={{top: 0, left: '50%', transform: 'translateX(-50%)'}} />
                <div className={styles.magNode} style={{bottom: 0, left: '50%', transform: 'translateX(-50%)'}} />
                <div className={styles.magNode} style={{top: '50%', left: 0, transform: 'translateY(-50%)'}} />
                <div className={styles.magNode} style={{top: '50%', right: 0, transform: 'translateY(-50%)'}} />
              </div>
            </div>
          </div>
        </section>

        {/* =========================================
            2. VEKTA OS CIRCULAR NODE GRAPH
            ========================================= */}
        <section className={styles.vektaSection}>
          <div className={styles.vektaHeader}>
            <div className={styles.pillBadgeOutline}>Overview</div>
            <h2>Complete AI Platform to <br/><span className={styles.gradientTextSecondary}>Power Everything</span></h2>
            <p>Growixa brings all your creative, analytical, and automation tools together into a seamless workspace designed to boost productivity.</p>
          </div>

          <div className={styles.vektaCircleContainer}>
            {/* The Central Hub */}
            <div className={styles.vektaCenter}>
              <h3>Growixa OS</h3>
              <h4>Everything Connected. Work Simplified.</h4>
              <p>One system to manage, automate, and grow your business.</p>
            </div>

            {/* Circular Nodes */}
            <div className={`${styles.vektaNodeWrapper} ${styles.node1}`}>
              <div className={styles.vektaNode}>
                <div className={styles.vkIcon}>🧠</div>
                <div className={styles.vkText}>
                  <strong>AI Content</strong>
                  <span>Generation & Insights</span>
                </div>
              </div>
            </div>

            <div className={`${styles.vektaNodeWrapper} ${styles.node2}`}>
              <div className={styles.vektaNode}>
                <div className={styles.vkIcon}>💬</div>
                <div className={styles.vkText}>
                  <strong>Engagement</strong>
                  <span>Unified Inbox & Listening</span>
                </div>
              </div>
            </div>

            <div className={`${styles.vektaNodeWrapper} ${styles.node3}`}>
              <div className={styles.vektaNode}>
                <div className={styles.vkIcon}>🏢</div>
                <div className={styles.vkText}>
                  <strong>Agency Management</strong>
                  <span>Clients, Team & White Label</span>
                </div>
              </div>
            </div>

            <div className={`${styles.vektaNodeWrapper} ${styles.node4}`}>
              <div className={styles.vektaNode}>
                <div className={styles.vkIcon}>⚡</div>
                <div className={styles.vkText}>
                  <strong>Marketing Automation</strong>
                  <span>Email, SMS & Workflows</span>
                </div>
              </div>
            </div>

            <div className={`${styles.vektaNodeWrapper} ${styles.node5}`}>
              <div className={styles.vektaNode}>
                <div className={styles.vkIcon}>👥</div>
                <div className={styles.vkText}>
                  <strong>CRM & Leads</strong>
                  <span>Contacts, Tags & Segments</span>
                </div>
              </div>
            </div>

            <div className={`${styles.vektaNodeWrapper} ${styles.node6}`}>
              <div className={styles.vektaNode}>
                <div className={styles.vkIcon}>📊</div>
                <div className={styles.vkText}>
                  <strong>Analytics</strong>
                  <span>Social, Email & Reports</span>
                </div>
              </div>
            </div>

            <div className={`${styles.vektaNodeWrapper} ${styles.node7}`}>
              <div className={styles.vektaNode}>
                <div className={styles.vkIcon}>📱</div>
                <div className={styles.vkText}>
                  <strong>Social Media</strong>
                  <span>Composer, Calendar & Posts</span>
                </div>
              </div>
            </div>
            
            {/* SVG Connecting Rings */}
            <svg className={styles.vektaSvgRings} viewBox="0 0 1000 1000">
              <circle cx="500" cy="500" r="300" className={styles.vkRingInner} />
              <circle cx="500" cy="500" r="450" className={styles.vkRingOuter} />
            </svg>
          </div>
        </section>

        {/* =========================================
            3. VOLT STUDIOS WORKFLOW DIAGRAM
            ========================================= */}
        <section className={styles.voltSection}>
          <div className={styles.voltHeader}>
            <div className={styles.pillBadgePurple}>Growixa Core Loop</div>
            <h2>AUDIENCE ENGAGEMENT. <br/><span className={styles.gradientTextPurple}>SYSTEMS COMPOUND.</span></h2>
          </div>

          <div className={styles.voltDiagram}>
            <svg className={styles.voltSvgPaths} viewBox="0 0 800 500" preserveAspectRatio="none">
              {/* Connecting lines from Step 1 & 3 to Step 2 & 4 */}
              <path d="M 300 100 C 400 100, 400 250, 500 250" className={styles.voltPath} />
              <path d="M 300 400 C 400 400, 400 250, 500 250" className={styles.voltPath} />
              <path d="M 300 400 C 400 400, 400 400, 500 400" className={styles.voltPath} />
            </svg>

            <div className={styles.voltColLeft}>
              <div className={styles.voltCard}>
                <span className={styles.voltNum}>01</span>
                <h4>Build Audience</h4>
                <p>Import contacts, leads, companies, and capture new segments.</p>
              </div>
              <div className={styles.voltCard} style={{marginTop: '150px'}}>
                <span className={styles.voltNum}>03</span>
                <h4>Automate Campaigns</h4>
                <p>Schedule omni-channel delivery across Email, SMS & Social.</p>
              </div>
            </div>

            <div className={styles.voltColRight}>
              <div className={styles.voltCard} style={{marginTop: '120px'}}>
                <span className={styles.voltNum}>02</span>
                <h4>Create Content</h4>
                <p>Use Brand Voice AI to generate posts, captions, and templates.</p>
              </div>
              <div className={styles.voltCard} style={{marginTop: '80px'}}>
                <span className={styles.voltNum}>04</span>
                <h4>AI Insights & Grow</h4>
                <p>Analyze engagement, follow-up with CRM, and optimize.</p>
              </div>
            </div>
          </div>
          
          <div className={styles.voltAction}>
            <Link href="/register" className={styles.btnPurpleSolid}>Build Your System</Link>
          </div>
        </section>

        {/* =========================================
            4. ASLASE AI AUTOMATION CORE
            ========================================= */}
        <section className={styles.aslaseSection}>
          <div className={styles.aslaseHeader}>
            <div className={styles.aslaseLogo}>▲ GROWIXA</div>
            <h2>Automate More. <br/><span className={styles.gradientTextBlue}>Work Better.</span></h2>
            <p>Visual workflows triggered by your audience actions.</p>
          </div>

          <div className={styles.aslaseDiagram}>
            {/* Background Tech Lines */}
            <div className={styles.aslaseTechBg}></div>

            {/* Inputs (Left) */}
            <div className={styles.aslaseInputs}>
              <div className={styles.aslaseBox}>📱 Social Actions</div>
              <div className={styles.aslaseBox}>👥 CRM Events</div>
              <div className={styles.aslaseBox}>📧 Email Opens</div>
              <div className={styles.aslaseBox}>💬 WhatsApp/SMS</div>
            </div>

            {/* Core Brain */}
            <div className={styles.aslaseCoreWrapper}>
              <div className={styles.aslasePulse1}></div>
              <div className={styles.aslasePulse2}></div>
              <div className={styles.aslaseCore}>
                <span className={styles.aslaseBrainIcon}>AI</span>
              </div>
              {/* Flow Lines SVG (In and Out) */}
              <svg className={styles.aslaseSvgLines} viewBox="0 0 600 300">
                <path d="M 0 50 C 100 50, 100 150, 200 150" className={styles.aslaseLineIn} />
                <path d="M 0 110 C 100 110, 100 150, 200 150" className={styles.aslaseLineIn} />
                <path d="M 0 190 C 100 190, 100 150, 200 150" className={styles.aslaseLineIn} />
                <path d="M 0 250 C 100 250, 100 150, 200 150" className={styles.aslaseLineIn} />

                <path d="M 400 150 C 500 150, 500 30, 600 30" className={styles.aslaseLineOut} />
                <path d="M 400 150 C 500 150, 500 90, 600 90" className={styles.aslaseLineOut} />
                <path d="M 400 150 C 500 150, 500 150, 600 150" className={styles.aslaseLineOut} />
                <path d="M 400 150 C 500 150, 500 210, 600 210" className={styles.aslaseLineOut} />
                <path d="M 400 150 C 500 150, 500 270, 600 270" className={styles.aslaseLineOut} />
              </svg>
            </div>

            {/* Outputs (Right) */}
            <div className={styles.aslaseOutputs}>
              <div className={styles.aslaseStatusBox}><span className={styles.iconCheck}>✓</span> TRIGGER</div>
              <div className={styles.aslaseStatusBox}><span className={styles.iconCheck}>✓</span> CONDITION</div>
              <div className={styles.aslaseStatusBox}><span className={styles.iconCheck}>✓</span> ACTION</div>
              <div className={styles.aslaseStatusBox}><span className={styles.iconCheck}>✓</span> FOLLOW-UP</div>
              <div className={styles.aslaseStatusBox}><span className={styles.iconDoc}>📄</span> Execution Log</div>
            </div>
          </div>
        </section>

      </main>
    </div>
  );
}
