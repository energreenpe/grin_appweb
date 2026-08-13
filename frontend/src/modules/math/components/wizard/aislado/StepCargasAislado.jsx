import React, { useState, useEffect, useRef } from 'react';
import { useCalculoStore } from '../../../store/calculoStore';
import { mathApi } from '../../../api/mathApi';

export default function StepCargasAislado({ onNext }) {
  const { data, setData } = useCalculoStore();

  const [catalogo, setCatalogo] = useState([]);
  const [nombre, setNombre] = useState('');
  const [cantidad, setCantidad] = useState(1);
  const [horas, setHoras] = useState(4);
  const [watts, setWatts] = useState('');

  // Autocomplete personalizado (el <datalist> nativo no funciona en móvil).
  const [showSugerencias, setShowSugerencias] = useState(false);
  const electroRef = useRef(null);

  useEffect(() => {
    (async () => {
      try {
        setCatalogo(await mathApi.getElectrodomesticos());
      } catch (e) {
        console.error('Error cargando catálogo de electrodomésticos', e);
      }
    })();
  }, []);

  // Cerrar el dropdown al hacer clic/tocar fuera.
  useEffect(() => {
    const handler = (e) => {
      if (electroRef.current && !electroRef.current.contains(e.target)) setShowSugerencias(false);
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  // Sugerencias filtradas por lo escrito (todas al enfocar vacío; el dropdown scrollea).
  const sugerencias = nombre.trim()
    ? catalogo.filter((e) => e.nombre.toLowerCase().includes(nombre.trim().toLowerCase()))
    : catalogo;

  const handleNombre = (val) => {
    setNombre(val);
    setShowSugerencias(true);
    // Si coincide exactamente con un ítem del catálogo, autocompletar potencia.
    const match = catalogo.find((e) => e.nombre.toLowerCase() === val.toLowerCase());
    if (match) setWatts(String(match.potencia_w));
  };

  const seleccionarElectro = (e) => {
    setNombre(e.nombre);
    setWatts(String(e.potencia_w));
    setShowSugerencias(false);
  };

  const handleAdd = (e) => {
    e.preventDefault();
    if (!nombre.trim() || !watts) return;
    const item = {
      nombre: nombre.trim(),
      cantidad: Number(cantidad),
      horas: Number(horas),
      potencia_w: Number(watts),
    };
    setData({ cargas: [...data.cargas, item] });
    setNombre(''); setCantidad(1); setHoras(4); setWatts(''); setShowSugerencias(false);
  };

  const handleRemove = (index) => {
    const list = [...data.cargas];
    list.splice(index, 1);
    setData({ cargas: list });
  };

  const totalEnergia = data.cargas.reduce((acc, c) => acc + c.cantidad * c.potencia_w * c.horas, 0);
  const totalPotencia = data.cargas.reduce((acc, c) => acc + c.cantidad * c.potencia_w, 0);
  const scrollable = data.cargas.length > 4;
  const stickyTh = { position: 'sticky', top: 0, zIndex: 1 };
  // minWidth:0 permite que los hijos de grid/flex se encojan (responsivo móvil).
  const field = { minWidth: 0 };

  const dropdownStyle = {
    position: 'absolute', top: '100%', left: 0, right: 0, background: 'var(--surface-color)',
    border: '1px solid var(--border-color)', borderRadius: 'var(--radius)', boxShadow: '0 8px 24px rgba(0,0,0,0.4)',
    zIndex: 50, maxHeight: '220px',
    // overflowX:hidden evita la barra horizontal: con overflow-y:auto el navegador
    // forzaría overflow-x a auto (spec CSS) y aparecería un scroll horizontal.
    overflowX: 'hidden', overflowY: 'auto', marginTop: '4px',
  };
  const dropdownItem = {
    padding: '0.6rem 0.8rem', cursor: 'pointer', borderBottom: '1px solid var(--border-color)',
    fontSize: '0.9rem', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis',
  };

  return (
    <div>
      <h2 style={{ marginBottom: '1rem', textAlign: 'center' }}>Levantamiento de Cargas</h2>
      <p style={{ textAlign: 'center', color: 'var(--text-secondary)', marginBottom: '2rem' }}>
        Añade los electrodomésticos a alimentar. Al elegir uno del catálogo, su potencia se autocompleta.
      </p>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: '2rem', maxWidth: '800px', margin: '0 auto', width: '100%', minWidth: 0 }}>
        <form
          className="glass-panel"
          style={{
            padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1rem', minWidth: 0,
            // Eleva el contexto de apilamiento del formulario por encima del panel
            // de cargas (ambos crean stacking context por su backdrop-filter), para
            // que el dropdown de sugerencias no quede oculto bajo la tabla.
            position: 'relative', zIndex: showSugerencias ? 30 : 1,
          }}
          onSubmit={handleAdd}
        >
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(120px, 1fr))', gap: '1rem', minWidth: 0 }}>
            <div style={{ ...field, position: 'relative' }} ref={electroRef}>
              <label>Electrodoméstico</label>
              <input
                type="text" className="input-field" value={nombre} autoComplete="off"
                onChange={(e) => handleNombre(e.target.value)}
                onFocus={() => setShowSugerencias(true)}
                required
              />
              {showSugerencias && sugerencias.length > 0 && (
                <div style={dropdownStyle}>
                  {sugerencias.map((e) => (
                    <div
                      key={e.id}
                      style={dropdownItem}
                      title={e.nombre}
                      onMouseEnter={(ev) => (ev.currentTarget.style.background = 'rgba(255,255,255,0.06)')}
                      onMouseLeave={(ev) => (ev.currentTarget.style.background = 'transparent')}
                      onClick={() => seleccionarElectro(e)}
                    >
                      {e.nombre}
                    </div>
                  ))}
                </div>
              )}
            </div>
            <div style={field}>
              <label>Cantidad</label>
              <input type="number" min="1" className="input-field" value={cantidad} onChange={(e) => setCantidad(e.target.value)} required />
            </div>
            <div style={field}>
              <label>Potencia (W)</label>
              <input type="number" min="0" className="input-field" value={watts} onChange={(e) => setWatts(e.target.value)} required />
            </div>
            <div style={field}>
              <label>Horas/día</label>
              <input type="number" min="0" step="0.1" max="24" className="input-field" value={horas} onChange={(e) => setHoras(e.target.value)} required />
            </div>
          </div>
          <button type="submit" className="btn btn-secondary" style={{ alignSelf: 'flex-start' }}>+ Agregar</button>
        </form>

        <div className="glass-panel" style={{ padding: '1.5rem', minWidth: 0 }}>
          <h3>Cargas registradas ({data.cargas.length})</h3>
          {data.cargas.length === 0 ? (
            <p style={{ color: 'var(--text-secondary)', marginTop: '1rem' }}>No hay cargas agregadas todavía.</p>
          ) : (
            <>
              <div className="table-container" style={{ marginTop: '1rem', ...(scrollable ? { maxHeight: '235px', overflowY: 'auto' } : {}) }}>
                <table style={{ minWidth: '420px' }}>
                  <thead>
                    <tr>
                      <th style={stickyTh}>Equipo</th>
                      <th style={stickyTh}>Cant.</th>
                      <th style={stickyTh}>W c/u</th>
                      <th style={stickyTh}>Potencia (W)</th>
                      <th style={stickyTh}>Hrs/día</th>
                      <th style={stickyTh}>Wh/día</th>
                      <th style={stickyTh}></th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.cargas.map((item, i) => (
                      <tr key={i}>
                        <td>{item.nombre}</td>
                        <td>{item.cantidad}</td>
                        <td>{item.potencia_w} W</td>
                        <td>{Math.round(item.cantidad * item.potencia_w)} W</td>
                        <td>{item.horas} h</td>
                        <td><strong>{Math.round(item.cantidad * item.potencia_w * item.horas)}</strong></td>
                        <td style={{ textAlign: 'right' }}>
                          <button className="btn" style={{ background: 'transparent', color: 'red', padding: '0.2rem' }} onClick={() => handleRemove(i)}>🗑️</button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <div style={{ textAlign: 'right', marginTop: '1rem', color: 'var(--text-secondary)' }}>
                Potencia requerida total: <strong style={{ color: 'var(--primary-color)' }}>{Math.round(totalPotencia)} W</strong>
              </div>
              <div style={{ textAlign: 'right', marginTop: '0.5rem', color: 'var(--text-secondary)' }}>
                Energía diaria total: <strong style={{ color: 'var(--primary-color)' }}>{Math.round(totalEnergia)} Wh/día</strong>
              </div>
            </>
          )}
        </div>

        <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
          <button
            className="btn btn-primary"
            onClick={() => onNext()}
            disabled={data.cargas.length === 0}
            style={{ opacity: data.cargas.length === 0 ? 0.5 : 1, cursor: data.cargas.length === 0 ? 'not-allowed' : 'pointer' }}
          >
            Continuar →
          </button>
        </div>
      </div>
    </div>
  );
}
