import { useNavigate } from 'react-router-dom';

export default function Dashboard() {
  const navigate = useNavigate();

  const modules = [
    { id: 'math', name: 'MATH', icon: '📐', active: false },
    { id: 'inspector', name: 'INSPECTOR', icon: '📋', active: true, path: '/inspector' },
    { id: 'quote', name: 'QUOTE', icon: '💰', active: true, path: '/quote' },
  ];

  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      background: 'linear-gradient(135deg, var(--bg-color) 0%, #1a2a22 100%)',
      position: 'relative'
    }}>
      <div className="glass-panel animate-fade-in" style={{
        padding: '3rem',
        width: '90%',
        maxWidth: '800px',
        textAlign: 'center',
        boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.5)'
      }}>
        <div style={{
          width: '80px', height: '80px', borderRadius: '50%',
          backgroundColor: 'var(--primary-color)', margin: '0 auto 1.5rem',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontSize: '2.5rem', fontWeight: 'bold', color: '#000',
          boxShadow: '0 0 20px rgba(98, 185, 137, 0.4)'
        }}>
          G
        </div>
        
        <h1 style={{ fontSize: '2.5rem', marginBottom: '0.5rem' }}>GRIN APP</h1>
        <p style={{ color: 'var(--text-secondary)', marginBottom: '3rem' }}>
          Plataforma Modular Incremental
        </p>

        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
          gap: '1.5rem'
        }}>
          {modules.map(mod => (
            <button
              key={mod.id}
              onClick={() => mod.active && navigate(mod.path)}
              disabled={!mod.active}
              style={{
                background: mod.active ? 'var(--primary-color)' : 'rgba(255,255,255,0.05)',
                color: mod.active ? '#000' : 'var(--text-secondary)',
                border: 'none',
                borderRadius: '16px',
                padding: '2rem 1rem',
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                gap: '1rem',
                cursor: mod.active ? 'pointer' : 'not-allowed',
                transition: 'transform 0.2s, box-shadow 0.2s',
                opacity: mod.active ? 1 : 0.6,
              }}
              onMouseOver={e => {
                if (mod.active) {
                  e.currentTarget.style.transform = 'translateY(-5px)';
                  e.currentTarget.style.boxShadow = '0 10px 20px rgba(98, 185, 137, 0.3)';
                }
              }}
              onMouseOut={e => {
                if (mod.active) {
                  e.currentTarget.style.transform = 'none';
                  e.currentTarget.style.boxShadow = 'none';
                }
              }}
            >
              <span style={{ fontSize: '3rem' }}>{mod.icon}</span>
              <span style={{ fontSize: '1.2rem', fontWeight: 'bold' }}>{mod.name}</span>
              {!mod.active && (
                <span style={{ fontSize: '0.75rem', padding: '2px 8px', background: 'rgba(0,0,0,0.5)', borderRadius: '10px' }}>
                  Próximamente
                </span>
              )}
            </button>
          ))}
        </div>
      </div>

      <div style={{
        position: 'absolute',
        bottom: '20px',
        color: 'var(--text-secondary)',
        fontSize: '0.8rem',
        fontStyle: 'italic'
      }}>
        Designed by EnergiAI
      </div>
    </div>
  );
}
