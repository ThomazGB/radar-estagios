import { useState } from 'react'
import { api } from './api.js'
import { useApi } from './useApi.js'
import { Status } from './Status.jsx'

const MODALIDADES = ['remoto', 'hibrido', 'presencial']
const PAGE_SIZE = 30

export default function Vagas() {
  const [filters, setFilters] = useState({ regiao: '', modalidade: '', tecnologia: '', busca: '' })
  const [page, setPage] = useState(0)
  const [reloadKey, setReloadKey] = useState(0)
  const [message, setMessage] = useState('')

  const options = useApi('/filtros')
  const vagas = useApi('/vagas', { ...filters, limit: PAGE_SIZE, offset: page * PAGE_SIZE }, reloadKey)

  function updateFilter(name, value) {
    setFilters({ ...filters, [name]: value })
    setPage(0) // new filter -> back to the first page
  }

  async function addToKanban(vaga) {
    try {
      await api('/candidaturas', { method: 'POST', body: { vaga_id: vaga.id } })
      setMessage(`“${vaga.titulo}” foi para o kanban.`)
      setReloadKey((k) => k + 1)
    } catch (err) {
      setMessage(err.message)
    }
  }

  const total = vagas.data?.total ?? 0
  const lastPage = Math.max(0, Math.ceil(total / PAGE_SIZE) - 1)

  return (
    <section>
      <div className="filters">
        <input
          placeholder="Buscar por título ou empresa"
          value={filters.busca}
          onChange={(e) => updateFilter('busca', e.target.value)}
        />
        <select value={filters.regiao} onChange={(e) => updateFilter('regiao', e.target.value)}>
          <option value="">Todas as regiões</option>
          {options.data?.regioes.map((r) => (
            <option key={r.regiao} value={r.regiao}>
              {r.regiao} ({r.total})
            </option>
          ))}
        </select>
        <select value={filters.modalidade} onChange={(e) => updateFilter('modalidade', e.target.value)}>
          <option value="">Qualquer modalidade</option>
          {MODALIDADES.map((m) => (
            <option key={m} value={m}>
              {m}
            </option>
          ))}
        </select>
        <select value={filters.tecnologia} onChange={(e) => updateFilter('tecnologia', e.target.value)}>
          <option value="">Qualquer tecnologia</option>
          {options.data?.tecnologias.map((t) => (
            <option key={t.tecnologia} value={t.tecnologia}>
              {t.tecnologia} ({t.total})
            </option>
          ))}
        </select>
      </div>

      {message && <p className="notice" onClick={() => setMessage('')}>{message}</p>}
      <Status loading={vagas.loading} error={vagas.error} hasData={!!vagas.data} />

      {vagas.data && (
        <>
          <p className="muted">{total} vagas encontradas</p>
          <ul className="cards">
            {vagas.data.itens.map((vaga) => (
              <li key={vaga.id} className="card">
                <div className="card-top">
                  {vaga.logo_url && <img src={vaga.logo_url} alt="" className="logo" />}
                  <div>
                    <a href={vaga.url} target="_blank" rel="noreferrer" className="title">
                      {vaga.titulo}
                    </a>
                    <p className="muted">
                      {vaga.empresa} · {vaga.cidade ?? 'cidade não informada'}
                    </p>
                  </div>
                </div>
                <div className="chips">
                  <span className="chip strong">{vaga.regiao}</span>
                  <span className="chip">{vaga.modalidade}</span>
                  {vaga.bolsa && <span className="chip">R$ {Number(vaga.bolsa).toLocaleString('pt-BR')}</span>}
                  {vaga.tecnologias.map((t) => (
                    <span key={t} className="chip tech">{t}</span>
                  ))}
                </div>
                <div className="card-actions">
                  {vaga.candidatura_status ? (
                    <span className="muted">No kanban: {vaga.candidatura_status}</span>
                  ) : (
                    <button onClick={() => addToKanban(vaga)}>+ Adicionar ao kanban</button>
                  )}
                </div>
              </li>
            ))}
          </ul>
          <div className="pager">
            <button disabled={page === 0} onClick={() => setPage(page - 1)}>← Anterior</button>
            <span className="muted">Página {page + 1} de {lastPage + 1}</span>
            <button disabled={page >= lastPage} onClick={() => setPage(page + 1)}>Próxima →</button>
          </div>
        </>
      )}
    </section>
  )
}
