import styles from "./tag.module.css";

export interface TagProps {
  status: "live" | "beta" | "soon" | string;
  label: string;
}

export default function Tag({ status, label }: TagProps) {
  const statusCls = styles[status as keyof typeof styles] || styles.soon;
  return <span className={`${styles.tag} ${statusCls}`}>{label}</span>;
}
