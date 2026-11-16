/**
 * The owner-approved notice (14.11.2026) shown instead of a result when typed text reads as
 * self-harm. The text comes from the server as approved; nothing is added here.
 */
export function CrisisNotice({ text, className = "" }: { text: string; className?: string }) {
  return (
    <p className={`crisis-notice${className ? ` ${className}` : ""}`} role="alert">{text}</p>
  );
}
