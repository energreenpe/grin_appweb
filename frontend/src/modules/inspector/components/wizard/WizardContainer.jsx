import React, { useState } from 'react';
import { useWizardStore } from '../../store/wizardStore';
import { inspectorApi } from '../../api/inspectorApi';
import { getNextStep, getStepLabel, getProgress } from '../../wizardSteps';

import StepInicioInspeccion from './StepInicioInspeccion';
import StepTipoSistema from './StepTipoSistema';
import StepConexionRed from './StepConexionRed';
import StepReciboLuz from './StepReciboLuz';
import StepCargasCriticas from './StepCargasCriticas';
import StepTipoTecho from './StepTipoTecho';
import StepCapturaFotos from './StepCapturaFotos';

export default function WizardContainer() {
  const { currentStep, stepHistory, goBack, data, goToStep } = useWizardStore();
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState(null);

  const handleNext = async (overrideData = null) => {
    const current = overrideData || data;
    const nextStep = getNextStep(currentStep, current);

    setSaveError(null);
    setSaving(true);
    try {
      // Crear visita en backend al avanzar desde inicio (tenemos cliente y técnico)
      if (currentStep === 'inicio' && !useWizardStore.getState().visitaId) {
        // Precreamos la visita con los datos mínimos para obtener el ID
        const res = await inspectorApi.createVisita({
          tipo_cliente: current.tipo_cliente,
          cliente_id: current.cliente_id,
          tecnico_id: current.tecnico_id,
          tipo_sistema: current.tipo_sistema || null,
          paso_actual: nextStep
        });
        useWizardStore.getState().setVisitaId(res.id);
      } else if (useWizardStore.getState().visitaId && currentStep !== 'done') {
        // Actualizamos los datos en BD para los demás pasos
        await inspectorApi.updateVisita(useWizardStore.getState().visitaId, {
          ...current,
          paso_actual: nextStep
        });
      }

      if (nextStep === 'done' && useWizardStore.getState().visitaId) {
        await inspectorApi.completarVisita(useWizardStore.getState().visitaId);
      }

      // Solo avanzamos si el guardado fue exitoso (evita pérdida silenciosa de datos)
      if (nextStep) {
        goToStep(nextStep);
      }
    } catch (error) {
      console.error("Error guardando progreso", error);
      setSaveError("No se pudo guardar el progreso. Revisa tu conexión e inténtalo de nuevo.");
    } finally {
      setSaving(false);
    }
  };

  const renderStep = () => {
    switch (currentStep) {
      case 'inicio':          return <StepInicioInspeccion onNext={handleNext} />;
      case 'tipo_sistema':    return <StepTipoSistema onNext={handleNext} />;
      case 'conexion_red':    return <StepConexionRed onNext={handleNext} />;
      case 'recibo_luz':      return <StepReciboLuz onNext={handleNext} />;
      case 'cargas_criticas': return <StepCargasCriticas onNext={handleNext} />;
      case 'tipo_techo':      return <StepTipoTecho onNext={handleNext} />;
      case 'fotos_techo':     return <StepCapturaFotos seccion="techo" onNext={handleNext} />;
      case 'fotos_interior':  return <StepCapturaFotos seccion="interior" onNext={handleNext} />;
      case 'done':
        return (
          <div style={{ textAlign: 'center', padding: '3rem' }}>
            <h2>✅ Visita Completada</h2>
            <p>El reporte PDF se está generando y guardando.</p>
          </div>
        );
      default:
        return <div>Paso desconocido</div>;
    }
  };

  return (
    <div style={{ maxWidth: '800px', margin: '0 auto', width: '100%' }}>
      {/* ProgressBar con etiqueta */}
      <div style={{ marginBottom: '1.5rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.4rem', fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
          <span style={{ fontWeight: 600, color: 'var(--primary-color, #62B989)' }}>{getStepLabel(currentStep)}</span>
          <span>{Math.round(getProgress(currentStep))}%</span>
        </div>
        <div style={{ background: 'var(--border-color)', height: '8px', borderRadius: '4px', overflow: 'hidden' }}>
          <div style={{ height: '100%', width: `${getProgress(currentStep)}%`, background: 'var(--primary-color, #62B989)', transition: 'width 0.35s ease' }} />
        </div>
      </div>

      <div className="glass-panel" style={{ padding: '2rem', position: 'relative' }}>
        {stepHistory.length > 0 && currentStep !== 'done' && (
          <button
            onClick={goBack}
            className="btn"
            style={{ position: 'absolute', top: '1rem', left: '1rem', background: 'transparent', color: 'var(--text-secondary)', padding: '0.5rem' }}
          >
            ← Volver
          </button>
        )}

        {saving && (
          <div style={{ position: 'absolute', top: '1rem', right: '1rem', fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
            Guardando…
          </div>
        )}

        <div style={{ marginTop: stepHistory.length > 0 ? '2rem' : '0' }}>
          {saveError && (
            <div style={{ background: 'rgba(220,50,50,0.12)', border: '1px solid rgba(220,50,50,0.4)', borderRadius: '8px', padding: '0.75rem 1rem', color: '#ff6b6b', fontSize: '0.9rem', marginBottom: '1rem' }}>
              ⚠️ {saveError}
            </div>
          )}
          {renderStep()}
        </div>
      </div>
    </div>
  );
}
