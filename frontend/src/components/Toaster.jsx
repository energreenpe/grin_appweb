import { useNotify } from '../lib/notify';

const COLORS = {
  error:   { bg: 'rgba(248,113,113,0.15)', border: '#f87171', fg: '#fca5a5', icon: '⚠' },
  success: { bg: 'rgba(74,222,128,0.15)',  border: '#4ade80', fg: '#86efac', icon: '✓' },
  info:    { bg: 'rgba(59,130,246,0.15)',  border: '#60a5fa', fg: '#93c5fd', icon: 'ℹ' },
};

export default function Toaster() {
  const { toasts, dismiss } = useNotify();
  if (toasts.length === 0) return null;

  return (
    <div style={{
      position: 'fixed', top: '1rem', right: '1rem', zIndex: 99999,
      display: 'flex', flexDirection: 'column', gap: '0.5rem', maxWidth: '360px',
    }}>
      {toasts.map(t => {
        const c = COLORS[t.type] || COLORS.info;
        return (
          <div
            key={t.id}
            role="alert"
            onClick={() => dismiss(t.id)}
            style={{
              background: c.bg, border: `1px solid ${c.border}`, color: c.fg,
              padding: '0.75rem 1rem', borderRadius: '8px', fontSize: '0.85rem',
              cursor: 'pointer', boxShadow: '0 6px 18px rgba(0,0,0,0.35)',
              display: 'flex', gap: '0.5rem', alignItems: 'flex-start',
            }}
          >
            <span aria-hidden>{c.icon}</span>
            <span style={{ flex: 1 }}>{t.message}</span>
            <span style={{ opacity: 0.6 }}>✕</span>
          </div>
        );
      })}
    </div>
  );
}
