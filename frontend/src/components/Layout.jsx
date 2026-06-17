import { Outlet } from 'react-router-dom';
import Sidebar from './Sidebar';
import Toaster from './Toaster';

export default function Layout() {
  return (
    <div style={{ display: 'flex', minHeight: '100vh', backgroundColor: 'var(--bg-color)' }}>
      <Toaster />
      <Sidebar />
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
        {/* Topbar opcional */}
        <header style={{ 
          height: '60px', 
          borderBottom: '1px solid var(--border-color)',
          display: 'flex',
          alignItems: 'center',
          padding: '0 2rem',
          backgroundColor: 'var(--surface-color)'
        }}>
          <h2 style={{ fontSize: '1.2rem', fontWeight: '600' }}>Plataforma GRIN</h2>
        </header>
        
        <main style={{ flex: 1, padding: '2rem', overflowY: 'auto' }}>
          <Outlet />
        </main>
      </div>
    </div>
  );
}
