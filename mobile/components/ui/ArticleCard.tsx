import { useRouter } from 'expo-router'
import React from 'react'
import { Dimensions, StyleSheet, Text, TouchableOpacity, View } from 'react-native'
import { Font, Spacing } from '../../constants/theme'
import { useTheme } from '../../context/ThemeContext'
import { Article } from '../../lib/api'
import { BiasTag } from './BiasTag'

const CARD_W = Dimensions.get('window').width - Spacing.md * 2

interface Props { article: Article }

function timeAgo(iso: string | null | undefined) {
  if (!iso) return ''
  // Backend returns naive UTC strings without a timezone suffix.
  // Appending Z tells JS to parse them as UTC instead of local time.
  const utc = iso.endsWith('Z') || iso.includes('+') ? iso : iso + 'Z'
  const h = Math.floor((Date.now() - new Date(utc).getTime()) / 3_600_000)
  if (h < 1) return 'Just now'
  if (h < 24) return `${h}h ago`
  return `${Math.floor(h / 24)}d ago`
}

export function ArticleCard({ article }: Props) {
  const router    = useRouter()
  const { colors } = useTheme()
  const catColor  = colors.category[article.category] ?? colors.muted

  return (
    <TouchableOpacity
      style={[styles.card, { backgroundColor: colors.card }]}
      activeOpacity={0.8}
      onPress={() => router.push(`/article/${article.id}`)}
    >
      {/* Left accent bar */}
      <View style={[styles.accent, { backgroundColor: catColor }]} />

      <View style={styles.body}>
        {/* Source row */}
        <View style={styles.sourceRow}>
          <View style={[styles.catDot, { backgroundColor: catColor }]} />
          <Text style={[styles.sourceName, { color: colors.muted }]} numberOfLines={1}>
            {article.source_name}
          </Text>
          <Text style={[styles.dot, { color: colors.border }]}> · </Text>
          <Text style={[styles.category, { color: colors.muted }]}>
            {article.category.charAt(0).toUpperCase() + article.category.slice(1)}
          </Text>
          <BiasTag bias={article.bias} confidence={article.bias_confidence} />
        </View>

        {/* Title */}
        <Text style={[styles.title, { color: colors.text }]} numberOfLines={2}>
          {article.title}
        </Text>

        {/* Summary */}
        {article.summary ? (
          <Text style={[styles.summary, { color: colors.muted }]} numberOfLines={3}>
            {article.summary}
          </Text>
        ) : (
          <Text style={[styles.pending, { color: colors.border }]}>Summarizing with AI…</Text>
        )}

        {/* Footer */}
        <View style={styles.footer}>
          <Text style={[styles.time, { color: colors.muted }]}>{timeAgo(article.published_at ?? article.created_at)}</Text>
          <Text style={[styles.readTime, { color: colors.muted }]}>
            {Math.ceil(article.read_time / 60)} min read
          </Text>
        </View>
      </View>
    </TouchableOpacity>
  )
}

const styles = StyleSheet.create({
  card: {
    width:         CARD_W,
    alignSelf:     'center',
    borderRadius:  14,
    marginBottom:  10,
    flexDirection: 'row',
    overflow:      'hidden',
    shadowColor:   '#000',
    shadowOffset:  { width: 0, height: 1 },
    shadowOpacity: 0.07,
    shadowRadius:  4,
    elevation:     2,
  },
  accent: {
    width:        4,
    borderRadius: 0,
  },
  body: {
    flex:    1,
    padding: 14,
    gap:     6,
  },
  sourceRow: {
    flexDirection: 'row',
    alignItems:    'center',
    gap:           4,
    flexWrap:      'nowrap',
  },
  catDot: {
    width: 6, height: 6, borderRadius: 3, flexShrink: 0,
  },
  sourceName: {
    fontSize:   Font.size.xs,
    fontWeight: '600',
    flexShrink: 1,
    maxWidth:   '35%',
  },
  dot: {
    fontSize: Font.size.xs,
  },
  category: {
    fontSize:   Font.size.xs,
    fontWeight: '600',
    flexShrink: 0,
  },
  title: {
    fontSize:      Font.size.lg,
    fontWeight:    '700',
    lineHeight:    Font.size.lg * 1.35,
    letterSpacing: -0.3,
  },
  summary: {
    fontSize:   Font.size.sm,
    lineHeight: Font.size.sm * 1.6,
  },
  pending: {
    fontSize:  Font.size.xs,
    fontStyle: 'italic',
  },
  footer: {
    flexDirection:  'row',
    justifyContent: 'space-between',
    alignItems:     'center',
    marginTop:      2,
  },
  time: {
    fontSize: Font.size.xs,
  },
  readTime: {
    fontSize:   Font.size.xs,
    fontWeight: '500',
  },
})
