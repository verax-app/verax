import { Ionicons } from '@expo/vector-icons'
import React, { useCallback, useMemo, useRef, useState } from 'react'
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
import { Article } from '../../lib/api'

const CATEGORIES = ['general', 'tech', 'science', 'health', 'sports', 'politics', 'business']
const REGIONS    = ['global', 'india', 'us', 'uk']

export default function FeedScreen() {
  const { colors, isDark, toggle } = useTheme()
  const [category, setCategory] = useState<string | undefined>(undefined)
  const [region,   setRegion  ] = useState('global')

  const {
    data,
    isLoading,
    isError,
    refetch,
    isRefetching,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
  } = useNews({ category, region })

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

  return (
    <SafeAreaView style={[styles.safe, { backgroundColor: colors.background }]}>

      {/* ── Header ── */}
      <View style={[styles.header, { backgroundColor: colors.background }]}>
        <View>
          <Text style={[styles.logo, { color: colors.accent }]}>verax</Text>
          <Text style={[styles.tagline, { color: colors.muted }]}>The truth-teller.</Text>
        </View>
        <TouchableOpacity onPress={toggle} style={styles.themeBtn} activeOpacity={0.7}>
          <Ionicons
            name={isDark ? 'sunny' : 'moon'}
            size={20}
            color={colors.muted}
          />
        </TouchableOpacity>
      </View>

      {/* ── Category pills ── */}
      <View style={styles.pillWrap}>
        <ScrollView
          horizontal
          showsHorizontalScrollIndicator={false}
          contentContainerStyle={styles.pillRow}
        >
          <CategoryPill label="all" active={!category} onPress={() => setCategory(undefined)} />
          {CATEGORIES.map(c => (
            <CategoryPill
              key={c}
              label={c}
              active={category === c}
              onPress={() => setCategory(c === category ? undefined : c)}
            />
          ))}
        </ScrollView>
      </View>

      {/* ── Region pills ── */}
      <View style={styles.pillWrap}>
        <ScrollView
          horizontal
          showsHorizontalScrollIndicator={false}
          contentContainerStyle={styles.pillRow}
        >
          {REGIONS.map(r => (
            <CategoryPill
              key={r}
              label={r}
              small
              active={region === r}
              onPress={() => setRegion(r)}
            />
          ))}
        </ScrollView>
      </View>

      {/* ── Divider ── */}
      <View style={[styles.divider, { backgroundColor: colors.border }]} />

      {/* ── Feed ── */}
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
          <Text style={[styles.errorSub, { color: colors.muted }]}>Make sure the backend is running on port 8000</Text>
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
            <RefreshControl
              refreshing={isRefetching}
              onRefresh={refetch}
              tintColor={colors.accent}
            />
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
  safe: {
    flex: 1,
  },
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
  tagline: {
    fontSize:      Font.size.xs,
    marginTop:     2,
    letterSpacing: 0.1,
  },
  themeBtn: {
    width:          38,
    height:         38,
    borderRadius:   19,
    alignItems:     'center',
    justifyContent: 'center',
  },
  pillWrap: {
    paddingVertical: Spacing.xs + 2,
  },
  pillRow: {
    paddingHorizontal: Spacing.md,
    gap:               Spacing.xs + 2,
    alignItems:        'center',
  },
  divider: {
    height:          1,
    marginHorizontal: Spacing.md,
    marginBottom:    Spacing.xs,
  },
  list: {
    paddingTop:    Spacing.sm,
    paddingBottom: Spacing.xl + 20,
  },
  footerLoader: {
    paddingVertical: Spacing.lg,
    alignItems:      'center',
  },
  center: {
    flex:              1,
    alignItems:        'center',
    justifyContent:    'center',
    paddingHorizontal: Spacing.xl,
    paddingTop:        Spacing.xl * 2,
  },
  errorIcon: {
    fontSize:     36,
    marginBottom: Spacing.sm,
  },
  errorTitle: {
    fontSize:     Font.size.lg,
    fontWeight:   Font.weight.semibold,
    marginBottom: Spacing.xs,
  },
  errorSub: {
    fontSize:  Font.size.sm,
    textAlign: 'center',
  },
  emptyText: {
    fontSize:   Font.size.md,
    textAlign:  'center',
    lineHeight: Font.size.md * 1.6,
  },
})
