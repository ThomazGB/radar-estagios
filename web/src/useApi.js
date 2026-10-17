import { useEffect, useState } from 'react'
import { api } from './api.js'

// Loads data from the API whenever `path` or `params` change.
// `reloadKey` lets a component force a new request (e.g. after a POST).
export function useApi(path, params, reloadKey = 0) {
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(true)
  const paramsKey = JSON.stringify(params ?? {})

  useEffect(() => {
    let ignore = false // if the filters change mid-request, drop the old answer
    setLoading(true)
    api(path, { params: JSON.parse(paramsKey) })
      .then((result) => !ignore && (setData(result), setError(null)))
      .catch((err) => !ignore && setError(err.message))
      .finally(() => !ignore && setLoading(false))
    return () => {
      ignore = true
    }
  }, [path, paramsKey, reloadKey]) // dependencies: re-run only when these change

  return { data, error, loading }
}
