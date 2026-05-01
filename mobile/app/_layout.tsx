import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { Stack } from 'expo-router'
import * as SplashScreen from 'expo-splash-screen'
import { StatusBar } from 'expo-status-bar'
import React, { useEffect, useState } from 'react'
import { SafeAreaProvider } from 'react-native-safe-area-context'
import { ThemeProvider, useTheme } from '../context/ThemeContext'
import { isOnboardingDone } from '../lib/preferences'

SplashScreen.preventAutoHideAsync()

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: 2, staleTime: 5 * 60 * 1000 } },
})

function AppShell({ initialRoute }: { initialRoute: string }) {
  const { isDark } = useTheme()

  useEffect(() => {
    SplashScreen.hideAsync()
  }, [])

  return (
    <>
      <StatusBar style={isDark ? 'light' : 'dark'} backgroundColor="transparent" translucent />
      <Stack initialRouteName={initialRoute} screenOptions={{ headerShown: false }} />
    </>
  )
}

export default function RootLayout() {
  const [initialRoute, setInitialRoute] = useState<string | null>(null)

  useEffect(() => {
    isOnboardingDone().then(done => {
      setInitialRoute(done ? '(tabs)' : 'onboarding')
    })
  }, [])

  if (initialRoute === null) return null

  return (
    <SafeAreaProvider>
      <QueryClientProvider client={queryClient}>
        <ThemeProvider>
          <AppShell initialRoute={initialRoute} />
        </ThemeProvider>
      </QueryClientProvider>
    </SafeAreaProvider>
  )
}
