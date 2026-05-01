import AsyncStorage from '@react-native-async-storage/async-storage'

const KEYS = {
  DONE:       '@verax/onboarding_done',
  REGIONS:    '@verax/preferred_regions',
  CATEGORIES: '@verax/preferred_categories',
}

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
