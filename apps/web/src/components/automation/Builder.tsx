"use client";
import React, { useState } from 'react';
import { apiFetch } from "@/lib/api-client";
import { useToast } from "@/components/toast/toast-context";
import { Plus, X, Zap, Mail, Tag, MessageCircle, Clock, Save, Globe } from "lucide-react";
import styles from "./builder.module.css";

type ActionType = "send_email" | "add_tag" | "send_whatsapp" | "delay" | "webhook";

interface ActionNode {
  id: string;
  type: ActionType;
  config: Record<string, string>;
}

export function AutomationBuilder() {
  const { showToast } = useToast();
  const [trigger, setTrigger] = useState("contact.created");
  const [actions, setActions] = useState<ActionNode[]>([{ id: "1", type: "add_tag", config: { tag: "" } }]);
  const [saving, setSaving] = useState(false);
  const [isModalOpen, setIsModalOpen] = useState(false);

  async function handleSave() {
    setSaving(true);
    try {
      await apiFetch("/automations", {
        method: "POST",
        body: JSON.stringify({
          name: "New Automation Workflow",
          trigger_type: trigger,
          conditions: [],
          actions: actions.map(a => ({ type: a.type, config: a.config }))
        })
      });
      showToast("success", "Workflow saved successfully!");
    } catch {
      showToast("error", "Failed to save workflow.");
    } finally {
      setSaving(false);
    }
  }

  const handleAddAction = (type: ActionType) => {
    setActions([...actions, { id: Date.now().toString(), type, config: {} }]);
    setIsModalOpen(false);
  };

  const handleDeleteAction = (id: string) => {
    setActions(actions.filter(a => a.id !== id));
  };

  const updateActionConfig = (id: string, key: string, value: string) => {
    setActions(actions.map(a => a.id === id ? { ...a, config: { ...a.config, [key]: value } } : a));
  };

  const getActionIcon = (type: ActionType) => {
    switch(type) {
      case "send_email": return <Mail className="w-5 h-5" />;
      case "add_tag": return <Tag className="w-5 h-5" />;
      case "send_whatsapp": return <MessageCircle className="w-5 h-5" />;
      case "delay": return <Clock className="w-5 h-5" />;
      case "webhook": return <Globe className="w-5 h-5" />;
    }
  };

  const getActionTitle = (type: ActionType) => {
    switch(type) {
      case "send_email": return "Send Email";
      case "add_tag": return "Add Tag";
      case "send_whatsapp": return "WhatsApp Message";
      case "delay": return "Wait Delay";
      case "webhook": return "Trigger Webhook";
    }
  };

  return (
    <div className={styles.canvas}>
      <div className={styles.glow} />
      
      {/* Header */}
      <div className={styles.header}>
        <div>
          <h1>Automation Workflow</h1>
          <p>Design multi-channel sequences with visual nodes.</p>
        </div>
        <button onClick={handleSave} disabled={saving} className={styles.btnSave}>
          {saving ? "Saving..." : <span className="flex items-center gap-2"><Save className="w-4 h-4" /> Save Workflow</span>}
        </button>
      </div>

      <div className={styles.treeContainer}>
        
        {/* Trigger Node */}
        <div className={styles.nodeCard}>
          <div className={styles.nodeHeader}>
            <div className={`${styles.iconWrapper} ${styles.triggerIcon}`}>
              <Zap className="w-5 h-5" />
            </div>
            <span className={styles.nodeTitle}>Workflow Trigger</span>
          </div>
          <div>
            <label className={styles.label}>When this happens:</label>
            <select 
              value={trigger} 
              onChange={e => setTrigger(e.target.value)}
              className={styles.select}
            >
              <option value="contact.created">New Contact Added</option>
              <option value="segment.entered">Contact Enters Segment</option>
              <option value="email.opened">Email Opened</option>
            </select>
          </div>
        </div>

        {/* Action Nodes */}
        {actions.map((action) => (
          <React.Fragment key={action.id}>
            <div className={styles.connector} />
            <div className={styles.nodeCard}>
              <button 
                onClick={() => handleDeleteAction(action.id)} 
                className={styles.deleteBtn}
                title="Remove Action"
              >
                <X className="w-3.5 h-3.5" />
              </button>

              <div className={styles.nodeHeader}>
                <div className={`${styles.iconWrapper} ${styles.actionIcon}`}>
                  {getActionIcon(action.type)}
                </div>
                <span className={styles.nodeTitle}>{getActionTitle(action.type)}</span>
              </div>
              
              <div>
                {action.type === 'add_tag' && (
                  <>
                    <label className={styles.label}>Tag Name</label>
                    <input 
                      type="text" 
                      value={action.config.tag || ""}
                      onChange={(e) => updateActionConfig(action.id, "tag", e.target.value)}
                      className={styles.input} 
                      placeholder="e.g. vip-lead" 
                    />
                  </>
                )}
                {action.type === 'send_email' && (
                  <>
                    <label className={styles.label}>Email Template</label>
                    <select 
                      className={styles.select}
                      value={action.config.template || ""}
                      onChange={(e) => updateActionConfig(action.id, "template", e.target.value)}
                    >
                      <option value="">Select a template...</option>
                      <option value="welcome">Welcome Series - Email 1</option>
                      <option value="promo">Monthly Promo</option>
                    </select>
                  </>
                )}
                {action.type === 'send_whatsapp' && (
                  <>
                    <label className={styles.label}>Message Template</label>
                    <select 
                      className={styles.select}
                      value={action.config.wa_template || ""}
                      onChange={(e) => updateActionConfig(action.id, "wa_template", e.target.value)}
                    >
                      <option value="">Select a template...</option>
                      <option value="opt_in">Opt-in Confirmation</option>
                    </select>
                  </>
                )}
                {action.type === 'delay' && (
                  <>
                    <label className={styles.label}>Wait Time (Hours)</label>
                    <input 
                      type="number" 
                      value={action.config.hours || ""}
                      onChange={(e) => updateActionConfig(action.id, "hours", e.target.value)}
                      className={styles.input} 
                      placeholder="24" 
                    />
                  </>
                )}
                {action.type === 'webhook' && (
                  <>
                    <label className={styles.label}>Endpoint URL</label>
                    <input 
                      type="url" 
                      value={action.config.url || ""}
                      onChange={(e) => updateActionConfig(action.id, "url", e.target.value)}
                      className={styles.input} 
                      placeholder="https://api.example.com/hook" 
                    />
                  </>
                )}
              </div>
            </div>
          </React.Fragment>
        ))}

        {/* Add Node Button */}
        <div className={styles.connector} />
        <button 
          onClick={() => setIsModalOpen(true)}
          className={styles.btnAdd}
          title="Add Node"
        >
          <Plus className="w-6 h-6" />
        </button>
      </div>

      {/* Add Action Modal */}
      {isModalOpen && (
        <div className={styles.modalOverlay}>
          <div className={styles.modalContent}>
            <div className={styles.modalHeader}>
              <h3>Add Action</h3>
              <button onClick={() => setIsModalOpen(false)} className={styles.modalClose}>
                <X className="w-5 h-5" />
              </button>
            </div>
            <div className={styles.actionGrid}>
              <div className={styles.actionOption} onClick={() => handleAddAction("send_email")}>
                <div className={`${styles.actionOptionIcon} ${styles.actionIcon}`}><Mail className="w-4 h-4" /></div>
                <div className={styles.actionOptionText}>Send Email</div>
              </div>
              <div className={styles.actionOption} onClick={() => handleAddAction("send_whatsapp")}>
                <div className={`${styles.actionOptionIcon} ${styles.actionIcon}`}><MessageCircle className="w-4 h-4" /></div>
                <div className={styles.actionOptionText}>Send WhatsApp</div>
              </div>
              <div className={styles.actionOption} onClick={() => handleAddAction("add_tag")}>
                <div className={`${styles.actionOptionIcon} ${styles.conditionIcon}`}><Tag className="w-4 h-4" /></div>
                <div className={styles.actionOptionText}>Add Tag</div>
              </div>
              <div className={styles.actionOption} onClick={() => handleAddAction("delay")}>
                <div className={`${styles.actionOptionIcon} ${styles.conditionIcon}`}><Clock className="w-4 h-4" /></div>
                <div className={styles.actionOptionText}>Wait Delay</div>
              </div>
              <div className={styles.actionOption} onClick={() => handleAddAction("webhook")}>
                <div className={`${styles.actionOptionIcon} ${styles.triggerIcon}`}><Globe className="w-4 h-4" /></div>
                <div className={styles.actionOptionText}>Webhook</div>
              </div>
            </div>
          </div>
        </div>
      )}

    </div>
  );
}
