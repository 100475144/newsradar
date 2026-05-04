import { request } from './client'

export function getGlobalStats() {
  return request('/stats/global')
}
