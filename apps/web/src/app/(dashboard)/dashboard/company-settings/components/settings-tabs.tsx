"use client";

import styles from "./components.module.css";

export interface SettingsTab {
  id: string;
  label: string;
}

interface SettingsTabsProps {
  tabs: SettingsTab[];
  activeTab: string;
  onChange: (tabId: string) => void;
}

/** Client-side tab switcher — never triggers a route change or reload. */
export function SettingsTabs({ tabs, activeTab, onChange }: SettingsTabsProps) {
  return (
    <div className={styles.tabs} role="tablist" aria-label="Company & brand settings sections">
      {tabs.map((tab) => (
        <button
          key={tab.id}
          type="button"
          role="tab"
          id={`tab-${tab.id}`}
          aria-selected={activeTab === tab.id}
          aria-controls={`tabpanel-${tab.id}`}
          className={`${styles.tab} ${activeTab === tab.id ? styles.tabActive : ""}`}
          onClick={() => onChange(tab.id)}
        >
          {tab.label}
        </button>
      ))}
    </div>
  );
}
