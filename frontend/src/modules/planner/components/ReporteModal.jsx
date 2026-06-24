import { useState } from 'react';
import { descargarPdf } from '../api/plannerApi';

const lunesDeEstaSemana = () => {
  const d = new Date();
  const day = d.getDay();
  const diff = d.getDate() - day + (day === 0 ? -6 : 1);
  return new Date(d.setDate(diff)).toISOString().split('T')[0];
};
const viernesDeEstaSemana = () => {
  const lunes = new Date(lunesDeEstaSemana());
  lunes.setDate(lunes.getDate() + 4);
  return lunes.toISOString().split('T')[0];
};

export default function ReporteModal({ proyectoId, proyectoNombre, onClose }) {
  const [tipo, setTipo] = useState('semanal');
  const [semanaNum, setSemanaNum] = useState(1);
  const [fechaDesde, setFechaDesde] = useState(lunesDeEstaSemana());
  const [fechaHasta, setFechaHasta] = useState(viernesDeEstaSemana());
  const [observaciones, setObservaciones] = useState('');
  const [generando, setGenerando] = useState(null); // 'cliente' | 'oficina' | null

  const generar = async (tipoPdf) => {
    setGenerando(tipoPdf);
    try {
      const params = {
        tipo, semana_num: semanaNum, observaciones,
        ...(tipo === 'rango' ? { fecha_desde: fechaDesde, fecha_hasta: fechaHasta } : {}),
      };
      const blob = await descargarPdf(proyectoId, tipoPdf, params);
      const link = document.createElement('a');
      link.href = URL.createObjectURL(blob);
      link.download = `Reporte_${tipoPdf === 'cliente' ? 'Cliente' : 'Oficina'}_${proyectoNombre}_S${semanaNum}.pdf`;
      link.click();
      URL.revokeObjectURL(link.href);
    } catch {
      window.alert('Error al generar el PDF.');
    } finally {
      setGenerando(null);
    }
  };

  return (
    <div className="pl-modal-overlay" onClick={onClose}>
      <div className="pl-modal" onClick={(e) => e.stopPropagation()}>
        <div className="pl-modal-head">
          <div>
            <h2 className="pl-h2">📄 Generar Reporte PDF</h2>
            <p className="pl-subtitle">{proyectoNombre}</p>
          </div>
          <button className="pl-x" onClick={onClose}>✕</button>
        </div>

        <div className="pl-modal-body">
          <div>
            <label className="pl-label">Tipo de período</label>
            <div className="pl-row" style={{ flexWrap: 'nowrap' }}>
              {[['semanal', '📅 Semanal'], ['rango', '📆 Rango de fechas']].map(([v, l]) => (
                <button key={v} onClick={() => setTipo(v)}
                  className={`pl-btn ${tipo === v ? 'pl-btn-primary' : 'pl-btn-outline'}`} style={{ flex: 1 }}>
                  {l}
                </button>
              ))}
            </div>
          </div>

          {tipo === 'semanal' ? (
            <div>
              <label className="pl-label">Número de semana</label>
              <input className="pl-input" type="number" min="1" max="52" value={semanaNum}
                onChange={(e) => setSemanaNum(Number(e.target.value))} />
            </div>
          ) : (
            <div className="pl-grid pl-grid-2">
              <div>
                <label className="pl-label">Desde</label>
                <input className="pl-input" type="date" value={fechaDesde} onChange={(e) => setFechaDesde(e.target.value)} />
              </div>
              <div>
                <label className="pl-label">Hasta</label>
                <input className="pl-input" type="date" value={fechaHasta} onChange={(e) => setFechaHasta(e.target.value)} />
              </div>
            </div>
          )}

          <div>
            <label className="pl-label">Observaciones / Comentarios del período</label>
            <textarea className="pl-textarea" rows={3} value={observaciones}
              onChange={(e) => setObservaciones(e.target.value)}
              placeholder="Ingresa observaciones, comentarios o solicitudes del período..." />
          </div>

          <div className="pl-grid pl-grid-2">
            <div className="pl-card pl-card-pad" style={{ borderColor: 'rgba(98,185,137,.4)' }}>
              <p style={{ fontWeight: 600, color: 'var(--primary-color)', fontSize: '.85rem', marginBottom: '.4rem' }}>📋 PDF Cliente</p>
              <ul className="pl-muted" style={{ fontSize: '.73rem', paddingLeft: '1rem', margin: 0, lineHeight: 1.6 }}>
                <li>Portada profesional</li>
                <li>Datos del proyecto</li>
                <li>Cronograma Gantt</li>
                <li>Curva S</li>
                <li>Fotos seleccionadas</li>
              </ul>
            </div>
            <div className="pl-card pl-card-pad" style={{ borderColor: 'rgba(122,183,255,.4)' }}>
              <p style={{ fontWeight: 600, color: '#7ab7ff', fontSize: '.85rem', marginBottom: '.4rem' }}>🏢 PDF Oficina</p>
              <ul className="pl-muted" style={{ fontSize: '.73rem', paddingLeft: '1rem', margin: 0, lineHeight: 1.6 }}>
                <li>Todo lo del cliente +</li>
                <li>Cuadrillas detalladas</li>
                <li>Asistencia completa</li>
                <li>Valorizaciones</li>
                <li>Todas las fotos</li>
              </ul>
            </div>
          </div>

          <div className="pl-grid pl-grid-2">
            <button className="pl-btn pl-btn-primary" onClick={() => generar('cliente')} disabled={!!generando}>
              {generando === 'cliente' ? '⏳ Generando...' : '📋 Descargar Cliente'}
            </button>
            <button className="pl-btn pl-btn-blue" onClick={() => generar('oficina')} disabled={!!generando}>
              {generando === 'oficina' ? '⏳ Generando...' : '🏢 Descargar Oficina'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
