import React, { useState, useEffect } from 'react';
import { useWizardStore } from '../../store/wizardStore';
import { inspectorApi } from '../../api/inspectorApi';

export default function StepDatosCliente({ onNext }) {
  const { data, setData } = useWizardStore();
  const [searchTerm, setSearchTerm] = useState('');
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [showNewForm, setShowNewForm] = useState(false);

  // Form para nuevo cliente
  const [newClient, setNewClient] = useState({
    nombre: '',
    documento: '',
    direccion: '',
    atencion: '',
    referencia: '',
    correo: '',
    telefono: ''
  });

  useEffect(() => {
    const delayDebounceFn = setTimeout(async () => {
      if (searchTerm.length >= 2) {
        setLoading(true);
        try {
          const res = await inspectorApi.searchClientes(searchTerm);
          setResults(res);
        } catch (error) {
          console.error('Error buscando clientes', error);
        } finally {
          setLoading(false);
        }
      } else {
        setResults([]);
      }
    }, 500);

    return () => clearTimeout(delayDebounceFn);
  }, [searchTerm]);

  const handleSelectClient = (cliente) => {
    setData({
      cliente_id: cliente.id,
      cliente_info: cliente
    });
    onNext({ ...data, cliente_id: cliente.id });
  };

  const handleCreateClient = async (e) => {
    e.preventDefault();
    try {
      setLoading(true);
      const created = await inspectorApi.createCliente(newClient);
      setData({
        cliente_id: created.id,
        cliente_info: created
      });
      onNext({ ...data, cliente_id: created.id });
    } catch (error) {
      console.error('Error creando cliente', error);
      alert('Hubo un error al crear el cliente');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <h2 style={{ marginBottom: '1.5rem', textAlign: 'center' }}>Datos del Cliente</h2>

      {!showNewForm ? (
        <div style={{ maxWidth: '500px', margin: '0 auto' }}>
          <div className="form-group">
            <label>Buscar cliente existente (Nombre o DNI/RUC)</label>
            <input 
              type="text" 
              className="form-control"
              placeholder="Escribe para buscar..." 
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>

          {loading && <p>Buscando...</p>}

          {results.length > 0 && (
            <div style={{ marginTop: '1rem', border: '1px solid var(--border-color)', borderRadius: '8px', overflow: 'hidden' }}>
              {results.map(c => (
                <div 
                  key={c.id} 
                  onClick={() => handleSelectClient(c)}
                  style={{ padding: '1rem', borderBottom: '1px solid var(--border-color)', cursor: 'pointer' }}
                  className="hover-bg"
                >
                  <strong>{c.nombre}</strong> <span style={{ color: 'var(--text-secondary)' }}>({c.documento})</span>
                </div>
              ))}
            </div>
          )}

          <div style={{ marginTop: '2rem', textAlign: 'center' }}>
            <p style={{ color: 'var(--text-secondary)', marginBottom: '1rem' }}>¿No encuentras al cliente?</p>
            <button className="btn btn-secondary" onClick={() => setShowNewForm(true)}>
              + Crear Nuevo Cliente
            </button>
          </div>
        </div>
      ) : (
        <form onSubmit={handleCreateClient} style={{ maxWidth: '600px', margin: '0 auto', display: 'grid', gap: '1rem' }}>
          <div className="form-group">
            <label>Nombre Completo / Razón Social *</label>
            <input required type="text" className="form-control" value={newClient.nombre} onChange={e => setNewClient({...newClient, nombre: e.target.value})} />
          </div>
          <div className="form-group">
            <label>Documento (DNI/RUC) *</label>
            <input required type="text" className="form-control" value={newClient.documento} onChange={e => setNewClient({...newClient, documento: e.target.value})} />
          </div>
          <div className="form-group">
            <label>Dirección</label>
            <input type="text" className="form-control" value={newClient.direccion} onChange={e => setNewClient({...newClient, direccion: e.target.value})} />
          </div>
          <div className="form-group">
            <label>Atención a</label>
            <input type="text" className="form-control" value={newClient.atencion} onChange={e => setNewClient({...newClient, atencion: e.target.value})} />
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
             <div className="form-group">
                <label>Teléfono</label>
                <input type="text" className="form-control" value={newClient.telefono} onChange={e => setNewClient({...newClient, telefono: e.target.value})} />
             </div>
             <div className="form-group">
                <label>Correo</label>
                <input type="email" className="form-control" value={newClient.correo} onChange={e => setNewClient({...newClient, correo: e.target.value})} />
             </div>
          </div>
          <div style={{ display: 'flex', gap: '1rem', marginTop: '1rem' }}>
            <button type="button" className="btn btn-secondary" style={{ flex: 1 }} onClick={() => setShowNewForm(false)}>
              Cancelar
            </button>
            <button type="submit" className="btn btn-primary" style={{ flex: 1 }} disabled={loading}>
              {loading ? 'Guardando...' : 'Guardar y Continuar'}
            </button>
          </div>
        </form>
      )}
    </div>
  );
}
