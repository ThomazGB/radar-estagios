import { useState } from 'react'
import { api, STATUSES } from './api.js'
import { useApi } from './useApi.js'
import { Status } from './Status.jsx'

export default function Kanban() {
  const [reloadKey, setReloadKey] = useState(0)
  const [error, setError] = useState('')
  const candidaturas = useApi('/candidaturas', null, reloadKey)

  async function change(id, request) {
    try {
      await api(`/candidaturas/${id}`, request)
      setReloadKey((k) => k + 1)
    } catch (err) {
      setError(err.message)
    }
  }

  const move = (id, status) => change(id, { method: 'PATCH', body: { status } })
  const remove = (id) => change(id, { method: 'DELETE' })

  return (
    <section>
      <Status loading={candidaturas.loading} error={candidaturas.error || error} hasData={!!candidaturas.data} />
      {candidaturas.data?.length === 0 && (
        <p className="notice">Nenhuma vaga ainda. Na aba “Vagas”, clique em “+ Adicionar ao kanban”.</p>
      )}
      <div className="kanban">
        {STATUSES.map((column, index) => {
          const cards = candidaturas.data?.filter((c) => c.status === column.id) ?? []
          return (
            <div
              key={column.id}
              className="column"
              onDragOver={(e) => e.preventDefault()}
              onDrop={(e) => move(e.dataTransfer.getData('text/plain'), column.id)}
            >
              <h2>
                {column.label} <span className="muted">{cards.length}</span>
              </h2>
              {cards.map((c) => (
                <article
                  key={c.id}
                  className="card small"
                  draggable
                  onDragStart={(e) => e.dataTransfer.setData('text/plain', c.id)}
                >
                  <a href={c.url} target="_blank" rel="noreferrer" className="title">{c.titulo}</a>
                  <p className="muted">{c.empresa} · {c.regiao}</p>
                  <div className="card-actions">
                    <button disabled={index === 0} onClick={() => move(c.id, STATUSES[index - 1].id)} aria-label="Voltar">←</button>
                    <button disabled={index === STATUSES.length - 1} onClick={() => move(c.id, STATUSES[index + 1].id)} aria-label="Avançar">→</button>
                    <button className="danger" onClick={() => remove(c.id)}>Remover</button>
                  </div>
                </article>
              ))}
            </div>
          )
        })}
      </div>
    </section>
  )
}
