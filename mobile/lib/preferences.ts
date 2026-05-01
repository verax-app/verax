import AsyncStorage from '@react-native-async-storage/async-storage'

const KEYS = {
  DONE:           '@verax/onboarding_done',
  REGIONS:        '@verax/preferred_regions',
  CATEGORIES:     '@verax/preferred_categories',
  VIEWED:         '@verax/viewed_ids',
  VIEWED_AUTHORS: '@verax/viewed_authors',
}

const MAX_VIEWED         = 50
const MAX_VIEWED_AUTHORS = 30

export interface UserPreferences {
  regions:    string[]
  categories: string[]
}

export async function isOnboardingDone(): Promise<boolean> {
  return !!(await AsyncStorage.getItem(KEYS.DONE))
}

export async function getPreferences(): Promise<UserPreferences> {
  const [regions, categories] = await Promise.all([
    AsyncStorage.getItem(KEYS.REGIONS),
    AsyncStorage.getItem(KEYS.CATEGORIES),
  ])
  return {
    regions:    regions    ? JSON.parse(regions)    : ['global'],
    categories: categories ? JSON.parse(categories) : [],
  }
}

export async function savePreferences(prefs: UserPreferences): Promise<void> {
  await Promise.all([
    AsyncStorage.setItem(KEYS.DONE,       'true'),
    AsyncStorage.setItem(KEYS.REGIONS,    JSON.stringify(prefs.regions)),
    AsyncStorage.setItem(KEYS.CATEGORIES, JSON.stringify(prefs.categories)),
  ])
}

export async function getViewedIds(): Promise<number[]> {
  const raw = await AsyncStorage.getItem(KEYS.VIEWED)
  return raw ? JSON.parse(raw) : []
}

export async function recordView(articleId: number, author?: string | null): Promise<void> {
  const [rawIds, rawAuthors] = await Promise.all([
    AsyncStorage.getItem(KEYS.VIEWED),
    AsyncStorage.getItem(KEYS.VIEWED_AUTHORS),
  ])

  const ids: number[] = rawIds ? JSON.parse(rawIds) : []
  const updatedIds = [articleId, ...ids.filter(id => id !== articleId)].slice(0, MAX_VIEWED)

  const saves: Promise<void>[] = [
    AsyncStorage.setItem(KEYS.VIEWED, JSON.stringify(updatedIds)),
  ]

  if (author) {
    const authors: string[] = rawAuthors ? JSON.parse(rawAuthors) : []
    const updatedAuthors = [author, ...authors.filter(a => a !== author)].slice(0, MAX_VIEWED_AUTHORS)
    saves.push(AsyncStorage.setItem(KEYS.VIEWED_AUTHORS, JSON.stringify(updatedAuthors)))
  }

  await Promise.all(saves)
}

export async function getViewedAuthors(): Promise<string[]> {
  const raw = await AsyncStorage.getItem(KEYS.VIEWED_AUTHORS)
  return raw ? JSON.parse(raw) : []
}
