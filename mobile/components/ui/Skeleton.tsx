import React, { useEffect, useRef } from 'react'
import { Animated, DimensionValue, StyleSheet, View, ViewStyle } from 'react-native'
import { Radius } from '../../constants/theme'
import { useTheme } from '../../context/ThemeContext'

interface Props {
  width?:  DimensionValue
  height?: number
  radius?: number
  style?:  ViewStyle
}

export function Skeleton({ width = '100%', height = 16, radius = Radius.sm, style }: Props) {
  const { colors } = useTheme()
  const opacity = useRef(new Animated.Value(0.4)).current

  useEffect(() => {
    Animated.loop(
      Animated.sequence([
        Animated.timing(opacity, { toValue: 1,   duration: 800, useNativeDriver: true }),
        Animated.timing(opacity, { toValue: 0.4, duration: 800, useNativeDriver: true }),
      ])
    ).start()
  }, [])

  return (
    <Animated.View
      style={[{ width, height, borderRadius: radius, backgroundColor: colors.border, opacity }, style]}
    />
  )
}

export function ArticleSkeleton() {
  const { colors } = useTheme()
  return (
    <View style={[styles.card, { backgroundColor: colors.card }]}>
      <View style={styles.row}>
        <Skeleton width={70}  height={24} radius={99} />
        <Skeleton width={60}  height={24} radius={99} />
      </View>
      <Skeleton height={20} style={{ marginTop: 10 }} />
      <Skeleton height={20} width="75%" style={{ marginTop: 6 }} />
      <Skeleton height={14} style={{ marginTop: 10 }} />
      <Skeleton height={14} style={{ marginTop: 5 }} />
      <Skeleton height={14} width="60%" style={{ marginTop: 5 }} />
      <View style={[styles.row, { marginTop: 12 }]}>
        <Skeleton width={80} height={12} radius={99} />
        <Skeleton width={90} height={12} radius={99} />
      </View>
    </View>
  )
}

const styles = StyleSheet.create({
  card: {
    borderRadius: 16,
    padding:      16,
    marginBottom: 10,
    marginHorizontal: 16,
  },
  row: {
    flexDirection:  'row',
    justifyContent: 'space-between',
  },
})
