import { useEffect, useState } from 'react';
import { getCurvaS } from '../api/plannerApi';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ReferenceLine } from 'recharts';

export default function CurvaSTab({ proyectoId }) {
  const [datos, setDatos] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getCurvaS(proyectoId).then((r) => { setDatos(r.data); setLoading(false); });
  }, [proyectoId]);

  if (loading) return <p className="pl-empty">Cargando...</p>;

  const chartData = datos.map((d) => ({ fecha: d.fecha, Planificado: d.avance_planificado, Real: d.avance_real }));
  const ult = datos[datos.length - 1];
  const diferencia = ult ? (ult.avance_real - ult.avance_planificado).toFixed(1) : 0;
  const positivo = Number(diferencia) >= 0;

  return (
    <div className="pl-page">
      <div className="pl-between">
        <h2 className="pl-h2">Curva S — Avance Planificado vs Real</h2>
        {datos.length > 0 && (
          <span className="pl-badge" style={positivo ? { background: 'rgba(98,185,137,.18)', color: '#62B989' } : { background: 'rgba(255,138,138,.18)', color: '#ff8a8a' }}>
            {positivo ? '▲' : '▼'} {Math.abs(diferencia)}% vs plan
          </span>
        )}
      </div>

      {datos.length === 0 ? (
        <div className="pl-empty">
          <div className="pl-empty-icon">📈</div>
          <p>Sin datos de Curva S aún.</p>
          <p style={{ fontSize: '.85rem', marginTop: '.25rem' }}>Usa el botón "📸 Snapshot" en la barra superior para registrar el avance de hoy.</p>
        </div>
      ) : (
        <>
          <div className="pl-grid pl-grid-3">
            <div className="pl-kpi" style={{ textAlign: 'center' }}>
              <p className="pl-kpi-label">Snapshots</p>
              <p className="pl-kpi-value">{datos.length}</p>
            </div>
            <div className="pl-kpi" style={{ textAlign: 'center' }}>
              <p className="pl-kpi-label" style={{ color: '#7ab7ff' }}>Último planificado</p>
              <p className="pl-kpi-value" style={{ color: '#7ab7ff' }}>{ult?.avance_planificado}%</p>
            </div>
            <div className="pl-kpi" style={{ textAlign: 'center' }}>
              <p className="pl-kpi-label" style={{ color: 'var(--primary-color)' }}>Último real</p>
              <p className="pl-kpi-value" style={{ color: 'var(--primary-color)' }}>{ult?.avance_real}%</p>
            </div>
          </div>

          <div className="pl-card pl-card-pad">
            <ResponsiveContainer width="100%" height={320}>
              <LineChart data={chartData} margin={{ top: 10, right: 20, left: 0, bottom: 10 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#333" />
                <XAxis dataKey="fecha" tick={{ fontSize: 11, fill: '#a0a0a0' }} stroke="#444" />
                <YAxis domain={[0, 100]} tickFormatter={(v) => `${v}%`} tick={{ fontSize: 11, fill: '#a0a0a0' }} stroke="#444" />
                <Tooltip formatter={(v) => `${v}%`} contentStyle={{ background: '#1e1e1e', border: '1px solid #333', borderRadius: 8, color: '#fff' }} />
                <Legend wrapperStyle={{ fontSize: 12 }} />
                <ReferenceLine y={100} stroke="#444" strokeDasharray="4 4" />
                <Line type="monotone" dataKey="Planificado" stroke="#9ca3af" strokeWidth={2} dot={{ r: 3 }} strokeDasharray="5 5" />
                <Line type="monotone" dataKey="Real" stroke="#62B989" strokeWidth={2.5} dot={{ r: 4 }} activeDot={{ r: 6 }} />
              </LineChart>
            </ResponsiveContainer>
          </div>

          <div className="pl-card" style={{ overflow: 'hidden' }}>
            <table className="pl-table">
              <thead>
                <tr>
                  <th>Fecha</th><th>Planificado</th><th>Real</th><th>Diferencia</th>
                </tr>
              </thead>
              <tbody>
                {[...datos].reverse().map((d) => {
                  const diff = (d.avance_real - d.avance_planificado).toFixed(1);
                  const pos = Number(diff) >= 0;
                  return (
                    <tr key={d.id}>
                      <td>{d.fecha}</td>
                      <td className="pl-muted">{d.avance_planificado}%</td>
                      <td style={{ color: 'var(--primary-color)', fontWeight: 600 }}>{d.avance_real}%</td>
                      <td style={{ color: pos ? '#62B989' : '#ff8a8a', fontWeight: 600 }}>{pos ? '+' : ''}{diff}%</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  );
}
