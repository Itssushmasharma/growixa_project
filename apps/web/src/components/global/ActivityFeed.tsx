"use client";

import React, { useState, useEffect } from "react";
import styles from "./activity-feed.module.css";

type ActivityType = "EMAIL" | "SOCIAL" | "AI" | "CONTACT" | "SYSTEM";

interface ActivityEvent {
  id: string;
  type: ActivityType;
  title: string;
  description: string;
  time: string;
  status: "success" | "pending" | "info";
}

const MOCK_EVENTS: ActivityEvent[] = [
  { id: "1", type: "EMAIL", title: "Campaign Sent", description: "Welcome sequence delivered to 45 contacts", time: "Just now", status: "success" },
  { id: "2", type: "AI", title: "AI Content Drafted", description: "Generated subject lines for Black Friday", time: "5m ago", status: "info" },
  { id: "3", type: "SOCIAL", title: "Post Scheduled", description: "Instagram carousel scheduled for tomorrow", time: "12m ago", status: "pending" },
  { id: "4", type: "CONTACT", title: "New Segment Created", description: "'High Value Leads' segment synced", time: "1h ago", status: "success" },
];

export function ActivityFeed() {
  const [events, setEvents] = useState<ActivityEvent[]>(MOCK_EVENTS);
  const [isPaused, setIsPaused] = useState(false);

  // Simulate real-time incoming events
  useEffect(() => {
    if (isPaused) return;

    const interval = setInterval(() => {
      const newEvent: ActivityEvent = {
        id: Math.random().toString(36).substring(7),
        type: "SYSTEM",
        title: "Sync Completed",
        description: "Background audience sync finished.",
        time: "Just now",
        status: "info"
      };

      setEvents((prev) => {
        const updated = [newEvent, ...prev].slice(0, 10); // Keep last 10
        return updated;
      });
    }, 15000); // Add a fake event every 15 seconds

    return () => clearInterval(interval);
  }, [isPaused]);

  const getIcon = (type: ActivityType) => {
    switch (type) {
      case "EMAIL": return "📧";
      case "SOCIAL": return "📱";
      case "AI": return "✨";
      case "CONTACT": return "👥";
      default: return "⚡";
    }
  };

  return (
    <div className={styles.feedContainer}>
      <div className={styles.header}>
        <h3 className={styles.title}>Live Activity</h3>
        <button 
          onClick={() => setIsPaused(!isPaused)} 
          className={styles.pauseBtn}
          title={isPaused ? "Resume feed" : "Pause feed"}
        >
          <span className={isPaused ? styles.dotPaused : styles.dotActive}></span>
          {isPaused ? "Paused" : "Live"}
        </button>
      </div>

      <div className={styles.eventList}>
        {events.map((event, index) => (
          <div 
            key={event.id} 
            className={styles.eventItem}
            style={{ animationDelay: `${index * 0.1}s` }}
          >
            <div className={styles.iconBox}>{getIcon(event.type)}</div>
            <div className={styles.eventContent}>
              <div className={styles.eventTop}>
                <span className={styles.eventTitle}>{event.title}</span>
                <span className={styles.eventTime}>{event.time}</span>
              </div>
              <p className={styles.eventDesc}>{event.description}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
