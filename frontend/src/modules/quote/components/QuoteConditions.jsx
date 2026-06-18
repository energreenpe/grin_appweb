import { useState, useEffect, useRef } from 'react';
import { useQuoteStore } from '../store/quoteStore';
import { quoteApi } from '../api/quoteApi';
import { fileUrl } from '../../../lib/api';
import { notify } from '../../../lib/notify';
import { ChevronDown, ChevronUp, Save, Download, Plus, Trash2, Bold, Palette, Upload, X } from 'lucide-react';

// ─── Toggle Switch ────────────────────────────────────────────────────────────
const ToggleSwitch = ({ checked, onChange }) => (
  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }} onClick={(e) => e.stopPropagation()}>
    <span style={{ fontSize: '0.75rem', color: checked ? '#4ade80' : 'var(--text-secondary)', whiteSpace: 'nowrap' }}>
      {checked ? 'En PDF' : 'Oculto'}
    </span>
    <div onClick={() => onChange(!checked)} style={{
      width: '40px', height: '22px', borderRadius: '11px', cursor: 'pointer',
      background: checked ? '#4ade80' : 'rgba(255,255,255,0.15)',
      position: 'relative', transition: 'background 0.25s', flexShrink: 0,
    }}>
      <div style={{
        position: 'absolute', top: '3px', left: checked ? '21px' : '3px',
        width: '16px', height: '16px', borderRadius: '50%',
        background: 'white', transition: 'left 0.25s', boxShadow: '0 1px 3px rgba(0,0,0,0.4)',
      }} />
    </div>
  </div>
);

// ─── Rich Text Editor ─────────────────────────────────────────────────────────
const RichTextEditor = ({ value, onChange, placeholder, minHeight = '40px' }) => {
  const editorRef = useRef(null);
  const [isFocused, setIsFocused] = useState(false);

  useEffect(() => {
    if (editorRef.current && editorRef.current.innerHTML !== value && !isFocused) {
      editorRef.current.innerHTML = value || '';
    }
  }, [value, isFocused]);

  const handleInput = () => { if (editorRef.current) onChange(editorRef.current.innerHTML); };
  const execCmd = (cmd, arg = null) => { document.execCommand(cmd, false, arg); editorRef.current?.focus(); handleInput(); };

  const handlePaste = (e) => {
    e.preventDefault();
    const text = e.clipboardData.getData('text/plain');
    document.execCommand('insertText', false, text);
  };

  return (
    <div style={{ border: '1px solid var(--border-color)', borderRadius: '6px', overflow: 'hidden', flex: 1 }}>
      <div style={{ padding: '5px', borderBottom: '1px solid var(--border-color)', display: 'flex', gap: '5px', background: 'rgba(255,255,255,0.05)' }}>
        <button type="button" onClick={() => execCmd('bold')} className="btn" style={{ padding: '4px 8px', background: 'none' }} title="Negrita"><Bold size={14} /></button>
        <div style={{ position: 'relative', display: 'flex', alignItems: 'center', width: '30px', height: '24px', cursor: 'pointer' }}>
          <Palette size={14} style={{ position: 'absolute', left: '8px', pointerEvents: 'none', color: 'var(--text-secondary)' }} />
          <input type="color" onChange={(e) => execCmd('foreColor', e.target.value)} style={{ width: '100%', height: '100%', opacity: 0, cursor: 'pointer' }} />
        </div>
      </div>
      <div ref={editorRef} contentEditable onInput={handleInput} onPaste={handlePaste}
        onFocus={() => setIsFocused(true)} onBlur={() => { setIsFocused(false); handleInput(); }}
        style={{ minHeight, padding: '10px', outline: 'none', fontSize: '0.9rem', whiteSpace: 'pre-wrap' }} data-placeholder={placeholder} />
    </div>
  );
};

// ─── Bank Card (editable: nombre, logo y campos dinámicos) ────────────────────
const BankCard = ({ cuenta, onChange, onRemove }) => {
  const fileInputRef = useRef(null);
  const [uploading, setUploading] = useState(false);
  const { beginLogoUpload, endLogoUpload } = useQuoteStore();
  const isVisible = cuenta.visible !== false;
  const logo = fileUrl(cuenta.logo);
  const campos = cuenta.campos || [];

  // Envía solo el PATCH; el padre lo aplica al banco por su id sobre el estado más
  // reciente (evita pisar otros bancos cuando una subida async termina tarde).
  const setField = (patch) => onChange(patch);
  const setCampo = (i, key, val) =>
    setField({ campos: campos.map((c, idx) => (idx === i ? { ...c, [key]: val } : c)) });
  const addCampo = () => setField({ campos: [...campos, { label: '', valor: '' }] });
  const removeCampo = (i) => setField({ campos: campos.filter((_, idx) => idx !== i) });

  const handleLogo = async (e) => {
    const f = e.target.files?.[0];
    e.target.value = '';                // permite volver a elegir el mismo archivo
    if (!f || uploading) return;        // ignora clics mientras ya está subiendo
    setUploading(true);
    beginLogoUpload();
    try {
      const { url } = await quoteApi.uploadBankLogo(f);
      setField({ logo: url });
    } catch (err) {
      notify(err?.response?.data?.detail || 'Error al subir el logo del banco.');
    } finally {
      setUploading(false);
      endLogoUpload();
    }
  };

  const openPicker = () => { if (!uploading) fileInputRef.current?.click(); };

  const inputBox = {
    background: 'rgba(255,255,255,0.07)', border: '1px solid var(--border-color)',
    borderRadius: '5px', padding: '5px 8px', color: 'inherit', fontSize: '0.85rem',
  };

  return (
    <div style={{
      background: 'rgba(255,255,255,0.04)', border: '1px solid var(--border-color)',
      borderRadius: '8px', padding: '1rem', flex: '1 1 320px', minWidth: '290px',
      opacity: isVisible ? 1 : 0.5, transition: 'opacity 0.2s'
    }}>
      {/* Cabecera: logo + nombre + toggle + eliminar */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.75rem', paddingBottom: '0.75rem', borderBottom: '1px solid var(--border-color)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flex: 1, minWidth: 0 }}>
          <input ref={fileInputRef} type="file" accept="image/png,image/jpeg,image/webp" style={{ display: 'none' }} onChange={handleLogo} disabled={uploading} />
          {uploading ? (
            <div style={{ height: '34px', width: '90px', flexShrink: 0, border: '1px dashed var(--border-color)', borderRadius: '6px', color: 'var(--text-secondary)', fontSize: '0.62rem', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: '2px', cursor: 'wait' }}>
              ⏳ Cargando…
            </div>
          ) : logo ? (
            <img src={logo} alt={cuenta.banco || 'logo'} onClick={openPicker}
              title="Cambiar logo" style={{ height: '34px', maxWidth: '90px', objectFit: 'contain', cursor: 'pointer', flexShrink: 0 }} />
          ) : (
            <button type="button" onClick={openPicker} title="Insertar logo"
              style={{ height: '34px', width: '90px', flexShrink: 0, border: '1px dashed var(--border-color)', borderRadius: '6px', background: 'none', color: 'var(--text-secondary)', fontSize: '0.62rem', cursor: 'pointer', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: '2px' }}>
              <Upload size={12} /> Insertar logo
            </button>
          )}
          <input type="text" value={cuenta.banco || ''} onChange={(e) => setField({ banco: e.target.value })}
            placeholder="Nombre del banco" style={{ ...inputBox, flex: 1, minWidth: 0, fontWeight: 'bold', fontSize: '0.9rem' }} />
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginLeft: '10px', flexShrink: 0 }}>
          <ToggleSwitch checked={isVisible} onChange={(v) => setField({ visible: v })} />
          <button type="button" onClick={onRemove} className="btn" style={{ padding: '4px', background: 'none', color: '#ff4d4f' }} title="Eliminar banco"><Trash2 size={16} /></button>
        </div>
      </div>

      {/* Campos dinámicos (label editable + valor) */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
        {campos.map((campo, i) => (
          <div key={i} style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <input type="text" value={campo.label || ''} onChange={(e) => setCampo(i, 'label', e.target.value)}
              placeholder="Etiqueta (ej. Soles S/)" style={{ ...inputBox, width: '42%', color: 'var(--text-secondary)', fontSize: '0.8rem' }} />
            <input type="text" value={campo.valor || ''} onChange={(e) => setCampo(i, 'valor', e.target.value)}
              placeholder="N° de cuenta" style={{ ...inputBox, flex: 1, minWidth: 0 }} />
            <button type="button" onClick={() => removeCampo(i)} className="btn" style={{ padding: '4px', background: 'none', color: 'var(--text-secondary)' }} title="Quitar campo"><X size={14} /></button>
          </div>
        ))}
        <button type="button" onClick={addCampo} className="btn btn-secondary" style={{ alignSelf: 'flex-start', padding: '4px 10px', fontSize: '0.78rem', display: 'flex', gap: '5px', alignItems: 'center' }}>
          <Plus size={13} /> Agregar campo
        </button>
      </div>
    </div>
  );
};

// ─── Main Component ───────────────────────────────────────────────────────────
export default function QuoteConditions({ cotizacionId, readOnly = false }) {
  const { cotizacion, updateHeader, logoUploads } = useQuoteStore();
  const [openSection, setOpenSection] = useState('tecnicas');
  const [plantillas, setPlantillas] = useState(null);
  const [loadingTemplate, setLoadingTemplate] = useState(false);

  useEffect(() => {
    quoteApi.getPlantillas().then(setPlantillas).catch(console.error);
  }, []);

  const toggleSection = (id) => setOpenSection(openSection === id ? null : id);
  const handleUpdate = async (field, value) => {
    if (readOnly) return;   // cotización aprobada/rechazada: solo lectura
    await updateHeader(cotizacionId, { [field]: value });
  };
  const handleToggleVisibility = async (field) => { await handleUpdate(field, !cotizacion[field]); };

  const loadTemplate = async (field) => {
    if (!plantillas) return;
    if (window.confirm('¿Reemplazar las condiciones actuales con la plantilla global?')) {
      await handleUpdate(field, plantillas[field]);
    }
  };

  const saveTemplate = async (field) => {
    if (window.confirm('¿Guardar estas condiciones como la nueva plantilla global?')) {
      setLoadingTemplate(true);
      try {
        const updated = await quoteApi.updatePlantillas({ [field]: cotizacion[field] });
        setPlantillas(updated);
        notify('Plantilla global actualizada.', 'success');
      } catch { notify('No se pudo actualizar la plantilla. Revisa tu conexión.'); }
      finally { setLoadingTemplate(false); }
    }
  };

  // ── Section Header ──────────────────────────────────────────────────────────
  const renderHeader = (id, title, fieldCond, fieldMostrar) => {
    const isVisible = cotizacion[fieldMostrar] !== false;
    return (
      <div style={{
        padding: '1rem', background: 'rgba(255,255,255,0.05)', display: 'flex',
        justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '0.75rem',
        borderBottom: openSection === id ? '1px solid var(--border-color)' : 'none',
        borderRadius: openSection === id ? '6px 6px 0 0' : '6px',
        opacity: isVisible ? 1 : 0.65,
      }}>
        <h4 onClick={() => toggleSection(id)} style={{ margin: 0, flex: '1 1 200px', minWidth: 0, display: 'flex', alignItems: 'center', gap: '10px', cursor: 'pointer' }}>
          {openSection === id ? <ChevronUp size={20} style={{ flexShrink: 0 }} /> : <ChevronDown size={20} style={{ flexShrink: 0 }} />}
          {title}
          {!isVisible && <span style={{ fontSize: '0.7rem', background: 'rgba(255,80,80,0.2)', color: '#ff7070', padding: '2px 8px', borderRadius: '10px', whiteSpace: 'nowrap' }}>No aparece en PDF</span>}
        </h4>
        <div style={{ display: 'flex', gap: '12px', alignItems: 'center', flexWrap: 'wrap', justifyContent: 'flex-end' }}>
          <ToggleSwitch checked={isVisible} onChange={() => handleToggleVisibility(fieldMostrar)} />
          {fieldCond && (
            <>
              <button onClick={(e) => { e.stopPropagation(); loadTemplate(fieldCond); }} className="btn btn-secondary"
                style={{ padding: '4px 10px', fontSize: '0.8rem', display: 'flex', gap: '5px', alignItems: 'center', whiteSpace: 'nowrap', flexShrink: 0 }}>
                <Download size={14} /> Cargar Plantilla
              </button>
              <button onClick={(e) => { e.stopPropagation(); saveTemplate(fieldCond); }} className="btn btn-primary"
                style={{ padding: '4px 10px', fontSize: '0.8rem', display: 'flex', gap: '5px', alignItems: 'center', whiteSpace: 'nowrap', flexShrink: 0 }}
                disabled={loadingTemplate}>
                <Save size={14} /> Guardar Global
              </button>
            </>
          )}
        </div>
      </div>
    );
  };

  // ── Array list editor ───────────────────────────────────────────────────────
  const renderArrayEditor = (field) => {
    const items = cotizacion[field] || [];
    const updateItem = (i, val) => { const n = [...items]; n[i] = val; handleUpdate(field, n); };
    const addItem = () => handleUpdate(field, [...items, '']);
    const removeItem = (i) => { if (window.confirm('¿Eliminar?')) handleUpdate(field, items.filter((_, idx) => idx !== i)); };
    return (
      <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
        {items.map((item, idx) => (
          <div key={idx} style={{ display: 'flex', gap: '10px', alignItems: 'flex-start' }}>
            <div style={{ marginTop: '35px', fontWeight: 'bold', color: 'var(--text-secondary)', width: '22px', textAlign: 'right' }}>{idx + 1}.</div>
            <RichTextEditor value={item} onChange={(val) => updateItem(idx, val)} />
            <button onClick={() => removeItem(idx)} className="btn btn-secondary" style={{ marginTop: '30px', padding: '6px', color: '#ff4d4f' }}><Trash2 size={16} /></button>
          </div>
        ))}
        <button onClick={addItem} className="btn btn-secondary" style={{ alignSelf: 'flex-start', display: 'flex', gap: '5px', alignItems: 'center' }}>
          <Plus size={16} /> Agregar Condición
        </button>
      </div>
    );
  };

  // ── Comerciales (6 fijos) ──────────────────────────────────────────────────
  const COMERCIALES_LABELS = ['FORMA DE PAGO:', 'COSTO DE ENTREGA:', 'LUGAR DE ENTREGA:', 'TIEMPO DE ENTREGA:', 'TIEMPO DE EJECUCIÓN:', 'VALIDEZ DE OFERTA:'];
  const renderComercialesEditor = () => {
    const items = [...(cotizacion.cond_comerciales || [])];
    while (items.length < 6) items.push('');
    const updateItem = (idx, val) => { const n = [...items]; n[idx] = val; handleUpdate('cond_comerciales', n); };
    return (
      <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
        {COMERCIALES_LABELS.map((label, idx) => (
          <div key={idx} style={{ display: 'flex', gap: '15px', alignItems: 'center' }}>
            <div style={{ fontWeight: 'bold', color: 'var(--text-secondary)', width: '180px', textAlign: 'right', fontSize: '0.85rem', flexShrink: 0 }}>{label}</div>
            <RichTextEditor value={items[idx] || ''} onChange={(val) => updateItem(idx, val)} minHeight="20px" />
          </div>
        ))}
      </div>
    );
  };

  // ── Bank Accounts Editor ────────────────────────────────────────────────────
  const renderBankEditor = () => {
    const cuentas = cotizacion.cuentas_bancarias || [];
    // Lee SIEMPRE el array más reciente del store (no una foto capturada en render),
    // así una subida async que termina tarde no pisa cambios hechos mientras tanto.
    const latestCuentas = () => useQuoteStore.getState().cotizacion?.cuentas_bancarias || [];

    const patchCuenta = (id, patch) =>
      handleUpdate('cuentas_bancarias', latestCuentas().map(b => (b.id === id ? { ...b, ...patch } : b)));
    const removeCuenta = (id) => {
      if (window.confirm('¿Eliminar este banco?')) {
        handleUpdate('cuentas_bancarias', latestCuentas().filter(b => b.id !== id));
      }
    };
    const addCuenta = () => handleUpdate('cuentas_bancarias', [
      ...latestCuentas(),
      {
        id: (typeof crypto !== 'undefined' && crypto.randomUUID) ? crypto.randomUUID() : String(Date.now()),
        banco: '', logo: '', visible: true, campos: [{ label: '', valor: '' }],
      },
    ]);

    return (
      <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
        {cuentas.length === 0 && (
          <div style={{ textAlign: 'center', padding: '1.5rem', color: 'var(--text-secondary)', border: '2px dashed var(--border-color)', borderRadius: '8px' }}>
            No hay bancos. Usa <strong>Agregar banco</strong> para crear uno (nombre, logo y campos editables).
          </div>
        )}
        {cuentas.length > 0 && (
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '1rem' }}>
            {cuentas.map(cuenta => (
              <BankCard key={cuenta.id} cuenta={cuenta}
                onChange={(patch) => patchCuenta(cuenta.id, patch)} onRemove={() => removeCuenta(cuenta.id)} />
            ))}
          </div>
        )}
        <button type="button" onClick={addCuenta} disabled={logoUploads > 0}
          className="btn btn-primary"
          title={logoUploads > 0 ? 'Espera a que termine de cargar el logo' : 'Agregar banco'}
          style={{ alignSelf: 'flex-start', display: 'flex', gap: '6px', alignItems: 'center', opacity: logoUploads > 0 ? 0.6 : 1 }}>
          <Plus size={16} /> {logoUploads > 0 ? 'Cargando logo…' : 'Agregar banco'}
        </button>
      </div>
    );
  };

  return (
    <div>
      <h3 style={{ marginBottom: '1rem', borderBottom: '1px solid var(--border-color)', paddingBottom: '0.5rem' }}>
        Condiciones Contractuales y Financieras
      </h3>
      <div style={{
        display: 'flex', flexDirection: 'column', gap: '10px',
        ...(readOnly ? { pointerEvents: 'none', opacity: 0.7 } : {})
      }}>

        <div style={{ border: '1px solid var(--border-color)', borderRadius: '6px' }}>
          {renderHeader('tecnicas', 'Condiciones Técnicas', 'cond_tecnicas', 'mostrar_cond_tecnicas')}
          {openSection === 'tecnicas' && <div style={{ padding: '1rem' }}>{renderArrayEditor('cond_tecnicas')}</div>}
        </div>

        <div style={{ border: '1px solid var(--border-color)', borderRadius: '6px' }}>
          {renderHeader('comerciales', 'Condiciones Comerciales', 'cond_comerciales', 'mostrar_cond_comerciales')}
          {openSection === 'comerciales' && (
            <div style={{ padding: '1rem' }}>
              <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '1rem' }}>Complete los valores para cada ítem comercial.</p>
              {renderComercialesEditor()}
            </div>
          )}
        </div>

        <div style={{ border: '1px solid var(--border-color)', borderRadius: '6px' }}>
          {renderHeader('otras', 'Otras Condiciones', 'cond_otras', 'mostrar_cond_otras')}
          {openSection === 'otras' && <div style={{ padding: '1rem' }}>{renderArrayEditor('cond_otras')}</div>}
        </div>

        <div style={{ border: '1px solid var(--border-color)', borderRadius: '6px' }}>
          {renderHeader('garantia', 'Garantía de Equipos', 'cond_garantia', 'mostrar_cond_garantia')}
          {openSection === 'garantia' && <div style={{ padding: '1rem' }}>{renderArrayEditor('cond_garantia')}</div>}
        </div>

        <div style={{ border: '1px solid var(--border-color)', borderRadius: '6px' }}>
          {renderHeader('garantia_servicio', 'Garantía de Servicio', 'cond_garantia_servicio', 'mostrar_cond_garantia_servicio')}
          {openSection === 'garantia_servicio' && (
            <div style={{ padding: '1rem' }}>
              <RichTextEditor value={cotizacion.cond_garantia_servicio || ''} onChange={(val) => handleUpdate('cond_garantia_servicio', val)} minHeight="100px" />
            </div>
          )}
        </div>

        <div style={{ border: '1px solid var(--border-color)', borderRadius: '6px' }}>
          {renderHeader('cuentas', 'Cuentas Bancarias', 'cuentas_bancarias', 'mostrar_cuentas_bancarias')}
          {openSection === 'cuentas' && (
            <div style={{ padding: '1rem' }}>
              <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '1rem' }}>
                Agrega bancos con su nombre, logo y campos (etiqueta y número). Usa <strong>Guardar Global</strong> para guardar estos bancos como plantilla, o <strong>Cargar Plantilla</strong> para traerlos a esta cotización.
              </p>
              {renderBankEditor()}
            </div>
          )}
        </div>

      </div>
    </div>
  );
}
