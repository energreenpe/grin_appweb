import { useState, useEffect } from 'react';
import { createProyecto, updateProyecto } from '../api/plannerApi';

const REGIONES = ['Lima', 'La Libertad', 'Piura', 'Lambayeque', 'Arequipa', 'Cusco', 'Junín', 'Áncash', 'Ica', 'Cajamarca', 'Puno', 'San Martín', 'Loreto', 'Ucayali', 'Madre de Dios', 'Tacna', 'Moquegua', 'Huánuco', 'Pasco', 'Apurímac', 'Ayacucho', 'Huancavelica', 'Amazonas', 'Tumbes', 'Callao'];
const ESTADOS = ['Pendiente', 'En Progreso', 'Completado', 'Cancelado'];

export default function ProyectoModal({ proyecto, onClose, onSaved }) {
  const [form, setForm] = useState({
    nombre: '', cliente: '', ubicacion: '', region: '',
    paneles: 0, estado: 'Pendiente', fecha_inicio: '', fecha_fin: '', alcance: '',
  });
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (proyecto) setForm({
      nombre: proyecto.nombre || '', cliente: proyecto.cliente || '',
      ubicacion: proyecto.ubicacion || '', region: proyecto.region || '',
      paneles: proyecto.paneles || 0, estado: proyecto.estado || 'Pendiente',
      fecha_inicio: proyecto.fecha_inicio || '', fecha_fin: proyecto.fecha_fin || '',
      alcance: proyecto.alcance || '',
    });
  }, [proyecto]);

  const set = (k, v) => setForm((f) => ({ ...f, [k]: v }));

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const payload = {
        ...form, paneles: Number(form.paneles),
        fecha_inicio: form.fecha_inicio || null, fecha_fin: form.fecha_fin || null,
      };
      if (proyecto) await updateProyecto(proyecto.id, payload);
      else await createProyecto(payload);
      onSaved();
    } catch { window.alert('Error al guardar'); }
    finally { setLoading(false); }
  };

  return (
    <div className="pl-modal-overlay" onClick={onClose}>
      <div className="pl-modal" onClick={(e) => e.stopPropagation()}>
        <div className="pl-modal-head">
          <h2 className="pl-h2">{proyecto ? 'Editar Proyecto' : 'Nuevo Proyecto'}</h2>
          <button className="pl-x" onClick={onClose}>✕</button>
        </div>
        <form onSubmit={handleSubmit} className="pl-modal-body">
          <input className="pl-input" required value={form.nombre}
            onChange={(e) => set('nombre', e.target.value)} placeholder="Nombre del proyecto *" />
          <div className="pl-grid pl-grid-2">
            <input className="pl-input" value={form.cliente} onChange={(e) => set('cliente', e.target.value)} placeholder="Cliente" />
            <input className="pl-input" value={form.ubicacion} onChange={(e) => set('ubicacion', e.target.value)} placeholder="Ubicación" />
            <select className="pl-select" value={form.region} onChange={(e) => set('region', e.target.value)}>
              <option value="">Región (feriados)</option>
              {REGIONES.map((r) => <option key={r}>{r}</option>)}
            </select>
            <input className="pl-input" type="number" min="0" value={form.paneles} onChange={(e) => set('paneles', e.target.value)} placeholder="Paneles" />
            <select className="pl-select" value={form.estado} onChange={(e) => set('estado', e.target.value)}>
              {ESTADOS.map((s) => <option key={s}>{s}</option>)}
            </select>
            <div />
            <div>
              <label className="pl-label">Fecha inicio</label>
              <input className="pl-input" type="date" value={form.fecha_inicio} onChange={(e) => set('fecha_inicio', e.target.value)} />
            </div>
            <div>
              <label className="pl-label">Fecha fin</label>
              <input className="pl-input" type="date" value={form.fecha_fin} onChange={(e) => set('fecha_fin', e.target.value)} />
            </div>
          </div>
          <textarea className="pl-textarea" rows={2} value={form.alcance}
            onChange={(e) => set('alcance', e.target.value)} placeholder="Alcance del proyecto..." />
          <div className="pl-row" style={{ gap: '.75rem' }}>
            <button type="button" className="pl-btn pl-btn-outline" style={{ flex: 1 }} onClick={onClose}>Cancelar</button>
            <button type="submit" className="pl-btn pl-btn-primary" style={{ flex: 1 }} disabled={loading}>
              {loading ? 'Guardando...' : proyecto ? 'Actualizar' : 'Crear Proyecto'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
