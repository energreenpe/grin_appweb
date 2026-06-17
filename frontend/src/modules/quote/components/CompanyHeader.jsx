import { useState, useEffect, useCallback } from 'react';
import { useQuoteStore } from '../store/quoteStore';
import { quoteApi } from '../api/quoteApi';
import { notify } from '../../../lib/notify';

export default function CompanyHeader({ readOnly = false }) {
  const { cotizacion, updateHeader } = useQuoteStore();
  const [empresa, setEmpresa] = useState(null);
  const [vendedores, setVendedores] = useState([]);
  const [showModal, setShowModal] = useState(false);
  const [editEmpresa, setEditEmpresa] = useState({});

  const loadData = useCallback(async () => {
    try {
      const [empData, vendData] = await Promise.all([
        quoteApi.getEmpresa(),
        quoteApi.getVendedores()
      ]);
      setEmpresa(empData);
      setVendedores(vendData);
    } catch (err) {
      console.error("Error cargando empresa/vendedores", err);
      notify('No se pudieron cargar los datos de empresa.');
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  if (!cotizacion || !empresa) return null;

  const handleSellerChange = (e) => {
    const vName = e.target.value;
    const v = vendedores.find(v => v.nombre === vName);
    updateHeader(cotizacion.id, {
      vendedor_nombre: v ? v.nombre : '',
      vendedor_correo: v ? v.correo : '',
      vendedor_tel: v ? v.telefono : ''
    });
  };

  const handleVersionChange = (e) => {
    updateHeader(cotizacion.id, { version: e.target.value });
  };

  const handleFileChange = async (e) => {
    const file = e.target.files[0];
    if (file) {
      try {
        await quoteApi.uploadLogo(file);
        notify("Logo subido correctamente.", "success");
        loadData(); // reload empresa data
      } catch (err) {
        notify(err?.response?.data?.detail || "Error al subir el logo.");
      }
    }
  };

  const openModal = () => {
    setEditEmpresa({ ...empresa });
    setShowModal(true);
  };

  const saveEmpresa = async () => {
    try {
      await quoteApi.updateEmpresa(editEmpresa);
      setShowModal(false);
      loadData();
    } catch (err) {
      notify(err?.response?.data?.detail || "Error al guardar los datos de empresa.");
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid var(--border-color)', paddingBottom: '0.5rem' }}>
        <h3>Datos de Empresa</h3>
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <button onClick={openModal} className="btn btn-secondary" style={{ fontSize: '0.8rem', padding: '0.25rem 0.5rem' }}>
            Cambiar Datos
          </button>
          <label className="btn btn-secondary" style={{ fontSize: '0.8rem', padding: '0.25rem 0.5rem', cursor: 'pointer' }}>
            Cambiar Logo
            <input type="file" style={{ display: 'none' }} accept="image/*" onChange={handleFileChange} />
          </label>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', backgroundColor: 'rgba(255,255,255,0.02)', padding: '1rem', borderRadius: 'var(--radius)' }}>
        <div>
          <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>Empresa Fija:</div>
          <div style={{ fontWeight: '600' }}>{empresa.nombre}</div>
          <div style={{ fontSize: '0.85rem' }}>RUC: {empresa.ruc}</div>
          <div style={{ fontSize: '0.85rem' }}>Dirección: {empresa.direccion}</div>
        </div>
        <div>
          <label style={{ display: 'block', fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '0.25rem' }}>Versión del Documento</label>
          <input
            type="text"
            value={cotizacion.version || ''}
            onChange={handleVersionChange}
            disabled={readOnly}
            className="input-field"
            placeholder="ej: A, B, B1"
            style={{ width: '100px' }}
          />
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '1rem' }}>
        <div>
          <label style={{ display: 'block', fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '0.25rem' }}>Vendedor</label>
          <select
            value={cotizacion.vendedor_nombre || ''}
            onChange={handleSellerChange}
            disabled={readOnly}
            className="input-field"
          >
            <option value="">Seleccione vendedor...</option>
            {vendedores.map(v => (
              <option key={v.id} value={v.nombre}>{v.nombre}</option>
            ))}
          </select>
        </div>
        <div>
          <label style={{ display: 'block', fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '0.25rem' }}>Correo Vendedor</label>
          <input
            type="text"
            readOnly
            value={cotizacion.vendedor_correo || ''}
            className="input-field"
            style={{ backgroundColor: 'rgba(0,0,0,0.2)', color: 'var(--text-secondary)' }}
          />
        </div>
        <div>
          <label style={{ display: 'block', fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '0.25rem' }}>Teléfono Vendedor</label>
          <input
            type="text"
            readOnly
            value={cotizacion.vendedor_tel || ''}
            className="input-field"
            style={{ backgroundColor: 'rgba(0,0,0,0.2)', color: 'var(--text-secondary)' }}
          />
        </div>
      </div>

      {showModal && (
        <div style={{
          position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
          backgroundColor: 'rgba(0,0,0,0.7)', zIndex: 100,
          display: 'flex', alignItems: 'center', justifyContent: 'center'
        }}>
          <div className="glass-panel" style={{ padding: '2rem', width: '400px', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <h3>Editar Empresa</h3>
            <div>
              <label>Nombre de la Empresa</label>
              <input
                type="text"
                value={editEmpresa.nombre || ''}
                onChange={e => setEditEmpresa({ ...editEmpresa, nombre: e.target.value })}
                className="input-field"
              />
            </div>
            <div>
              <label>RUC</label>
              <input
                type="text"
                value={editEmpresa.ruc || ''}
                onChange={e => setEditEmpresa({ ...editEmpresa, ruc: e.target.value })}
                className="input-field"
              />
            </div>
            <div>
              <label>Dirección</label>
              <textarea
                value={editEmpresa.direccion || ''}
                onChange={e => setEditEmpresa({ ...editEmpresa, direccion: e.target.value })}
                className="input-field"
                style={{ minHeight: '80px' }}
              />
            </div>
            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '1rem', marginTop: '1rem' }}>
              <button onClick={() => setShowModal(false)} className="btn btn-secondary">Cancelar</button>
              <button onClick={saveEmpresa} className="btn btn-primary">Guardar</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
