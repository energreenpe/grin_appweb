import { Outlet } from 'react-router-dom';
import { useState, useEffect } from 'react';
import Sidebar from './Sidebar';
import Toaster from './Toaster';

const MOBILE_BREAKPOINT = 768;

export default function Layout() {
  const [isMobile, setIsMobile] = useState(() => window.innerWidth < MOBILE_BREAKPOINT);
  // Visible por defecto en escritorio; oculto en celular.
  const [open, setOpen] = useState(() => window.innerWidth >= MOBILE_BREAKPOINT);

  // Solo reacciona al CRUZAR el breakpoint (no pisa el colapso manual del usuario
  // mientras redimensiona dentro del mismo rango).
  useEffect(() => {
    let prevMobile = window.innerWidth < MOBILE_BREAKPOINT;
    const onResize = () => {
      const mobile = window.innerWidth < MOBILE_BREAKPOINT;
      if (mobile !== prevMobile) {
        prevMobile = mobile;
        setIsMobile(mobile);
        setOpen(!mobile);
      }
    };
    window.addEventListener('resize', onResize);
    return () => window.removeEventListener('resize', onResize);
  }, []);

  // En celular, al navegar a un módulo se cierra el sidebar (overlay).
  const handleNavigate = () => { if (isMobile) setOpen(false); };

  return (
    <div style={{ display: 'flex', minHeight: '100vh', backgroundColor: 'var(--bg-color)' }}>
      <Toaster />

      {open && (
        <>
          {/* Fondo oscuro detrás del sidebar (solo en celular) */}
          {isMobile && (
            <div
              onClick={() => setOpen(false)}
              style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.5)', zIndex: 90 }}
            />
          )}
          {/* En celular el sidebar va superpuesto; en escritorio empuja el contenido */}
          <div style={isMobile ? { position: 'fixed', top: 0, left: 0, bottom: 0, zIndex: 100 } : undefined}>
            <Sidebar onNavigate={handleNavigate} showClose={isMobile} onClose={() => setOpen(false)} />
          </div>
        </>
      )}

      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', minWidth: 0 }}>
        <header style={{
          height: '60px',
          borderBottom: '1px solid var(--border-color)',
          display: 'flex',
          alignItems: 'center',
          gap: '1rem',
          padding: '0 1.5rem',
          backgroundColor: 'var(--surface-color)',
        }}>
          <button
            onClick={() => setOpen(o => !o)}
            aria-label={open ? 'Ocultar menú' : 'Mostrar menú'}
            title={open ? 'Ocultar menú' : 'Mostrar menú'}
            style={{
              background: 'none', border: '1px solid var(--border-color)',
              color: 'var(--text-primary)', borderRadius: 'var(--radius)',
              width: '38px', height: '38px', cursor: 'pointer', fontSize: '1.1rem',
              display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0,
            }}
          >
            ☰
          </button>
          <h2 style={{ fontSize: '1.2rem', fontWeight: '600', margin: 0 }}>Plataforma GRIN</h2>
        </header>

        <main style={{ flex: 1, padding: '2rem', overflowY: 'auto' }}>
          <Outlet />
        </main>
      </div>
    </div>
  );
}
