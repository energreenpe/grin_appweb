import React, { useEffect } from 'react';
import { useWizardStore } from '../../store/wizardStore';
import { inspectorApi } from '../../api/inspectorApi';

import StepInicioInspeccion from './StepInicioInspeccion';
import StepTipoSistema from './StepTipoSistema';
import StepConexionRed from './StepConexionRed';
import StepReciboLuz from './StepReciboLuz';
import StepCargasCriticas from './StepCargasCriticas';
import StepTipoTecho from './StepTipoTecho';
import StepCapturaFotos from './StepCapturaFotos';

export default function WizardContainer() {
  const { currentStep, stepHistory, goBack, data, goToStep } = useWizardStore();

  // Función para determinar el siguiente paso lógico de la state machine
  const getNextStep = (step, currentData) => {
    switch (step) {
      case 'inicio':        return 'tipo_sistema';
      case 'tipo_sistema':
        if (['SFV Autoconsumo', 'SFV Híbrido'].includes(currentData.tipo_sistema)) return 'conexion_red';
        if (currentData.tipo_sistema === 'SFV Aislado') return 'cargas_criticas';
        return 'tipo_techo'; // Terma Solar, BESS
      case 'conexion_red':
        if (currentData.conexion_red === 'Si') return 'recibo_luz';
        return currentData.tipo_sistema === 'SFV Híbrido' ? 'cargas_criticas' : 'tipo_techo';
      case 'recibo_luz':
        return currentData.tipo_sistema === 'SFV Híbrido' ? 'cargas_criticas' : 'tipo_techo';
      case 'cargas_criticas': return 'tipo_techo';
      case 'tipo_techo':      return 'fotos_techo';
      case 'fotos_techo':     return 'fotos_interior';
      case 'fotos_interior':  return 'done';
      default: return null;
    }
  };

  const handleNext = async (overrideData = null) => {
    const current = overrideData || data;
    const nextStep = getNextStep(currentStep, current);

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
    } catch (error) {
      console.error("Error guardando progreso", error);
    }

    if (nextStep) {
      goToStep(nextStep);
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

  // Porcentaje aproximado de avance
  const getProgress = () => {
    const stepOrder = ['inicio', 'tipo_sistema', 'conexion_red', 'recibo_luz', 'cargas_criticas', 'tipo_techo', 'fotos_techo', 'fotos_interior', 'done'];
    const idx = stepOrder.indexOf(currentStep);
    return Math.max(5, Math.min(100, (idx / (stepOrder.length - 1)) * 100));
  };

  // Etiqueta legible del paso actual
  const getStepLabel = () => {
    const labels = {
      inicio: 'Cliente y Técnico',
      tipo_sistema: 'Tipo de Sistema',
      conexion_red: 'Conexión a Red',
      recibo_luz: 'Recibo de Luz',
      cargas_criticas: 'Cargas Críticas',
      tipo_techo: 'Tipo de Techo',
      fotos_techo: 'Fotos del Techo',
      fotos_interior: 'Fotos del Interior',
      done: 'Completado',
    };
    return labels[currentStep] || currentStep;
  };

  return (
    <div style={{ maxWidth: '800px', margin: '0 auto', width: '100%' }}>
      {/* ProgressBar con etiqueta */}
      <div style={{ marginBottom: '1.5rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.4rem', fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
          <span style={{ fontWeight: 600, color: 'var(--primary-color, #62B989)' }}>{getStepLabel()}</span>
          <span>{Math.round(getProgress())}%</span>
        </div>
        <div style={{ background: 'var(--border-color)', height: '8px', borderRadius: '4px', overflow: 'hidden' }}>
          <div style={{ height: '100%', width: `${getProgress()}%`, background: 'var(--primary-color, #62B989)', transition: 'width 0.35s ease' }} />
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

        <div style={{ marginTop: stepHistory.length > 0 ? '2rem' : '0' }}>
          {renderStep()}
        </div>
      </div>
    </div>
  );
}
