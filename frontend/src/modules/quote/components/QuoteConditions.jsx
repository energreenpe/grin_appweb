import { useState, useEffect, useRef } from 'react';
import { useQuoteStore } from '../store/quoteStore';
import { quoteApi } from '../api/quoteApi';
import { ChevronDown, ChevronUp, Save, Download, Plus, Trash2, Bold, Palette } from 'lucide-react';

// Importa todos los logos de bancos desde src/assets/banks/
const bankLogos = import.meta.glob('../../../assets/banks/*.png', { eager: true, import: 'default' });
const getBankLogo = (filename) => {
  const key = Object.keys(bankLogos).find(k => k.endsWith(`/${filename}`));
  return key ? bankLogos[key] : null;
};

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

// ─── Bank Card ────────────────────────────────────────────────────────────────
const BANK_FIELDS_FULL = ['Soles', 'CCI Soles', 'Dólares', 'CCI Dólares'];
const BANK_FIELDS_DETRACCIONES = ['Detracciones'];

const BankCard = ({ cuenta, onChange }) => {
  const fields = cuenta.tipo === 'detracciones' ? BANK_FIELDS_DETRACCIONES : BANK_FIELDS_FULL;
  const logoSrc = getBankLogo(cuenta.logo);
  const updateField = (key, val) => onChange({ ...cuenta, datos: { ...cuenta.datos, [key]: val } });
  const isVisible = cuenta.visible !== false;
  const toggleVisibility = (val) => onChange({ ...cuenta, visible: val });

  return (
    <div style={{
      background: 'rgba(255,255,255,0.04)', border: '1px solid var(--border-color)',
      borderRadius: '8px', padding: '1rem', flex: '1 1 300px', minWidth: '270px',
      opacity: isVisible ? 1 : 0.5, transition: 'opacity 0.2s'
    }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1rem', paddingBottom: '0.75rem', borderBottom: '1px solid var(--border-color)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          {logoSrc
            ? <img src={logoSrc} alt={cuenta.banco} style={{ height: '28px', maxWidth: '100px', objectFit: 'contain' }} />
            : <span style={{ fontWeight: 'bold', fontSize: '0.9rem' }}>{cuenta.banco}</span>
          }
          <span style={{ fontWeight: 'bold', fontSize: '0.9rem', color: 'var(--text-secondary)' }}>{logoSrc ? cuenta.banco : ''}</span>
        </div>
        <ToggleSwitch checked={isVisible} onChange={toggleVisibility} />
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
        {fields.map(field => (
          <div key={field} style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <label style={{ width: '90px', textAlign: 'right', fontSize: '0.78rem', color: 'var(--text-secondary)', flexShrink: 0 }}>{field}:</label>
            <input
              type="text"
              value={cuenta.datos?.[field] || ''}
              onChange={(e) => updateField(field, e.target.value)}
              placeholder="—"
              style={{
                flex: 1, background: 'rgba(255,255,255,0.07)', border: '1px solid var(--border-color)',
                borderRadius: '5px', padding: '5px 10px', color: 'inherit', fontSize: '0.85rem',
              }}
            />
          </div>
        ))}
      </div>
    </div>
  );
};

// ─── Main Component ───────────────────────────────────────────────────────────
export default function QuoteConditions({ cotizacionId }) {
  const { cotizacion, updateHeader } = useQuoteStore();
  const [openSection, setOpenSection] = useState('tecnicas');
  const [plantillas, setPlantillas] = useState(null);
  const [loadingTemplate, setLoadingTemplate] = useState(false);

  useEffect(() => {
    quoteApi.getPlantillas().then(setPlantillas).catch(console.error);
  }, []);

  const toggleSection = (id) => setOpenSection(openSection === id ? null : id);
  const handleUpdate = async (field, value) => { await updateHeader(cotizacionId, { [field]: value }); };
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
        alert('Plantilla global actualizada.');
      } catch { alert('Error al actualizar la plantilla.'); }
      finally { setLoadingTemplate(false); }
    }
  };

  // ── Section Header ──────────────────────────────────────────────────────────
  const renderHeader = (id, title, fieldCond, fieldMostrar) => {
    const isVisible = cotizacion[fieldMostrar] !== false;
    return (
      <div style={{
        padding: '1rem', background: 'rgba(255,255,255,0.05)', display: 'flex',
        justifyContent: 'space-between', alignItems: 'center',
        borderBottom: openSection === id ? '1px solid var(--border-color)' : 'none',
        borderRadius: openSection === id ? '6px 6px 0 0' : '6px',
        opacity: isVisible ? 1 : 0.65,
      }}>
        <h4 onClick={() => toggleSection(id)} style={{ margin: 0, flex: 1, display: 'flex', alignItems: 'center', gap: '10px', cursor: 'pointer' }}>
          {openSection === id ? <ChevronUp size={20} /> : <ChevronDown size={20} />}
          {title}
          {!isVisible && <span style={{ fontSize: '0.7rem', background: 'rgba(255,80,80,0.2)', color: '#ff7070', padding: '2px 8px', borderRadius: '10px' }}>No aparece en PDF</span>}
        </h4>
        <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
          <ToggleSwitch checked={isVisible} onChange={() => handleToggleVisibility(fieldMostrar)} />
          {fieldCond && (
            <>
              <button onClick={(e) => { e.stopPropagation(); loadTemplate(fieldCond); }} className="btn btn-secondary"
                style={{ padding: '4px 10px', fontSize: '0.8rem', display: 'flex', gap: '5px', alignItems: 'center' }}>
                <Download size={14} /> Cargar Plantilla
              </button>
              <button onClick={(e) => { e.stopPropagation(); saveTemplate(fieldCond); }} className="btn btn-primary"
                style={{ padding: '4px 10px', fontSize: '0.8rem', display: 'flex', gap: '5px', alignItems: 'center' }}
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
    const updateCuenta = (idx, updated) => {
      const newCuentas = [...cuentas];
      newCuentas[idx] = updated;
      handleUpdate('cuentas_bancarias', newCuentas);
    };

    if (cuentas.length === 0) {
      return (
        <div style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-secondary)', border: '2px dashed var(--border-color)', borderRadius: '8px' }}>
          <p style={{ marginBottom: '1rem' }}>No hay cuentas bancarias configuradas.</p>
          <p>Haz clic en <strong style={{ color: 'var(--accent)' }}>Cargar Plantilla</strong> para inicializar los 5 bancos por defecto.</p>
        </div>
      );
    }

    return (
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '1rem' }}>
        {cuentas.map((cuenta, idx) => (
          <BankCard key={idx} cuenta={cuenta} onChange={(updated) => updateCuenta(idx, updated)} />
        ))}
      </div>
    );
  };

  return (
    <div>
      <h3 style={{ marginBottom: '1rem', borderBottom: '1px solid var(--border-color)', paddingBottom: '0.5rem' }}>
        Condiciones Contractuales y Financieras
      </h3>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>

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
                Edita los números de cuenta. Usa <strong>Cargar Plantilla</strong> para aplicar la plantilla maestra, o <strong>Guardar Global</strong> para actualizarla.
              </p>
              {renderBankEditor()}
            </div>
          )}
        </div>

      </div>
    </div>
  );
}
