import { NavLink } from 'react-router-dom';

export default function Sidebar({ onNavigate, showClose = false, onClose }) {
  const navStyle = ({ isActive }) => ({
    display: 'flex',
    alignItems: 'center',
    padding: '0.75rem 1rem',
    color: isActive ? 'var(--primary-color)' : 'var(--text-secondary)',
    backgroundColor: isActive ? 'rgba(98, 185, 137, 0.1)' : 'transparent',
    borderRadius: 'var(--radius)',
    textDecoration: 'none',
    fontWeight: '500',
    marginBottom: '0.5rem',
    transition: 'all 0.2s',
  });

  return (
    <aside style={{
      width: '250px',
      height: '100%',
      minHeight: '100vh',
      boxSizing: 'border-box',
      backgroundColor: 'var(--surface-color)',
      borderRight: '1px solid var(--border-color)',
      display: 'flex',
      flexDirection: 'column',
      padding: '1.5rem',
      overflowY: 'auto',
    }}>
      <div style={{ marginBottom: '2rem', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div style={{
            width: '32px', height: '32px', borderRadius: '50%',
            backgroundColor: 'var(--primary-color)', display: 'flex',
            alignItems: 'center', justifyContent: 'center', color: '#000', fontWeight: 'bold'
          }}>G</div>
          <h1 style={{ fontSize: '1.5rem', margin: 0, color: 'var(--text-primary)' }}>GRIN</h1>
        </div>
        {showClose && (
          <button
            onClick={onClose}
            aria-label="Cerrar menú"
            style={{
              background: 'none', border: 'none', color: 'var(--text-secondary)',
              fontSize: '1.4rem', cursor: 'pointer', lineHeight: 1,
            }}
          >
            ✕
          </button>
        )}
      </div>

      <nav style={{ flex: 1 }}>
        <NavLink to="/" style={navStyle} onClick={onNavigate}>
          🏠 Inicio
        </NavLink>
        <div style={{ margin: '1.5rem 0 0.5rem 0', fontSize: '0.8rem', color: 'var(--text-secondary)', textTransform: 'uppercase' }}>
          Módulos
        </div>
        <NavLink to="/quote" style={navStyle} onClick={onNavigate}>
          💰 Cotizaciones (QUOTE)
        </NavLink>
        <NavLink to="/products" style={navStyle} onClick={onNavigate}>
          📦 Productos
        </NavLink>
        <NavLink to="/math" style={navStyle} onClick={onNavigate}>
          📐 Calculos Solares (MATH)
        </NavLink>
        <NavLink to="/inspector" style={navStyle} onClick={onNavigate}>
          📋 Inspecciónes (INSPECTOR)
        </NavLink>
        <NavLink to="/list" style={navStyle} onClick={onNavigate}>
          📝 Editor de Documentos (LIST)
        </NavLink>
        <NavLink to="/planner" style={navStyle} onClick={onNavigate}>
          ☀️ Proyectos (PLANNER)
        </NavLink>
      </nav>
    </aside>
  );
}
