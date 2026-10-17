import { useApi } from './useApi.js'
import { Status } from './Status.jsx'

// Horizontal bar chart made with plain CSS: each bar's width is its share of the biggest value
function BarChart({ title, items, format = (v) => v }) {
  const max = Math.max(1, ...items.map((i) => Number(i.total)))
  return (
    <div className="chart">
      <h2>{title}</h2>
      {items.length === 0 && <p className="muted">Sem dados ainda.</p>}
      {items.map((item) => (
        <div key={item.nome} className="bar-row">
          <span className="bar-label">{item.nome}</span>
          <div className="bar-track">
            <div className="bar" style={{ width: `${(Number(item.total) / max) * 100}%` }} />
          </div>
          <span className="bar-value">{format(item.total)}</span>
        </div>
      ))}
    </div>
  )
}

export default function Estatisticas() {
  const { data, loading, error } = useApi('/estatisticas')
  const money = (v) => `R$ ${Number(v).toLocaleString('pt-BR')}`

  return (
    <section>
      <Status loading={loading} error={error} hasData={!!data} />
      {data && (
        <>
          <p className="big-number">{data.total_vagas} <span className="muted">vagas no radar</span></p>
          <div className="charts">
            <BarChart title="Vagas por região" items={data.por_regiao} />
            <BarChart title="Tecnologias mais pedidas" items={data.top_tecnologias} />
            <BarChart title="Modalidade" items={data.por_modalidade} />
            <BarChart title="Bolsa média por região" items={data.bolsa_media_por_regiao} format={money} />
            <BarChart title="Minhas candidaturas" items={data.candidaturas_por_status} />
          </div>
        </>
      )}
    </section>
  )
}
