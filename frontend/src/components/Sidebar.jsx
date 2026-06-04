import { NavLink } from 'react-router-dom';

export default function Sidebar() {
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
      backgroundColor: 'var(--surface-color)',
      borderRight: '1px solid var(--border-color)',
      display: 'flex',
      flexDirection: 'column',
      padding: '1.5rem',
    }}>
      <div style={{ marginBottom: '2rem', display: 'flex', alignItems: 'center', gap: '10px' }}>
        <div style={{
          width: '32px', height: '32px', borderRadius: '50%',
          backgroundColor: 'var(--primary-color)', display: 'flex',
          alignItems: 'center', justifyContent: 'center', color: '#000', fontWeight: 'bold'
        }}>G</div>
        <h1 style={{ fontSize: '1.5rem', margin: 0, color: 'var(--text-primary)' }}>GRIN</h1>
      </div>

      <nav style={{ flex: 1 }}>
        <NavLink to="/" style={navStyle}>
          🏠 Inicio
        </NavLink>
        <div style={{ margin: '1.5rem 0 0.5rem 0', fontSize: '0.8rem', color: 'var(--text-secondary)', textTransform: 'uppercase' }}>
          Módulos
        </div>
        <NavLink to="/quote" style={navStyle}>
          💰 Cotizador (QUOTE)
        </NavLink>
        <NavLink to="/products" style={navStyle}>
          📦 Productos
        </NavLink>
        <div style={{...navStyle({isActive: false}), opacity: 0.5, cursor: 'not-allowed'}}>
          📐 Matemático (MATH)
        </div>
        <NavLink to="/inspector" style={navStyle}>
          📋 Inspección (INSPECTOR)
        </NavLink>
      </nav>
    </aside>
  );
}
