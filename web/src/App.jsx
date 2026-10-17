import { useState } from 'react'
import Vagas from './Vagas.jsx'
import Kanban from './Kanban.jsx'
import Estatisticas from './Estatisticas.jsx'

const TABS = [
  { id: 'vagas', label: 'Vagas', Component: Vagas },
  { id: 'kanban', label: 'Minhas candidaturas', Component: Kanban },
  { id: 'stats', label: 'Estatísticas', Component: Estatisticas },
]

export default function App() {
  const [tab, setTab] = useState('vagas')
  const { Component } = TABS.find((t) => t.id === tab)

  return (
    <div className="app">
      <header className="header">
        <h1>Radar de Estágios</h1>
        <p className="muted">Vagas de estágio em tecnologia: remoto e região oeste de SP</p>
        <nav className="tabs">
          {TABS.map((t) => (
            <button
              key={t.id}
              className={t.id === tab ? 'tab active' : 'tab'}
              onClick={() => setTab(t.id)}
            >
              {t.label}
            </button>
          ))}
        </nav>
      </header>
      <main>
        <Component />
      </main>
    </div>
  )
}
