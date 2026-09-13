import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  StatusBar,
  SafeAreaView,
} from 'react-native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { AuthStackParamList } from '../../types';
import { Colors, Typography, Spacing, Radius } from '../../theme';

type Props = {
  navigation: NativeStackNavigationProp<AuthStackParamList, 'Welcome'>;
};

export default function WelcomeScreen({ navigation }: Props) {
  return (
    <SafeAreaView style={styles.container}>
      <StatusBar barStyle="light-content" backgroundColor={Colors.bgDeep} />

      {/* Logo & Branding */}
      <View style={styles.heroSection}>
        <View style={styles.logoContainer}>
          <Text style={styles.logoIcon}>⚖️</Text>
        </View>
        <Text style={styles.appName}>VerdictAI</Text>
        <Text style={styles.tagline}>Frictionless Dispute Resolution</Text>
      </View>

      {/* Value Propositions */}
      <View style={styles.featuresSection}>
        <FeatureRow icon="⚡" text="Disputes resolved in minutes, not weeks" />
        <FeatureRow icon="🔍" text="AI-powered evidence analysis & fair scoring" />
        <FeatureRow icon="🔒" text="Cryptographic tamper-evident audit trail" />
        <FeatureRow icon="📱" text="Real-time 48h SLA status tracking" />
      </View>

      {/* Actions */}
      <View style={styles.actionsSection}>
        <TouchableOpacity
          style={styles.primaryButton}
          onPress={() => navigation.navigate('Login')}
          activeOpacity={0.85}
        >
          <Text style={styles.primaryButtonText}>Get Started</Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={styles.secondaryButton}
          onPress={() => navigation.navigate('Login')}
          activeOpacity={0.85}
        >
          <Text style={styles.secondaryButtonText}>Sign In</Text>
        </TouchableOpacity>
      </View>

      <Text style={styles.footer}>
        IT644 · VerdictAI · Frictionless Dispute Platform
      </Text>
    </SafeAreaView>
  );
}

function FeatureRow({ icon, text }: { icon: string; text: string }) {
  return (
    <View style={styles.featureRow}>
      <Text style={styles.featureIcon}>{icon}</Text>
      <Text style={styles.featureText}>{text}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.bgDeep,
    paddingHorizontal: Spacing.xl,
    justifyContent: 'space-between',
  },
  heroSection: {
    alignItems: 'center',
    paddingTop: Spacing['3xl'],
  },
  logoContainer: {
    width: 90,
    height: 90,
    borderRadius: Radius.xl,
    backgroundColor: Colors.bgCard,
    borderWidth: 1.5,
    borderColor: Colors.primary,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: Spacing.base,
  },
  logoIcon: {
    fontSize: 40,
  },
  appName: {
    fontSize: Typography['3xl'],
    fontWeight: Typography.extrabold,
    color: Colors.textPrimary,
    letterSpacing: -0.5,
  },
  tagline: {
    fontSize: Typography.base,
    color: Colors.primary,
    fontWeight: Typography.medium,
    marginTop: Spacing.xs,
    letterSpacing: 0.3,
  },
  featuresSection: {
    gap: Spacing.md,
  },
  featureRow: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: Colors.bgCard,
    borderRadius: Radius.md,
    paddingVertical: Spacing.md,
    paddingHorizontal: Spacing.base,
    borderWidth: 1,
    borderColor: Colors.border,
    gap: Spacing.md,
  },
  featureIcon: {
    fontSize: 22,
  },
  featureText: {
    fontSize: Typography.sm,
    color: Colors.textSecondary,
    fontWeight: Typography.medium,
    flex: 1,
  },
  actionsSection: {
    gap: Spacing.md,
  },
  primaryButton: {
    backgroundColor: Colors.primary,
    borderRadius: Radius.lg,
    paddingVertical: Spacing.base,
    alignItems: 'center',
  },
  primaryButtonText: {
    fontSize: Typography.md,
    fontWeight: Typography.bold,
    color: '#FFFFFF',
    letterSpacing: 0.3,
  },
  secondaryButton: {
    backgroundColor: Colors.bgCard,
    borderRadius: Radius.lg,
    paddingVertical: Spacing.base,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: Colors.border,
  },
  secondaryButtonText: {
    fontSize: Typography.md,
    fontWeight: Typography.semibold,
    color: Colors.textPrimary,
  },
  footer: {
    textAlign: 'center',
    fontSize: Typography.xs,
    color: Colors.textMuted,
    paddingBottom: Spacing.base,
  },
});
