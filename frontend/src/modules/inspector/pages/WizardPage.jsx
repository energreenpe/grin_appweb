import React, { useEffect, useState } from 'react';
import WizardContainer from '../components/wizard/WizardContainer';
import { useWizardStore, VALID_STEPS } from '../store/wizardStore';
import { useNavigate } from 'react-router-dom';
import { inspectorApi } from '../api/inspectorApi';

export default function WizardPage() {
  const { currentStep, reset, visitaId, data } = useWizardStore();
  const navigate = useNavigate();
  const [exiting, setExiting] = useState(false);

  // ── Guardar el progreso actual y salir conservando el borrador ──
  const handleGuardarSalir = async () => {
    if (visitaId && currentStep !== 'done') {
      try {
        setExiting(true);
        await inspectorApi.updateVisita(visitaId, { ...data, paso_actual: currentStep });
      } catch (e) {
        console.error('Error guardando antes de salir', e);
        if (!window.confirm('No se pudo guardar el progreso. ¿Salir de todas formas? (la inspección quedará como estaba)')) {
          setExiting(false);
          return;
        }
      }
    }
    reset();
    navigate('/inspector');
  };

  // ── Descartar: borra el registro y sus archivos del servidor (acción explícita) ──
  const handleDescartar = async () => {
    if (!window.confirm('¿Descartar esta inspección? Se eliminará permanentemente junto con sus fotos.')) return;
    if (visitaId) {
      try {
        await inspectorApi.cancelarVisita(visitaId);
      } catch (e) {
        console.error('Error al descartar visita', e);
      }
    }
    reset();
    navigate('/inspector');
  };

  // ── Limpiar estado inválido del localStorage (ej: paso antiguo 'tipo_cliente') ──
  useEffect(() => {
    if (!VALID_STEPS.includes(currentStep)) {
      console.warn(`[Inspector] Paso inválido detectado: "${currentStep}". Reseteando wizard.`);
      reset();
    }
  }, [currentStep, reset]);

  // ── Al completar, redirigir a la lista tras 5 segundos ──
  useEffect(() => {
    if (currentStep === 'done') {
      const timer = setTimeout(() => {
        reset();
        navigate('/inspector');
      }, 5000);
      return () => clearTimeout(timer);
    }
  }, [currentStep, reset, navigate]);

  return (
    <div className="animate-fade-in" style={{ padding: '1rem' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
        <h1 style={{ margin: 0, fontSize: '1.8rem' }}>Nueva Inspección Técnica</h1>
        <div style={{ display: 'flex', gap: '0.75rem' }}>
          <button
            className="btn btn-secondary"
            onClick={handleGuardarSalir}
            disabled={exiting}
            title="Guarda el progreso y vuelve a la lista; podrás continuar después"
          >
            {exiting ? 'Guardando…' : '💾 Guardar y salir'}
          </button>
          <button
            className="btn"
            onClick={handleDescartar}
            disabled={exiting}
            style={{ background: 'transparent', color: '#ff6b6b', border: '1px solid rgba(220,50,50,0.4)' }}
            title="Elimina permanentemente esta inspección y sus fotos"
          >
            🗑️ Descartar
          </button>
        </div>
      </div>

      <WizardContainer />
    </div>
  );
}
