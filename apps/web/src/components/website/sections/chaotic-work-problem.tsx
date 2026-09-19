import React from "react";
import styles from "./chaotic-work-problem.module.css";
import { 
  AlertTriangle, 
  Calendar, 
  MessageSquare, 
  Video, 
  FolderGit2, 
  FileText 
} from "lucide-react";

export function ChaoticWorkProblemSection() {
  return (
    <section className={styles.section} id="problem">
      <div className={styles.header}>
        <div className={styles.eyebrow}>
          <AlertTriangle className="w-4 h-4" /> Fragmented Stack Problem
        </div>
        <h2 className={styles.title}>
          The Current Way Growth Teams Work Is Chaotic.
        </h2>
        <p className={styles.subtitle}>
          Switching between disconnected email relays, social schedulers, analytics tools, and AI copilots wastes time and causes critical campaign errors.
        </p>
      </div>

      <div className={styles.stage}>
        <svg className={styles.svgLines} viewBox="0 0 1100 440">
          <path d="M150,80 C350,180 500,100 950,90" className={styles.pathLine} />
          <path d="M100,320 C300,180 600,350 900,280" className={styles.pathLine} />
          <path d="M250,380 C500,220 750,400 850,150" className={styles.pathLine} />
        </svg>

        {/* Floating App Icons matching Image 4 */}
        <div className={styles.floatingIcon} style={{ top: "40px", left: "12%" }}>
          <Calendar className="w-8 h-8 text-rose-400" />
          <span className={styles.badgeAlert}>99+</span>
          <span className={styles.badgeTag}>Calendar</span>
        </div>

        <div className={styles.floatingIcon} style={{ top: "30px", right: "20%" }}>
          <MessageSquare className="w-8 h-8 text-emerald-400" />
          <span className={styles.badgeAlert}>1M+</span>
          <span className={styles.badgeTag}>Slack</span>
        </div>

        <div className={styles.floatingIcon} style={{ top: "60px", right: "8%" }}>
          <Video className="w-8 h-8 text-amber-400" />
          <span className={styles.badgeAlert}>Join</span>
          <span className={styles.badgeTag}>Meet</span>
        </div>

        <div className={styles.floatingIcon} style={{ bottom: "80px", left: "15%" }}>
          <FolderGit2 className="w-8 h-8 text-sky-400" />
          <span className={styles.badgeAlert}>Offline</span>
          <span className={styles.badgeTag}>Drive</span>
        </div>

        <div className={styles.floatingIcon} style={{ bottom: "50px", left: "48%" }}>
          <MessageSquare className="w-8 h-8 text-green-400" />
          <span className={styles.badgeAlert}>420</span>
          <span className={styles.badgeTag}>Messages</span>
        </div>

        <div className={styles.floatingIcon} style={{ bottom: "60px", right: "12%" }}>
          <FileText className="w-8 h-8 text-purple-400" />
          <span className={styles.badgeAlert}>100▲</span>
          <span className={styles.badgeTag}>Notion</span>
        </div>
      </div>

      {/* 3 Impact Stats matching Image 4 */}
      <div className={styles.statsRow}>
        <div className={styles.statCard}>
          <div className={styles.statNumber}>2x More Errors</div>
          <div className={styles.statText}>
            Occur when context-switching between disconnected marketing platforms and manual copy-pasting.
          </div>
        </div>

        <div className={styles.statCard}>
          <div className={styles.statNumber}>Constant Multitasking</div>
          <div className={styles.statText}>
            Leads to team burnout, missed approval deadlines, and inconsistent brand voice execution.
          </div>
        </div>

        <div className={styles.statCard}>
          <div className={styles.statNumber}>1.2 Months/Year Wasted</div>
          <div className={styles.statText}>
            Spent solely on channel switching, manual status reporting, and data re-entry.
          </div>
        </div>
      </div>
    </section>
  );
}
