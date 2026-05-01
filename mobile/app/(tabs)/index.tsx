import { Ionicons } from '@expo/vector-icons'
import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import {
  ActivityIndicator,
  FlatList,
  RefreshControl,
  ScrollView,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native'
import { SafeAreaView } from 'react-native-safe-area-context'
import { ArticleCard } from '../../components/ui/ArticleCard'
import { ArticleSkeleton } from '../../components/ui/Skeleton'
import { CategoryPill } from '../../components/ui/CategoryPill'
import { Font, Spacing } from '../../constants/theme'
import { useTheme } from '../../context/ThemeContext'
import { useNews } from '../../hooks/useNews'
import { Article, NewsParams } from '../../lib/api'
import { getPreferences, UserPreferences } from '../../lib/preferences'

const ALL_CATEGORIES = ['general', 'tech', 'science', 'health', 'business', 'sports', 'politics', 'environment', 'entertainment', 'gaming', 'crypto']
const ALL_REGIONS    = ['global', 'us', 'uk', 'india', 'australia', 'canada', 'europe', 'middle-east', 'africa', 'latam', 'asia']

export default function FeedScreen() {
  const { colors } = useTheme()
  const [prefs, setPrefs] = useState<UserPreferences | null>(null)

  useEffect(() => {
    getPreferences().then(setPrefs)
  }, [])

  if (!prefs) {
    return (
      <SafeAreaView style={[styles.safe, { backgroundColor: colors.background }]}>
        <FlatList
          data={Array(6).fill(null)}
          keyExtractor={(_, i) => `sk-${i}`}
          renderItem={() => <ArticleSkeleton />}
          contentContainerStyle={styles.list}
          showsVerticalScrollIndicator={false}
        />
      </SafeAreaView>
    )
  }

  return <Feed prefs={prefs} />
}

function Feed({ prefs }: { prefs: UserPreferences }) {
  const { colors, isDark, toggle } = useTheme()

  const [activeCategory, setActiveCategory] = useState<string | undefined>(undefined)
  const [activeRegion,   setActiveRegion  ] = useState<string | undefined>(undefined)

  const hasPrefs = prefs.categories.length > 0 || prefs.regions.some(r => r !== 'global')

  const newsParams = useMemo<NewsParams>(() => {
    const p: NewsParams = {}

    if (activeRegion) {
      p.region = activeRegion
    } else {
      const regions = prefs.regions.filter(r => r !== 'global')
      if (regions.length === 1)      p.region  = regions[0]
      else if (regions.length > 1)   p.regions = regions.join(',')
    }

    if (activeCategory) {
      p.category = activeCategory
    } else if (prefs.categories.length === 1) {
      p.category   = prefs.categories[0]
    } else if (prefs.categories.length > 1) {
      p.categories = prefs.categories.join(',')
    }

    return p
  }, [prefs, activeCategory, activeRegion])

  const {
    data,
    isLoading,
    isError,
    refetch,
    isRefetching,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
  } = useNews(newsParams)

  const articles = useMemo<Article[]>(() => {
    const seen = new Set<number>()
    return (data?.pages.flatMap(p => p) ?? []).filter(a => {
      if (seen.has(a.id)) return false
      seen.add(a.id)
      return true
    })
  }, [data])

  const canLoadMore = useRef(false)
  canLoadMore.current = !!hasNextPage && !isFetchingNextPage

  const onEndReached = useCallback(() => {
    if (canLoadMore.current) fetchNextPage()
  }, [fetchNextPage])

  const ListFooter = useCallback(() => {
    if (!isFetchingNextPage) return null
    return (
      <View style={styles.footerLoader}>
        <ActivityIndicator color={colors.accent} size="small" />
      </View>
    )
  }, [isFetchingNextPage, colors.accent])

  const feedLabel = activeCategory
    ? activeCategory
    : hasPrefs ? 'for you' : 'all'

  const visibleCategories = activeCategory
    ? ALL_CATEGORIES
    : hasPrefs
      ? ['all', ...prefs.categories, ...ALL_CATEGORIES.filter(c => !prefs.categories.includes(c))]
      : ['all', ...ALL_CATEGORIES]

  const visibleRegions = hasPrefs && prefs.regions.some(r => r !== 'global')
    ? ['for you', ...ALL_REGIONS]
    : ALL_REGIONS

  return (
    <SafeAreaView style={[styles.safe, { backgroundColor: colors.background }]}>

      <View style={styles.header}>
        <View>
          <Text style={[styles.logo, { color: colors.accent }]}>verax</Text>
          <Text style={[styles.feedLabel, { color: colors.muted }]}>{feedLabel}</Text>
        </View>
        <TouchableOpacity onPress={toggle} style={styles.themeBtn} activeOpacity={0.7}>
          <Ionicons name={isDark ? 'sunny' : 'moon'} size={20} color={colors.muted} />
        </TouchableOpacity>
      </View>

      <View style={styles.pillWrap}>
        <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.pillRow}>
          {visibleCategories.map(c => {
            const isAll    = c === 'all'
            const isActive = isAll ? !activeCategory : activeCategory === c
            return (
              <CategoryPill
                key={c}
                label={c}
                active={isActive}
                onPress={() => setActiveCategory(isAll || activeCategory === c ? undefined : c)}
              />
            )
          })}
        </ScrollView>
      </View>

      <View style={styles.pillWrap}>
        <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.pillRow}>
          {visibleRegions.map(r => {
            const isForYou = r === 'for you'
            const isActive = isForYou ? !activeRegion : activeRegion === r
            return (
              <CategoryPill
                key={r}
                label={r}
                small
                active={isActive}
                onPress={() => setActiveRegion(isForYou || activeRegion === r ? undefined : r)}
              />
            )
          })}
        </ScrollView>
      </View>

      <View style={[styles.divider, { backgroundColor: colors.border }]} />

      {isLoading ? (
        <FlatList
          data={Array(6).fill(null)}
          keyExtractor={(_, i) => `sk-${i}`}
          renderItem={() => <ArticleSkeleton />}
          contentContainerStyle={styles.list}
          showsVerticalScrollIndicator={false}
        />
      ) : isError ? (
        <View style={styles.center}>
          <Text style={styles.errorIcon}>⚡</Text>
          <Text style={[styles.errorTitle, { color: colors.text }]}>Cannot reach backend</Text>
          <Text style={[styles.errorSub,   { color: colors.muted }]}>Make sure the backend is running on port 8000</Text>
        </View>
      ) : (
        <FlatList
          data={articles}
          keyExtractor={item => String(item.id)}
          renderItem={({ item }) => <ArticleCard article={item} />}
          contentContainerStyle={styles.list}
          showsVerticalScrollIndicator={false}
          onEndReached={onEndReached}
          onEndReachedThreshold={0.2}
          ListFooterComponent={ListFooter}
          refreshControl={
            <RefreshControl refreshing={isRefetching} onRefresh={refetch} tintColor={colors.accent} />
          }
          ListEmptyComponent={
            <View style={styles.center}>
              <Text style={[styles.emptyText, { color: colors.muted }]}>
                No articles yet.{'\n'}Check back in a moment.
              </Text>
            </View>
          }
        />
      )}
    </SafeAreaView>
  )
}

const styles = StyleSheet.create({
  safe:   { flex: 1 },
  header: {
    flexDirection:     'row',
    alignItems:        'center',
    justifyContent:    'space-between',
    paddingHorizontal: Spacing.md,
    paddingTop:        Spacing.sm,
    paddingBottom:     Spacing.sm,
  },
  logo: {
    fontSize:      Font.size.xxl,
    fontWeight:    Font.weight.bold,
    letterSpacing: -1,
  },
  feedLabel: {
    fontSize:      Font.size.xs,
    marginTop:     2,
    letterSpacing: 0.3,
    textTransform: 'uppercase',
  },
  themeBtn: {
    width: 38, height: 38, borderRadius: 19,
    alignItems: 'center', justifyContent: 'center',
  },
  pillWrap: { paddingVertical: Spacing.xs + 2 },
  pillRow:  { paddingHorizontal: Spacing.md, gap: Spacing.xs + 2, alignItems: 'center' },
  divider:  { height: 1, marginHorizontal: Spacing.md, marginBottom: Spacing.xs },
  list:         { paddingTop: Spacing.sm, paddingBottom: Spacing.xl + 20 },
  footerLoader: { paddingVertical: Spacing.lg, alignItems: 'center' },
  center: {
    flex: 1, alignItems: 'center', justifyContent: 'center',
    paddingHorizontal: Spacing.xl, paddingTop: Spacing.xl * 2,
  },
  errorIcon:  { fontSize: 36, marginBottom: Spacing.sm },
  errorTitle: { fontSize: Font.size.lg, fontWeight: Font.weight.semibold, marginBottom: Spacing.xs },
  errorSub:   { fontSize: Font.size.sm, textAlign: 'center' },
  emptyText:  { fontSize: Font.size.md, textAlign: 'center', lineHeight: Font.size.md * 1.6 },
})
