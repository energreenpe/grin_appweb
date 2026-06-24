import { useEffect, useState, useRef } from 'react';
import { getFotos, uploadFoto, updateFoto, deleteFoto } from '../api/plannerApi';
import { fileUrl } from '../../../lib/api';

const ETAPAS = [
  { label: 'Estructura', codigo: 'estructura', emoji: '🏗️' },
  { label: 'Paneles', codigo: 'paneles', emoji: '☀️' },
  { label: 'Cableado', codigo: 'cableado', emoji: '🔌' },
  { label: 'Inversor', codigo: 'inversor', emoji: '⚡' },
  { label: 'Conexión Red', codigo: 'conexion_red', emoji: '🔗' },
  { label: 'Terminado', codigo: 'terminado', emoji: '✅' },
  { label: 'General', codigo: 'general', emoji: '📷' },
];
const hoy = () => new Date().toISOString().split('T')[0];

export default function EvidenciaTab({ proyectoId }) {
  const [fotos, setFotos] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [etapaFil, setEtapaFil] = useState(null);
  const [soloPdf, setSoloPdf] = useState(false);
  const [form, setForm] = useState({ etapa: 'General', etapa_codigo: 'general', emoji: '📷', fecha: hoy(), subido_por: '' });
  const [archivo, setArchivo] = useState(null);
  const [preview, setPreview] = useState(null);
  const [subiendo, setSubiendo] = useState(false);
  const [fotoGrande, setFotoGrande] = useState(null);
  const inputRef = useRef();

  const cargar = async () => {
    setLoading(true);
    const res = await getFotos(proyectoId, { etapa: etapaFil || undefined, solo_pdf: soloPdf || undefined });
    setFotos(res.data); setLoading(false);
  };
  useEffect(() => { cargar(); /* eslint-disable-next-line */ }, [proyectoId, etapaFil, soloPdf]);

  const handleArchivo = (e) => { const f = e.target.files[0]; if (!f) return; setArchivo(f); setPreview(URL.createObjectURL(f)); };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!archivo) { window.alert('Selecciona una imagen'); return; }
    setSubiendo(true);
    try {
      const fd = new FormData();
      fd.append('file', archivo);
      Object.entries(form).forEach(([k, v]) => fd.append(k, v));
      await uploadFoto(proyectoId, fd);
      setShowForm(false); setArchivo(null); setPreview(null);
      setForm({ etapa: 'General', etapa_codigo: 'general', emoji: '📷', fecha: hoy(), subido_por: '' });
      cargar();
    } catch (err) {
      window.alert(err?.response?.data?.detail || 'Error al subir');
    } finally { setSubiendo(false); }
  };

  const togglePdf = async (foto) => { await updateFoto(foto.id, { incluir_en_pdf: !foto.incluir_en_pdf }); cargar(); };
  const handleEditComentario = async (foto, texto) => { await updateFoto(foto.id, { comentario_pdf: texto }); cargar(); };

  const grupos = fotos.reduce((acc, f) => { const k = f.etapa || 'General'; (acc[k] = acc[k] || []).push(f); return acc; }, {});
  const seleccionadas = fotos.filter((f) => f.incluir_en_pdf).length;

  return (
    <div className="pl-page">
      <div className="pl-between">
        <div className="pl-row">
          <h2 className="pl-h2">Evidencia Fotográfica</h2>
          {seleccionadas > 0 && (
            <span className="pl-badge" style={{ background: 'rgba(98,185,137,.18)', color: '#62B989' }}>{seleccionadas} foto{seleccionadas > 1 ? 's' : ''} para PDF</span>
          )}
        </div>
        <div className="pl-row">
          <button className={`pl-btn pl-btn-sm ${soloPdf ? 'pl-btn-primary' : 'pl-btn-outline'}`} onClick={() => setSoloPdf((v) => !v)}>{soloPdf ? '✅ Solo para PDF' : '📄 Filtrar PDF'}</button>
          <button className="pl-btn pl-btn-primary pl-btn-sm" onClick={() => setShowForm(true)}>📷 Subir Foto</button>
        </div>
      </div>

      <div className="pl-row">
        <button className={`pl-pill ${!etapaFil ? 'pl-pill-active' : ''}`} onClick={() => setEtapaFil(null)}>Todas</button>
        {ETAPAS.map((e) => (
          <button key={e.codigo} className={`pl-pill ${etapaFil === e.label ? 'pl-pill-active' : ''}`} onClick={() => setEtapaFil(e.label)}>{e.emoji} {e.label}</button>
        ))}
      </div>

      {showForm && (
        <div className="pl-modal-overlay" onClick={() => { setShowForm(false); setPreview(null); setArchivo(null); }}>
          <div className="pl-modal pl-modal-sm" onClick={(e) => e.stopPropagation()}>
            <div className="pl-modal-head"><h3 className="pl-h2">Subir Evidencia</h3><button className="pl-x" onClick={() => { setShowForm(false); setPreview(null); setArchivo(null); }}>✕</button></div>
            <form onSubmit={handleSubmit} className="pl-modal-body">
              <div>
                <p className="pl-label">Etapa</p>
                <div className="pl-grid" style={{ gridTemplateColumns: 'repeat(4, 1fr)', gap: '.4rem' }}>
                  {ETAPAS.map((e) => {
                    const active = form.etapa === e.label;
                    return (
                      <button key={e.codigo} type="button" onClick={() => setForm((f) => ({ ...f, etapa: e.label, etapa_codigo: e.codigo, emoji: e.emoji }))}
                        className="pl-card" style={{ padding: '.5rem', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '.2rem', fontSize: '.7rem', cursor: 'pointer', borderColor: active ? 'var(--primary-color)' : 'var(--border-color)', background: active ? 'rgba(98,185,137,.1)' : 'transparent', color: active ? 'var(--primary-color)' : 'var(--text-secondary)' }}>
                        <span style={{ fontSize: '1.1rem' }}>{e.emoji}</span>{e.label}
                      </button>
                    );
                  })}
                </div>
              </div>
              <div className="pl-dropzone" onClick={() => inputRef.current.click()}>
                {preview ? <img src={preview} alt="preview" style={{ maxHeight: 160, margin: '0 auto', borderRadius: 8, objectFit: 'cover' }} />
                  : <div className="pl-muted"><p style={{ fontSize: '1.8rem', marginBottom: '.25rem' }}>📷</p><p style={{ fontSize: '.85rem' }}>Click para seleccionar imagen</p><p style={{ fontSize: '.72rem' }}>JPG, PNG, WEBP — máx 10MB (se convierte a WebP)</p></div>}
                <input ref={inputRef} type="file" accept="image/*" style={{ display: 'none' }} onChange={handleArchivo} />
              </div>
              <div className="pl-grid pl-grid-2">
                <div><label className="pl-label">Fecha</label><input className="pl-input" type="date" value={form.fecha} onChange={(e) => setForm((f) => ({ ...f, fecha: e.target.value }))} /></div>
                <div><label className="pl-label">Subido por</label><input className="pl-input" value={form.subido_por} onChange={(e) => setForm((f) => ({ ...f, subido_por: e.target.value }))} placeholder="Tu nombre" /></div>
              </div>
              <div className="pl-row" style={{ gap: '.5rem' }}>
                <button type="button" className="pl-btn pl-btn-outline" style={{ flex: 1 }} onClick={() => { setShowForm(false); setPreview(null); setArchivo(null); }}>Cancelar</button>
                <button type="submit" className="pl-btn pl-btn-primary" style={{ flex: 1 }} disabled={subiendo || !archivo}>{subiendo ? 'Subiendo...' : 'Subir Foto'}</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {loading ? <p className="pl-empty">Cargando...</p>
        : fotos.length === 0 ? <div className="pl-empty"><div className="pl-empty-icon">📷</div><p>Sin fotos aún.</p></div>
          : (
            <div className="pl-page">
              {Object.entries(grupos).map(([etapa, imgs]) => {
                const ei = ETAPAS.find((e) => e.label === etapa) || { emoji: '📷' };
                return (
                  <div key={etapa}>
                    <h3 className="pl-h3">{ei.emoji} {etapa} <span className="pl-muted" style={{ fontWeight: 400 }}>({imgs.length})</span></h3>
                    <div className="pl-grid pl-grid-2">
                      {imgs.map((f) => (
                        <div key={f.id} className="pl-card" style={{ overflow: 'hidden', borderColor: f.incluir_en_pdf ? 'rgba(98,185,137,.5)' : 'var(--border-color)' }}>
                          <div style={{ position: 'relative', cursor: 'pointer' }} onClick={() => setFotoGrande(f)}>
                            <img src={fileUrl(f.ruta)} alt={f.nombre_original} style={{ width: '100%', height: 160, objectFit: 'cover', display: 'block' }} />
                            <div style={{ position: 'absolute', top: 8, right: 8, display: 'flex', gap: '.3rem' }}>
                              <button onClick={(e) => { e.stopPropagation(); togglePdf(f); }} title="Incluir/excluir del PDF"
                                style={{ width: 28, height: 28, borderRadius: '50%', border: 'none', cursor: 'pointer', fontWeight: 700, background: f.incluir_en_pdf ? '#62B989' : 'rgba(0,0,0,.6)', color: f.incluir_en_pdf ? '#000' : '#fff' }}>{f.incluir_en_pdf ? '✓' : '○'}</button>
                              <button onClick={(e) => { e.stopPropagation(); if (window.confirm('¿Eliminar foto?')) deleteFoto(f.id).then(cargar); }}
                                style={{ width: 28, height: 28, borderRadius: '50%', border: 'none', cursor: 'pointer', background: '#a33', color: '#fff' }}>✕</button>
                            </div>
                          </div>
                          <div className="pl-card-pad">
                            <div className="pl-between pl-muted" style={{ fontSize: '.72rem', marginBottom: '.5rem' }}>
                              <span>📅 {f.fecha}</span>{f.subido_por && <span>👤 {f.subido_por}</span>}
                            </div>
                            {f.incluir_en_pdf && (
                              <div>
                                <p className="pl-label">Comentario PDF</p>
                                <textarea className="pl-textarea" defaultValue={f.comentario_pdf || ''} rows={2}
                                  placeholder="Escribe un comentario para el reporte..."
                                  onBlur={(e) => handleEditComentario(f, e.target.value)} />
                              </div>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                );
              })}
            </div>
          )}

      {fotoGrande && (
        <div className="pl-modal-overlay" style={{ background: 'rgba(0,0,0,.9)' }} onClick={() => setFotoGrande(null)}>
          <button className="pl-x" style={{ position: 'absolute', top: 16, right: 16, color: '#fff', fontSize: '1.5rem' }}>✕</button>
          <img src={fileUrl(fotoGrande.ruta)} alt="foto" style={{ maxWidth: '100%', maxHeight: '100%', borderRadius: 12, objectFit: 'contain' }} onClick={(e) => e.stopPropagation()} />
        </div>
      )}
    </div>
  );
}
