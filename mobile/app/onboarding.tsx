import { Ionicons } from '@expo/vector-icons'
import { router } from 'expo-router'
import React, { useState } from 'react'
import {
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native'
import { SafeAreaView } from 'react-native-safe-area-context'
import { Font, Radius, Spacing } from '../constants/theme'
import { useTheme } from '../context/ThemeContext'
import { savePreferences } from '../lib/preferences'

const REGIONS = [
  { id: 'global',      label: 'Global',         emoji: '🌍', desc: 'World coverage'    },
  { id: 'us',          label: 'United States',  emoji: '🇺🇸', desc: 'American news'     },
  { id: 'uk',          label: 'United Kingdom', emoji: '🇬🇧', desc: 'British news'      },
  { id: 'india',       label: 'India',          emoji: '🇮🇳', desc: 'Indian news'       },
  { id: 'australia',   label: 'Australia',      emoji: '🇦🇺', desc: 'Australian news'   },
  { id: 'canada',      label: 'Canada',         emoji: '🇨🇦', desc: 'Canadian news'     },
  { id: 'europe',      label: 'Europe',         emoji: '🇪🇺', desc: 'European news'     },
  { id: 'middle-east', label: 'Middle East',    emoji: '🕌', desc: 'Regional coverage' },
  { id: 'africa',      label: 'Africa',         emoji: '🌍', desc: 'African news'      },
  { id: 'latam',       label: 'Latin America',  emoji: '🌎', desc: 'LatAm coverage'    },
  { id: 'asia',        label: 'Asia Pacific',   emoji: '🌏', desc: 'Asian news'        },
]

const TOPICS = [
  { id: 'general',      label: 'General',      emoji: '📰', color: '#6b7280' },
  { id: 'tech',         label: 'Tech',         emoji: '💻', color: '#6366f1' },
  { id: 'science',      label: 'Science',      emoji: '🔬', color: '#06b6d4' },
  { id: 'health',       label: 'Health',       emoji: '🏥', color: '#10b981' },
  { id: 'business',     label: 'Business',     emoji: '💼', color: '#8b5cf6' },
  { id: 'sports',       label: 'Sports',       emoji: '⚽', color: '#f59e0b' },
  { id: 'politics',     label: 'Politics',     emoji: '🗳️',  color: '#ef4444' },
  { id: 'environment',  label: 'Environment',  emoji: '🌱', color: '#84cc16' },
  { id: 'entertainment',label: 'Entertainment',emoji: '🎬', color: '#ec4899' },
  { id: 'gaming',       label: 'Gaming',       emoji: '🎮', color: '#a855f7' },
  { id: 'crypto',       label: 'Crypto',       emoji: '₿',  color: '#f97316' },
]

export default function OnboardingScreen() {
  const { colors, isDark } = useTheme()
  const [step,            setStep           ] = useState(0)
  const [selectedRegions, setSelectedRegions] = useState<string[]>(['global'])
  const [selectedTopics,  setSelectedTopics ] = useState<string[]>([])

  const toggleRegion = (id: string) =>
    setSelectedRegions(prev =>
      prev.includes(id)
        ? prev.length > 1 ? prev.filter(r => r !== id) : prev
        : [...prev, id]
    )

  const toggleTopic = (id: string) =>
    setSelectedTopics(prev =>
      prev.includes(id) ? prev.filter(t => t !== id) : [...prev, id]
    )

  const finish = async () => {
    await savePreferences({ regions: selectedRegions, categories: selectedTopics })
    router.replace('/(tabs)')
  }

  const bg = { backgroundColor: colors.background }

  return (
    <SafeAreaView style={[styles.safe, bg]}>

      {/* ── Progress bar ── */}
      {step > 0 && (
        <View style={[styles.progressTrack, { backgroundColor: colors.border }]}>
          <View style={[styles.progressFill, { backgroundColor: colors.accent, width: step === 1 ? '50%' : '100%' }]} />
        </View>
      )}

      {/* ── Top nav ── */}
      <View style={styles.topNav}>
        {step > 0
          ? <TouchableOpacity onPress={() => setStep(s => s - 1)} style={styles.navBtn}>
              <Ionicons name="arrow-back" size={22} color={colors.text} />
            </TouchableOpacity>
          : <View style={styles.navBtn} />
        }
        {step > 0 && (
          <Text style={[styles.stepLabel, { color: colors.muted }]}>
            Step {step} of 2
          </Text>
        )}
        {step > 0
          ? <TouchableOpacity onPress={finish} style={styles.navBtn}>
              <Text style={[styles.skipLabel, { color: colors.muted }]}>Skip</Text>
            </TouchableOpacity>
          : <View style={styles.navBtn} />
        }
      </View>

      {/* ══════════════════════════════════════════════════
          STEP 0 — Welcome
      ══════════════════════════════════════════════════ */}
      {step === 0 && (
        <View style={styles.welcomeBody}>
          <View style={styles.logoWrap}>
            <Text style={[styles.logoText, { color: colors.accent }]}>verax</Text>
            <View style={[styles.logoDot, { backgroundColor: colors.accent }]} />
          </View>

          <Text style={[styles.welcomeTitle, { color: colors.text }]}>
            News that{'\n'}thinks for itself.
          </Text>
          <Text style={[styles.welcomeSub, { color: colors.muted }]}>
            AI-summarised, bias-detected, open source.{'\n'}No ads. No algorithms. Just the truth.
          </Text>

          <View style={styles.pillsPreview}>
            {['Tech', 'Politics', 'Science', 'Sports', 'Crypto'].map(t => (
              <View key={t} style={[styles.previewPill, { backgroundColor: colors.card, borderColor: colors.border }]}>
                <Text style={[styles.previewPillText, { color: colors.muted }]}>{t}</Text>
              </View>
            ))}
          </View>
        </View>
      )}

      {/* ══════════════════════════════════════════════════
          STEP 1 — Regions
      ══════════════════════════════════════════════════ */}
      {step === 1 && (
        <>
          <View style={styles.header}>
            <Text style={[styles.title, { color: colors.text }]}>
              Where do you want{'\n'}news from?
            </Text>
            <Text style={[styles.subtitle, { color: colors.muted }]}>
              Pick one or more — you can change this in Settings
            </Text>
          </View>

          <ScrollView
            style={styles.scrollArea}
            showsVerticalScrollIndicator={false}
            contentContainerStyle={styles.regionGrid}
          >
            {REGIONS.map(r => {
              const active = selectedRegions.includes(r.id)
              return (
                <Pressable
                  key={r.id}
                  onPress={() => toggleRegion(r.id)}
                  style={[
                    styles.regionCard,
                    {
                      backgroundColor: active ? colors.accent + '15' : colors.card,
                      borderColor:     active ? colors.accent : colors.border,
                    },
                  ]}
                >
                  {active && (
                    <View style={[styles.checkBadge, { backgroundColor: colors.accent }]}>
                      <Ionicons name="checkmark" size={10} color="#1a1a2e" />
                    </View>
                  )}
                  <Text style={styles.regionEmoji}>{r.emoji}</Text>
                  <Text style={[styles.regionLabel, { color: colors.text }]}>{r.label}</Text>
                  <Text style={[styles.regionDesc,  { color: colors.muted }]}>{r.desc}</Text>
                </Pressable>
              )
            })}
          </ScrollView>
        </>
      )}

      {/* ══════════════════════════════════════════════════
          STEP 2 — Topics
      ══════════════════════════════════════════════════ */}
      {step === 2 && (
        <>
          <View style={styles.header}>
            <Text style={[styles.title, { color: colors.text }]}>
              What do you{'\n'}care about?
            </Text>
            <Text style={[styles.subtitle, { color: colors.muted }]}>
              Pick topics — or skip to see everything
            </Text>
          </View>

          <ScrollView
            style={styles.scrollArea}
            showsVerticalScrollIndicator={false}
            contentContainerStyle={styles.topicsWrap}
          >
            {TOPICS.map(t => {
              const active = selectedTopics.includes(t.id)
              return (
                <Pressable
                  key={t.id}
                  onPress={() => toggleTopic(t.id)}
                  style={[
                    styles.topicChip,
                    {
                      backgroundColor: active ? t.color + '20' : colors.card,
                      borderColor:     active ? t.color : colors.border,
                    },
                  ]}
                >
                  <Text style={styles.topicEmoji}>{t.emoji}</Text>
                  <Text style={[styles.topicLabel, { color: active ? t.color : colors.text }]}>
                    {t.label}
                  </Text>
                  {active && <Ionicons name="checkmark-circle" size={14} color={t.color} />}
                </Pressable>
              )
            })}
          </ScrollView>
        </>
      )}

      {/* ── CTA ── */}
      <View style={[styles.footer, { borderTopColor: step === 0 ? 'transparent' : colors.border }]}>
        {step === 0 ? (
          <TouchableOpacity
            onPress={() => setStep(1)}
            activeOpacity={0.85}
            style={[styles.cta, { backgroundColor: colors.accent }]}
          >
            <Text style={styles.ctaText}>Get started</Text>
            <Ionicons name="arrow-forward" size={18} color="#1a1a2e" />
          </TouchableOpacity>
        ) : step === 1 ? (
          <TouchableOpacity
            onPress={() => setStep(2)}
            activeOpacity={0.85}
            style={[styles.cta, { backgroundColor: colors.accent }]}
          >
            <Text style={styles.ctaText}>Choose my topics</Text>
            <Ionicons name="arrow-forward" size={18} color="#1a1a2e" />
          </TouchableOpacity>
        ) : (
          <TouchableOpacity
            onPress={finish}
            activeOpacity={0.85}
            style={[styles.cta, { backgroundColor: colors.accent }]}
          >
            <Text style={styles.ctaText}>Build my feed</Text>
            <Ionicons name="sparkles-outline" size={18} color="#1a1a2e" />
          </TouchableOpacity>
        )}
      </View>

    </SafeAreaView>
  )
}

const styles = StyleSheet.create({
  safe: { flex: 1 },

  progressTrack: {
    height: 3,
    marginHorizontal: Spacing.md,
    borderRadius: 2,
    marginTop: Spacing.xs,
  },
  progressFill: {
    height: 3,
    borderRadius: 2,
  },

  topNav: {
    flexDirection:     'row',
    alignItems:        'center',
    justifyContent:    'space-between',
    paddingHorizontal: Spacing.md,
    paddingVertical:   Spacing.sm,
  },
  navBtn:    { width: 44, height: 36, alignItems: 'center', justifyContent: 'center' },
  stepLabel: { fontSize: Font.size.sm, fontWeight: Font.weight.medium },
  skipLabel: { fontSize: Font.size.sm },

  welcomeBody: {
    flex:              1,
    alignItems:        'center',
    justifyContent:    'center',
    paddingHorizontal: Spacing.xl,
    gap:               Spacing.lg,
  },
  logoWrap: {
    flexDirection: 'row',
    alignItems:    'flex-end',
    gap:           4,
    marginBottom:  Spacing.sm,
  },
  logoText: {
    fontSize:      42,
    fontWeight:    '800',
    letterSpacing: -2,
  },
  logoDot: {
    width:        8,
    height:       8,
    borderRadius: 4,
    marginBottom: 10,
  },
  welcomeTitle: {
    fontSize:   Font.size.xxl + 4,
    fontWeight: Font.weight.bold,
    textAlign:  'center',
    lineHeight: (Font.size.xxl + 4) * 1.2,
  },
  welcomeSub: {
    fontSize:   Font.size.sm,
    textAlign:  'center',
    lineHeight: Font.size.sm * 1.7,
  },
  pillsPreview: {
    flexDirection: 'row',
    flexWrap:      'wrap',
    gap:           8,
    justifyContent:'center',
    marginTop:     Spacing.sm,
  },
  previewPill: {
    paddingVertical:   6,
    paddingHorizontal: 12,
    borderRadius:      Radius.full,
    borderWidth:       1,
  },
  previewPillText: { fontSize: Font.size.xs, fontWeight: Font.weight.medium },

  header: {
    paddingHorizontal: Spacing.md,
    paddingBottom:     Spacing.md,
  },
  title: {
    fontSize:     Font.size.xxl,
    fontWeight:   Font.weight.bold,
    lineHeight:   Font.size.xxl * 1.2,
    marginBottom: Spacing.xs,
  },
  subtitle: {
    fontSize:   Font.size.sm,
    lineHeight: Font.size.sm * 1.5,
  },

  scrollArea: { flex: 1 },

  regionGrid: {
    flexDirection:     'row',
    flexWrap:          'wrap',
    gap:               10,
    paddingHorizontal: Spacing.md,
    paddingBottom:     Spacing.xl,
  },
  regionCard: {
    width:          '47%',
    borderRadius:   Radius.lg,
    borderWidth:    1.5,
    padding:        Spacing.md,
    alignItems:     'center',
    paddingTop:     Spacing.lg,
    position:       'relative',
  },
  checkBadge: {
    position:       'absolute',
    top:            10,
    right:          10,
    width:          20,
    height:         20,
    borderRadius:   10,
    alignItems:     'center',
    justifyContent: 'center',
  },
  regionEmoji: { fontSize: 32, marginBottom: Spacing.sm },
  regionLabel: { fontSize: Font.size.sm, fontWeight: Font.weight.semibold, textAlign: 'center' },
  regionDesc:  { fontSize: Font.size.xs, marginTop: 2, textAlign: 'center' },

  topicsWrap: {
    flexDirection:     'row',
    flexWrap:          'wrap',
    gap:               10,
    paddingHorizontal: Spacing.md,
    paddingBottom:     Spacing.xl,
  },
  topicChip: {
    flexDirection:     'row',
    alignItems:        'center',
    gap:               6,
    paddingVertical:   10,
    paddingHorizontal: 14,
    borderRadius:      Radius.full,
    borderWidth:       1.5,
  },
  topicEmoji: { fontSize: 15 },
  topicLabel: { fontSize: Font.size.sm, fontWeight: Font.weight.medium },

  footer: {
    paddingHorizontal: Spacing.md,
    paddingTop:        Spacing.md,
    paddingBottom:     Spacing.lg,
    borderTopWidth:    1,
  },
  cta: {
    flexDirection:   'row',
    alignItems:      'center',
    justifyContent:  'center',
    gap:             8,
    borderRadius:    Radius.full,
    paddingVertical: 15,
  },
  ctaText: {
    fontSize:   Font.size.md,
    fontWeight: Font.weight.bold,
    color:      '#1a1a2e',
  },
})
