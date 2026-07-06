import React, { useState } from 'react';
import { useCalculoStore } from '../../store/calculoStore';
import { mathApi } from '../../api/mathApi';
import { getNextStep, getStepLabel, getProgress } from '../../wizardSteps';

import StepInicioCalculo from './StepInicioCalculo';
import StepTipoSistema from './StepTipoSistema';
import StepCargasAislado from './aislado/StepCargasAislado';
import StepSeleccionAislado from './aislado/StepSeleccionAislado';
import ResultadoAislado from './aislado/ResultadoAislado';
import StepSeleccionAutoconsumo from './autoconsumo/StepSeleccionAutoconsumo';
import ResultadoAutoconsumo from './autoconsumo/ResultadoAutoconsumo';

// Arma la `entrada` (JSON) del cálculo aislado desde el estado del store.
function buildEntradaAislado(data) {
  return {
    cargas: data.cargas,
    dias_autonomia: data.dias_autonomia,
    tipo_hsp: data.tipo_hsp,
    tipo_bateria: data.tipo_bateria,
    panel_id: data.panel_id,
    bateria_id: data.bateria_id,
    ...(data.voltaje_sistema ? { voltaje_sistema: data.voltaje_sistema } : {}),
  };
}

// Arma la `entrada` (JSON) del cálculo de autoconsumo.
function buildEntradaAuto(data) {
  return {
    panel_id: data.panel_id,
    inversor_id: data.inversor_id,
    consumo_mensual: Number(data.consumo_mensual) || 0,
    potencia_contratada: Number(data.potencia_contratada) || 0,
    autarquia: Number(data.autarquia) || 0,
    tipo_conexion: data.tipo_conexion,
    voltaje_red: data.voltaje_red,
    ...(data.opcion_elegida ? { opcion_elegida: data.opcion_elegida } : {}),
  };
}

export default function WizardContainer() {
  const { currentStep, stepHistory, goBack, data, goToStep, readOnly } = useCalculoStore();
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState(null);

  const handleNext = async (override = null) => {
    if (readOnly) return;   // en modo lectura no se guarda ni recalcula
    const current = override || data;
    const nextStep = getNextStep(currentStep, current);
    if (!nextStep) return;

    setSaveError(null);
    setSaving(true);
    try {
      const store = useCalculoStore.getState();
      let cid = store.calculoId;

      if (currentStep === 'inicio' && !cid) {
        const res = await mathApi.createCalculo({
          nombre_proyecto: current.nombre_proyecto,
          cliente_id: current.cliente_id,
          tipo_cliente: current.tipo_cliente,
          ingeniero_id: current.ingeniero_id,
          region: current.region,
          tipo_sistema: current.tipo_sistema || null,
          paso_actual: nextStep,
        });
        store.setCalculoId(res.id);
        cid = res.id;
      } else if (cid) {
        const payload = { paso_actual: nextStep };
        if (currentStep === 'tipo_sistema') payload.tipo_sistema = current.tipo_sistema;
        if (currentStep === 'cargas' || currentStep === 'seleccion') payload.entrada = buildEntradaAislado(current);
        if (currentStep === 'seleccion_auto' || currentStep === 'resultado_auto') payload.entrada = buildEntradaAuto(current);
        await mathApi.updateCalculo(cid, payload);
      }

      // Al pasar de una selección a su resultado: ejecutar el motor y persistir.
      if ((currentStep === 'seleccion' || currentStep === 'seleccion_auto') && cid) {
        const calc = await mathApi.calcularCalculo(cid);
        store.setData({ resultado: calc.resultado });
      }

      // Al completar.
      if (nextStep === 'done' && cid) {
        await mathApi.completarCalculo(cid);
      }

      goToStep(nextStep);
    } catch (error) {
      console.error('Error guardando progreso', error);
      setSaveError(
        error?.response?.data?.detail ||
        'No se pudo guardar el progreso. Revisa tu conexión e inténtalo de nuevo.'
      );
    } finally {
      setSaving(false);
    }
  };

  const renderStep = () => {
    switch (currentStep) {
      case 'inicio':       return <StepInicioCalculo onNext={handleNext} />;
      case 'tipo_sistema': return <StepTipoSistema onNext={handleNext} />;
      case 'cargas':          return <StepCargasAislado onNext={handleNext} />;
      case 'seleccion':       return <StepSeleccionAislado onNext={handleNext} />;
      case 'resultado':       return <ResultadoAislado onNext={handleNext} readOnly={readOnly} />;
      case 'seleccion_auto':  return <StepSeleccionAutoconsumo onNext={handleNext} />;
      case 'resultado_auto':  return <ResultadoAutoconsumo onNext={handleNext} readOnly={readOnly} />;
      case 'done':
        return (
          <div style={{ textAlign: 'center', padding: '3rem' }}>
            <h2>✅ Cálculo Completado</h2>
            <p style={{ color: 'var(--text-secondary)' }}>El cálculo se guardó correctamente.</p>
          </div>
        );
      default:
        return <div>Paso desconocido</div>;
    }
  };

  return (
    <div style={{ maxWidth: '900px', margin: '0 auto', width: '100%' }}>
      <div style={{ marginBottom: '1.5rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.4rem', fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
          <span style={{ fontWeight: 600, color: 'var(--primary-color)' }}>{getStepLabel(currentStep)}</span>
          <span>{Math.round(getProgress(currentStep))}%</span>
        </div>
        <div style={{ background: 'var(--border-color)', height: '8px', borderRadius: '4px', overflow: 'hidden' }}>
          <div style={{ height: '100%', width: `${getProgress(currentStep)}%`, background: 'var(--primary-color)', transition: 'width 0.35s ease' }} />
        </div>
      </div>

      <div className="glass-panel" style={{ padding: '2rem', position: 'relative' }}>
        {stepHistory.length > 0 && currentStep !== 'done' && (
          <button onClick={goBack} className="btn"
            style={{ position: 'absolute', top: '1rem', left: '1rem', background: 'transparent', color: 'var(--text-secondary)', padding: '0.5rem' }}>
            ← Volver
          </button>
        )}
        {!readOnly && saving && (
          <div style={{ position: 'absolute', top: '1rem', right: '1rem', fontSize: '0.8rem', color: 'var(--text-secondary)' }}>Guardando…</div>
        )}
        {readOnly && (() => {
          const next = getNextStep(currentStep, data);
          const canForward = next && next !== 'done';
          return (
            <button onClick={() => canForward && goToStep(next)} disabled={!canForward} className="btn"
              style={{ position: 'absolute', top: '1rem', right: '1rem', background: 'transparent', padding: '0.5rem',
                color: canForward ? 'var(--text-secondary)' : 'var(--border-color)', cursor: canForward ? 'pointer' : 'default' }}>
              Siguiente →
            </button>
          );
        })()}

        <div style={{ marginTop: (stepHistory.length > 0 || readOnly) ? '2rem' : '0' }}>
          {readOnly && (
            <div style={{ background: 'rgba(98,185,137,0.1)', border: '1px solid rgba(98,185,137,0.3)', borderRadius: '8px', padding: '0.6rem 1rem', color: 'var(--primary-color)', fontSize: '0.85rem', marginBottom: '1rem', textAlign: 'center' }}>
              🔒 Cálculo completado — modo lectura (recorre los pasos con Volver / Siguiente)
            </div>
          )}
          {saveError && (
            <div style={{ background: 'rgba(220,50,50,0.12)', border: '1px solid rgba(220,50,50,0.4)', borderRadius: '8px', padding: '0.75rem 1rem', color: '#ff6b6b', fontSize: '0.9rem', marginBottom: '1rem' }}>
              ⚠️ {saveError}
            </div>
          )}
          <fieldset disabled={readOnly}
            style={{ border: 'none', padding: 0, margin: 0, minInlineSize: 'auto', ...(readOnly ? { pointerEvents: 'none' } : {}) }}>
            {renderStep()}
          </fieldset>
        </div>
      </div>
    </div>
  );
}
