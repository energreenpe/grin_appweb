import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { inspectorApi } from '../api/inspectorApi';
import { useWizardStore } from '../store/wizardStore';
import { buildHistory } from '../wizardSteps';
import { notify } from '../../../lib/notify';

export default function VisitaCard({ visita }) {
  const { id, cliente, tipo_sistema, tipo_cliente, fecha, estado } = visita;
  const dateObj = new Date(fecha);
  const navigate = useNavigate();
  const { setVisitaId, setData, resumeAt } = useWizardStore();
  const [loadingResume, setLoadingResume] = useState(false);

  const handleDownloadPDF = async () => {
    try {
      await inspectorApi.downloadPdf(id, `Visita_${id}_${cliente.nombre.replace(/ /g, '_')}.pdf`);
    } catch (err) {
      console.error("Error descargando PDF", err);
      notify("No se pudo descargar el PDF. Revisa tu conexión.");
    }
  };

  const handleResume = async () => {
    try {
      setLoadingResume(true);
      const fullVisita = await inspectorApi.getVisita(id);

      // Rehidratar el store mapeando el shape de la API (cliente/tecnico) al del
      // store (cliente_info/tecnico_info), que es lo que consume la UI del wizard.
      const mapped = {
        ...fullVisita,
        cliente_info: fullVisita.cliente || null,
        tecnico_info: fullVisita.tecnico || null,
      };
      setVisitaId(fullVisita.id);
      setData(mapped);
      const target = fullVisita.paso_actual || 'inicio';
      resumeAt(target, buildHistory(target, mapped));
      
      navigate('/inspector/new');
    } catch (err) {
      console.error("Error reanudando visita", err);
      notify("No se pudo reanudar la inspección. Revisa tu conexión.");
    } finally {
      setLoadingResume(false);
    }
  };

  return (
    <div className="glass-panel hover-bg" style={{ padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1rem', transition: 'transform 0.2s' }}>
      
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '0.25rem' }}>
            {dateObj.toLocaleDateString()} {dateObj.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
          </div>
          <h3 style={{ margin: '0 0 0.5rem 0', fontSize: '1.1rem' }}>{cliente.nombre}</h3>
          <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
            <span style={{ fontSize: '0.75rem', padding: '2px 8px', borderRadius: '12px', background: 'rgba(255,255,255,0.1)' }}>
              {tipo_cliente}
            </span>
            <span style={{ fontSize: '0.75rem', padding: '2px 8px', borderRadius: '12px', background: 'rgba(98, 185, 137, 0.2)', color: 'var(--primary-color)' }}>
              {tipo_sistema}
            </span>
            <span style={{ fontSize: '0.75rem', padding: '2px 8px', borderRadius: '12px', background: estado === 'completada' ? 'rgba(98, 185, 137, 0.1)' : 'rgba(255, 193, 7, 0.1)' }}>
              {estado === 'borrador' ? '🔄 Borrador' : '✅ Completada'}
            </span>
          </div>
        </div>
        
        <div>
          {estado === 'borrador' ? (
            <button 
              className="btn btn-primary" 
              style={{ padding: '0.5rem 1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}
              onClick={handleResume}
              disabled={loadingResume}
            >
              {loadingResume ? 'Cargando...' : '▶ Continuar'}
            </button>
          ) : (
            <button 
              className="btn btn-secondary" 
              style={{ padding: '0.5rem 1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}
              onClick={handleDownloadPDF}
              title="Descargar Reporte PDF"
            >
              <span>📄</span> PDF
            </button>
          )}
        </div>
      </div>

      <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
        <div>📍 {cliente.direccion || 'Sin dirección registrada'}</div>
        <div>📞 {cliente.telefono || 'Sin teléfono'}</div>
      </div>
      
    </div>
  );
}
