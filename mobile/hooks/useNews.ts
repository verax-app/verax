import { useInfiniteQuery, useQuery } from '@tanstack/react-query'
import { api, NewsParams, PageCursor, RecommendedParams } from '../lib/api'

const PAGE_SIZE = 20

export function useNews(params: NewsParams = {}, options?: { enabled?: boolean }) {
  return useInfiniteQuery({
    queryKey:  ['news', params],
    enabled:   options?.enabled ?? true,
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

export function useRecommendedNews(params: RecommendedParams = {}, options?: { enabled?: boolean }) {
  return useInfiniteQuery({
    queryKey:  ['news', 'recommended', params],
    enabled:   options?.enabled ?? true,
    queryFn:   ({ pageParam = 0 }: { pageParam: number }) =>
      api.news.recommended({ ...params, offset: pageParam, limit: PAGE_SIZE }),
    initialPageParam: 0 as number,
    getNextPageParam: (lastPage, _allPages, lastPageParam) => {
      if (lastPage.length < PAGE_SIZE) return undefined
      // Advance by the exact count returned, not total loaded, so cache
      // rebuilds mid-session don't misalign the offset.
      return (lastPageParam as number) + lastPage.length
    },
    staleTime: 2 * 60 * 1000,
  })
}

export function useArticle(id: number) {
  return useQuery({
    queryKey: ['article', id],
    queryFn:  () => api.news.detail(id),
    staleTime: 10 * 60 * 1000,
  })
}
