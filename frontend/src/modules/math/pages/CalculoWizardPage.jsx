import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import WizardContainer from '../components/wizard/WizardContainer';
import { useCalculoStore, VALID_STEPS } from '../store/calculoStore';
import { mathApi } from '../api/mathApi';

export default function CalculoWizardPage() {
  const { currentStep, reset, calculoId, data, readOnly } = useCalculoStore();
  const navigate = useNavigate();
  const [exiting, setExiting] = useState(false);

  const handleGuardarSalir = async () => {
    if (calculoId && currentStep !== 'done') {
      try {
        setExiting(true);
        await mathApi.updateCalculo(calculoId, { paso_actual: currentStep });
      } catch (e) {
        console.error('Error guardando antes de salir', e);
        if (!window.confirm('No se pudo guardar el progreso. ¿Salir de todas formas?')) {
          setExiting(false);
          return;
        }
      }
    }
    reset();
    navigate('/math');
  };

  const handleDescartar = async () => {
    if (!window.confirm('¿Descartar este cálculo? Se eliminará permanentemente.')) return;
    if (calculoId) {
      try {
        await mathApi.deleteCalculo(calculoId);
      } catch (e) {
        console.error('Error al descartar cálculo', e);
      }
    }
    reset();
    navigate('/math');
  };

  // Limpia estado inválido del localStorage (ej. paso antiguo).
  useEffect(() => {
    if (!VALID_STEPS.includes(currentStep)) {
      reset();
    }
  }, [currentStep, reset]);

  // Al completar, volver a la lista tras 5s.
  useEffect(() => {
    if (currentStep === 'done') {
      const t = setTimeout(() => { reset(); navigate('/math'); }, 5000);
      return () => clearTimeout(t);
    }
  }, [currentStep, reset, navigate]);

  return (
    <div className="animate-fade-in" style={{ padding: '1rem' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
        <h1 style={{ margin: 0, fontSize: '1.8rem' }}>{readOnly ? 'Ver Cálculo' : 'Nuevo Cálculo'}</h1>
        <div style={{ display: 'flex', gap: '0.75rem' }}>
          {readOnly ? (
            <button className="btn btn-secondary" onClick={() => { reset(); navigate('/math'); }}>
              ← Volver a la lista
            </button>
          ) : (
            <>
              <button className="btn btn-secondary" onClick={handleGuardarSalir} disabled={exiting}
                title="Guarda el progreso y vuelve a la lista; podrás continuar después">
                {exiting ? 'Guardando…' : '💾 Guardar y salir'}
              </button>
              <button className="btn" onClick={handleDescartar} disabled={exiting}
                style={{ background: 'transparent', color: '#ff6b6b', border: '1px solid rgba(220,50,50,0.4)' }}
                title="Elimina permanentemente este cálculo">
                🗑️ Descartar
              </button>
            </>
          )}
        </div>
      </div>

      <WizardContainer />
    </div>
  );
}
