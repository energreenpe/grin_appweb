import { useState, useEffect } from 'react';

// Devuelve true cuando el ancho de la ventana es menor al breakpoint (móvil).
// Se actualiza al redimensionar. Pensado para alternar layouts inline sin CSS media queries.
export function useIsMobile(breakpoint = 768) {
  const [isMobile, setIsMobile] = useState(() => window.innerWidth < breakpoint);

  useEffect(() => {
    const onResize = () => setIsMobile(window.innerWidth < breakpoint);
    window.addEventListener('resize', onResize);
    return () => window.removeEventListener('resize', onResize);
  }, [breakpoint]);

  return isMobile;
}
