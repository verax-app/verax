import { useInfiniteQuery, useQuery } from '@tanstack/react-query'
import { api, NewsParams, PageCursor } from '../lib/api'

const PAGE_SIZE = 15

export function useNews(params: NewsParams = {}) {
  return useInfiniteQuery({
    queryKey:  ['news', params],
    queryFn:   ({ pageParam }: { pageParam: PageCursor | undefined }) =>
      api.news.list({ ...params, ...pageParam, limit: PAGE_SIZE }),
    initialPageParam: undefined as PageCursor | undefined,
    getNextPageParam: (lastPage) => {
      if (lastPage.length < PAGE_SIZE) return undefined
      const last = lastPage[lastPage.length - 1]
      return {
        before_ts: last.published_at ?? last.created_at,
        before_id: last.id,
      }
    },
    staleTime: 5 * 60 * 1000,
  })
}

export function useArticle(id: number) {
  return useQuery({
    queryKey: ['article', id],
    queryFn:  () => api.news.detail(id),
    staleTime: 10 * 60 * 1000,
  })
}
