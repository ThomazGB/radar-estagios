// Loading / error messages shared by every screen
export function Status({ loading, error, hasData }) {
  if (error) return <p className="notice error">Não consegui falar com a API: {error}</p>
  if (loading && !hasData) {
    return (
      <p className="notice">
        Carregando… Na primeira visita a API pode levar até 1 minuto para “acordar” (plano grátis do Render).
      </p>
    )
  }
  return null
}
