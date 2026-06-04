import React, { useEffect } from 'react';
import WizardContainer from '../components/wizard/WizardContainer';
import { useWizardStore, VALID_STEPS } from '../store/wizardStore';
import { useNavigate } from 'react-router-dom';
import { inspectorApi } from '../api/inspectorApi';

export default function WizardPage() {
  const { currentStep, reset, visitaId } = useWizardStore();
  const navigate = useNavigate();

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
        <button
          className="btn btn-secondary"
          onClick={async () => {
            if (confirm('¿Seguro que deseas salir? Los datos no guardados se perderán y la inspección será cancelada.')) {
              if (visitaId) {
                try {
                  await inspectorApi.cancelarVisita(visitaId);
                } catch (e) {
                  console.error("Error al cancelar visita", e);
                }
              }
              reset();
              navigate('/inspector');
            }
          }}
        >
          ✖ Cancelar / Salir
        </button>
      </div>

      <WizardContainer />
    </div>
  );
}
