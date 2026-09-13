import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  SafeAreaView,
  StatusBar,
  Alert,
} from 'react-native';
import { Colors, Typography, Spacing, Radius } from '../../theme';
import { useNavigation } from '@react-navigation/native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { RootStackParamList } from '../../types';

const DEMO_USER = {
  name: 'Alice Smith',
  cardholderID: 'usr_alice_01',
  email: 'alice.smith@email.com',
  card: '**** **** **** 8841',
  cardType: 'Visa Credit',
  memberSince: 'August 2026',
};

export default function ProfileScreen() {
  const navigation = useNavigation<NativeStackNavigationProp<RootStackParamList>>();

  const handleSignOut = () => {
    Alert.alert(
      'Sign Out',
      'Are you sure you want to sign out?',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Sign Out',
          style: 'destructive',
          onPress: () => {
            navigation.reset({ index: 0, routes: [{ name: 'Auth' }] });
          },
        },
      ]
    );
  };

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar barStyle="light-content" backgroundColor={Colors.bgDeep} />

      <ScrollView contentContainerStyle={styles.scrollContent}>
        {/* Header */}
        <View style={styles.header}>
          <Text style={styles.headerTitle}>Profile</Text>
          <Text style={styles.avatar}>👤</Text>
        </View>

        {/* User Card */}
        <View style={styles.userCard}>
          <View style={styles.avatarCircle}>
            <Text style={styles.avatarInitial}>
              {DEMO_USER.name.split(' ').map(n => n[0]).join('')}
            </Text>
          </View>
          <Text style={styles.userName}>{DEMO_USER.name}</Text>
          <Text style={styles.userEmail}>{DEMO_USER.email}</Text>
          <View style={styles.idBadge}>
            <Text style={styles.idText}>ID: {DEMO_USER.cardholderID}</Text>
          </View>
        </View>

        {/* Linked Card */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>💳 Linked Card</Text>
          <View style={styles.linkedCard}>
            <View>
              <Text style={styles.cardNumber}>{DEMO_USER.card}</Text>
              <Text style={styles.cardType}>{DEMO_USER.cardType}</Text>
            </View>
            <Text style={styles.cardEmoji}>💳</Text>
          </View>
        </View>

        {/* Settings */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>⚙️ Settings</Text>

          <SettingRow
            icon="🔔"
            label="Push Notifications"
            value="Enabled"
            onPress={() => Alert.alert('Notifications', 'Dispute status push alerts are enabled.')}
          />
          <SettingRow
            icon="🔐"
            label="Biometric Authentication"
            value="Face ID / Fingerprint"
            onPress={() => Alert.alert('Biometrics', 'Biometric authentication is active.')}
          />
          <SettingRow
            icon="🌐"
            label="API Server"
            value="localhost:8000"
            onPress={() => Alert.alert('API', 'Connected to VerdictAI FastAPI backend at localhost:8000')}
          />
          <SettingRow
            icon="📅"
            label="Member Since"
            value={DEMO_USER.memberSince}
            onPress={() => {}}
          />
        </View>

        {/* Legal */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>📋 Legal & Info</Text>
          <SettingRow icon="📄" label="Privacy Policy" value="" onPress={() => {}} />
          <SettingRow icon="📝" label="Terms of Service" value="" onPress={() => {}} />
          <SettingRow icon="ℹ️" label="App Version" value="1.0.0 (Phase 2)" onPress={() => {}} />
        </View>

        {/* Sign Out */}
        <TouchableOpacity style={styles.signOutBtn} onPress={handleSignOut} activeOpacity={0.85}>
          <Text style={styles.signOutText}>Sign Out</Text>
        </TouchableOpacity>

        <Text style={styles.footer}>
          VerdictAI · IT644 · Mayank Jayswal (202512093){'\n'}
          Mobile Engineer — Card Member App
        </Text>
      </ScrollView>
    </SafeAreaView>
  );
}

function SettingRow({ icon, label, value, onPress }: {
  icon: string; label: string; value: string; onPress: () => void;
}) {
  return (
    <TouchableOpacity style={styles.settingRow} onPress={onPress} activeOpacity={0.7}>
      <Text style={styles.settingIcon}>{icon}</Text>
      <Text style={styles.settingLabel}>{label}</Text>
      <View style={styles.settingRight}>
        {value ? <Text style={styles.settingValue}>{value}</Text> : null}
        <Text style={styles.chevron}>›</Text>
      </View>
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Colors.bgDeep },
  scrollContent: { padding: Spacing.xl, gap: Spacing.lg, paddingBottom: Spacing['3xl'] },
  header: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  headerTitle: { fontSize: Typography.xl, fontWeight: Typography.bold, color: Colors.textPrimary },
  avatar: { fontSize: 26 },
  userCard: {
    backgroundColor: Colors.bgCard, borderRadius: Radius.xl, padding: Spacing.xl,
    alignItems: 'center', borderWidth: 1, borderColor: Colors.border, gap: Spacing.sm,
  },
  avatarCircle: {
    width: 72, height: 72, borderRadius: 36,
    backgroundColor: Colors.primary + '30', borderWidth: 2, borderColor: Colors.primary,
    alignItems: 'center', justifyContent: 'center',
  },
  avatarInitial: { fontSize: Typography['2xl'], fontWeight: Typography.bold, color: Colors.primary },
  userName: { fontSize: Typography.xl, fontWeight: Typography.bold, color: Colors.textPrimary },
  userEmail: { fontSize: Typography.sm, color: Colors.textSecondary },
  idBadge: { backgroundColor: Colors.bgSurface, borderRadius: Radius.full, paddingHorizontal: Spacing.md, paddingVertical: Spacing.xs },
  idText: { fontSize: Typography.xs, color: Colors.textMuted, fontFamily: 'monospace' },
  section: { gap: Spacing.sm },
  sectionTitle: { fontSize: Typography.base, fontWeight: Typography.semibold, color: Colors.textPrimary, marginBottom: Spacing.xs },
  linkedCard: {
    flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center',
    backgroundColor: Colors.bgCard, borderRadius: Radius.lg, padding: Spacing.base,
    borderWidth: 1, borderColor: Colors.border,
  },
  cardNumber: { fontSize: Typography.base, fontWeight: Typography.bold, color: Colors.textPrimary, letterSpacing: 2 },
  cardType: { fontSize: Typography.xs, color: Colors.textSecondary, marginTop: 2 },
  cardEmoji: { fontSize: 28 },
  settingRow: {
    flexDirection: 'row', alignItems: 'center',
    backgroundColor: Colors.bgCard, borderRadius: Radius.lg, padding: Spacing.base,
    borderWidth: 1, borderColor: Colors.border, gap: Spacing.md,
  },
  settingIcon: { fontSize: 20 },
  settingLabel: { flex: 1, fontSize: Typography.base, color: Colors.textPrimary, fontWeight: Typography.medium },
  settingRight: { flexDirection: 'row', alignItems: 'center', gap: Spacing.xs },
  settingValue: { fontSize: Typography.xs, color: Colors.textSecondary },
  chevron: { fontSize: Typography.lg, color: Colors.textMuted },
  signOutBtn: {
    backgroundColor: Colors.bgCard, borderRadius: Radius.lg, paddingVertical: Spacing.base,
    alignItems: 'center', borderWidth: 1, borderColor: Colors.error + '60',
  },
  signOutText: { fontSize: Typography.base, fontWeight: Typography.semibold, color: Colors.error },
  footer: { textAlign: 'center', fontSize: Typography.xs, color: Colors.textMuted, lineHeight: 18 },
});
