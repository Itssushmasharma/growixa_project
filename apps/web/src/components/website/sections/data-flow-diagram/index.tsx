import React from "react";
import styles from "./data-flow.module.css";

export function DataFlowDiagram() {
  return (
    <section className={styles.section}>
      <h2 className={styles.title}>How Growixa Works</h2>
      <p className={styles.subtitle}>
        Connect your data, let our AI engine analyze it, and automatically execute marketing campaigns across every channel.
      </p>

      <div className={styles.diagramContainer}>
        {/* Background Animated SVG Lines */}
        <svg className={styles.svgBackground} preserveAspectRatio="none" viewBox="0 0 1100 600">
          <defs>
            <linearGradient id="gradientLeft" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#00b887" />
              <stop offset="100%" stopColor="#00a9e0" />
            </linearGradient>
            <linearGradient id="gradientRight" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#00a9e0" />
              <stop offset="100%" stopColor="#7b4dff" />
            </linearGradient>
          </defs>

          {/* Left Lines (Data -> Hub) */}
          <path d="M260,100 C400,100 450,300 550,300" className={styles.pathLine} />
          <path d="M260,100 C400,100 450,300 550,300" className={styles.pathLineAnim} />

          <path d="M260,200 C400,200 450,300 550,300" className={styles.pathLine} />
          <path d="M260,200 C400,200 450,300 550,300" className={styles.pathLineAnim} style={{ animationDelay: '-5s' }} />

          <path d="M260,400 C400,400 450,300 550,300" className={styles.pathLine} />
          <path d="M260,400 C400,400 450,300 550,300" className={styles.pathLineAnim} style={{ animationDelay: '-10s' }} />

          <path d="M260,500 C400,500 450,300 550,300" className={styles.pathLine} />
          <path d="M260,500 C400,500 450,300 550,300" className={styles.pathLineAnim} style={{ animationDelay: '-15s' }} />

          {/* Right Lines (Hub -> Execution) */}
          <path d="M550,300 C650,300 700,100 840,100" className={styles.pathLineRight} />
          <path d="M550,300 C650,300 700,100 840,100" className={styles.pathLineAnimRight} />

          <path d="M550,300 C650,300 700,200 840,200" className={styles.pathLineRight} />
          <path d="M550,300 C650,300 700,200 840,200" className={styles.pathLineAnimRight} style={{ animationDelay: '-5s' }} />

          <path d="M550,300 C650,300 700,400 840,400" className={styles.pathLineRight} />
          <path d="M550,300 C650,300 700,400 840,400" className={styles.pathLineAnimRight} style={{ animationDelay: '-10s' }} />

          <path d="M550,300 C650,300 700,500 840,500" className={styles.pathLineRight} />
          <path d="M550,300 C650,300 700,500 840,500" className={styles.pathLineAnimRight} style={{ animationDelay: '-15s' }} />
        </svg>

        {/* Left Column: DATA */}
        <div className={styles.column}>
          <div className={`${styles.colHeader} ${styles.headerLeft}`}>DATA</div>
          
          <div className={styles.card}>
            <div className={styles.cardIcon} style={{ background: 'rgba(0,184,135,0.1)', color: '#00b887' }}>🌐</div>
            <span className={styles.cardLabel}>Web behavior</span>
          </div>
          
          <div className={styles.card}>
            <div className={styles.cardIcon} style={{ background: 'rgba(0,184,135,0.1)', color: '#00b887' }}>💻</div>
            <span className={styles.cardLabel}>Online sales</span>
          </div>
          
          <div className={styles.card}>
            <div className={styles.cardIcon} style={{ background: 'rgba(0,184,135,0.1)', color: '#00b887' }}>📦</div>
            <span className={styles.cardLabel}>Product Data</span>
          </div>
          
          <div className={styles.card}>
            <div className={styles.cardIcon} style={{ background: 'rgba(0,184,135,0.1)', color: '#00b887' }}>@</div>
            <span className={styles.cardLabel}>Contact</span>
          </div>

          <div className={styles.card}>
            <div className={styles.cardIcon} style={{ background: 'rgba(0,184,135,0.1)', color: '#00b887' }}>🔌</div>
            <span className={styles.cardLabel}>Custom APIs</span>
          </div>
        </div>

        {/* Center Hub: KNOWLEDGE */}
        <div className={styles.centerHubWrapper}>
          <div className={styles.colHeader} style={{ position: 'absolute', top: -30, width: '100%' }}>KNOWLEDGE</div>
          <div className={styles.centerGlow} />
          
          <div className={styles.knowledgePoints}>
            <div className={`${styles.kPoint} ${styles.tl}`}>Engagement scoring</div>
            <div className={`${styles.kPoint} ${styles.tr}`}>Lifecycle stage</div>
            <div className={`${styles.kPoint} ${styles.bl}`}>Predicted Spend</div>
            <div className={`${styles.kPoint} ${styles.br}`}>Loyalty status</div>
          </div>

          <div className={styles.centerHub}>
            <div className={styles.hubLogo}>Grow<span>ixa</span></div>
            <div className={styles.hubSubtitle}>AI Marketing Engine</div>
          </div>
        </div>

        {/* Right Column: EXECUTION */}
        <div className={styles.column}>
          <div className={`${styles.colHeader} ${styles.headerRight}`}>EXECUTION</div>
          
          <div className={styles.card}>
            <div className={styles.cardIcon} style={{ background: 'rgba(123,77,255,0.1)', color: '#7b4dff' }}>📱</div>
            <span className={styles.cardLabel}>SMS & WhatsApp</span>
          </div>
          
          <div className={styles.card}>
            <div className={styles.cardIcon} style={{ background: 'rgba(123,77,255,0.1)', color: '#7b4dff' }}>✉️</div>
            <span className={styles.cardLabel}>Direct Email</span>
          </div>
          
          <div className={styles.card}>
            <div className={styles.cardIcon} style={{ background: 'rgba(123,77,255,0.1)', color: '#7b4dff' }}>💬</div>
            <span className={styles.cardLabel}>Social Posts</span>
          </div>
          
          <div className={styles.card}>
            <div className={styles.cardIcon} style={{ background: 'rgba(123,77,255,0.1)', color: '#7b4dff' }}>🎯</div>
            <span className={styles.cardLabel}>Digital Ads</span>
          </div>

          <div className={styles.card}>
            <div className={styles.cardIcon} style={{ background: 'rgba(123,77,255,0.1)', color: '#7b4dff' }}>🔔</div>
            <span className={styles.cardLabel}>Mobile Push</span>
          </div>
        </div>

      </div>
    </section>
  );
}
