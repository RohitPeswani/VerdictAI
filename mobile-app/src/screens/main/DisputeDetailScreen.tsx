import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  SafeAreaView,
  StatusBar,
  ActivityIndicator,
} from 'react-native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { RouteProp } from '@react-navigation/native';
import { HomeStackParamList, UnifiedCaseFile, DisputeStatus } from '../../types';
import { Colors, Typography, Spacing, Radius, Shadow } from '../../theme';
import { getDisputeById } from '../../services/disputesService';

type Props = {
  navigation: NativeStackNavigationProp<HomeStackParamList, 'DisputeDetail'>;
  route: RouteProp<HomeStackParamList, 'DisputeDetail'>;
};

// Full lifecycle state machine order (mirrors backend state_machine.py)
const LIFECYCLE_STEPS: DisputeStatus[] = [
  'SUBMITTED',
  'EVIDENCE_INGESTED',
  'IN_ANALYSIS',
  'SCORING_EVALUATED',
  'AUTO_RESOLVED',
];

const STATUS_LABELS: Record<string, string> = {
  SUBMITTED: 'Dispute Filed',
  EVIDENCE_PENDING: 'Evidence Pending',
  EVIDENCE_INGESTED: 'Evidence Analyzed',
  IN_ANALYSIS: 'AI Analysis',
  SCORING_EVALUATED: 'Score Generated',
  AUTO_RESOLVED: 'Auto Resolved',
  MANUAL_REVIEW_QUEUE: 'Manual Review',
  ADMIN_OVERRIDDEN: 'Admin Override',
  RESOLUTION_NOTIFIED: 'Notified',
  CLOSED: 'Closed',
  REJECTED: 'Rejected',
};

export default function DisputeDetailScreen({ navigation, route }: Props) {
  const { disputeId } = route.params;
  const [caseFile, setCaseFile] = useState<UnifiedCaseFile | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchCase();
  }, [disputeId]);

  const fetchCase = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getDisputeById(disputeId);
      setCaseFile(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load case file.');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.center}>
          <ActivityIndicator size="large" color={Colors.primary} />
          <Text style={styles.loadingText}>Loading case file...</Text>
        </View>
      </SafeAreaView>
    );
  }

  if (error || !caseFile) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.center}>
          <Text style={styles.errorIcon}>⚠️</Text>
          <Text style={styles.errorText}>{error ?? 'Case not found.'}</Text>
          <TouchableOpacity onPress={fetchCase} style={styles.retryBtn}>
            <Text style={styles.retryText}>Retry</Text>
          </TouchableOpacity>
        </View>
      </SafeAreaView>
    );
  }

  const status = caseFile.header.current_status;
  const slaDate = new Date(caseFile.header.sla_deadline);
  const now = new Date();
  const hoursLeft = Math.max(0, Math.floor((slaDate.getTime() - now.getTime()) / 3600000));
  const minsLeft = Math.max(0, Math.floor(((slaDate.getTime() - now.getTime()) % 3600000) / 60000));

  // Current step index in lifecycle
  const currentStepIndex = LIFECYCLE_STEPS.indexOf(status as DisputeStatus);

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar barStyle="light-content" backgroundColor={Colors.bgDeep} />

      {/* Nav Header */}
      <View style={styles.navHeader}>
        <TouchableOpacity onPress={() => navigation.goBack()} style={styles.backBtn}>
          <Text style={styles.backIcon}>←</Text>
        </TouchableOpacity>
        <Text style={styles.navTitle}>Case Tracker</Text>
        <View style={{ width: 40 }} />
      </View>

      <ScrollView contentContainerStyle={styles.scrollContent} showsVerticalScrollIndicator={false}>
        {/* Case Identity Card */}
        <View style={styles.identityCard}>
          <Text style={styles.merchantName}>{caseFile.transaction.merchant_name}</Text>
          <Text style={styles.caseRef}>{caseFile.header.case_reference_number}</Text>
          <Text style={styles.disputedAmount}>
            ${caseFile.header.disputed_amount.toFixed(2)} {caseFile.header.currency}
          </Text>
          <Text style={styles.caseHash}>
            🔐 SHA-256: {caseFile.case_hash_sha256.slice(0, 20)}...
          </Text>
        </View>

        {/* SLA Countdown */}
        {!['AUTO_RESOLVED', 'CLOSED', 'REJECTED'].includes(status) && (
          <View style={styles.slaCard}>
            <Text style={styles.slaTitle}>⏱ SLA Decision Window</Text>
            <Text style={styles.slaTime}>{hoursLeft}h {minsLeft}m remaining</Text>
            <Text style={styles.slaNote}>
              Merchant response deadline: {slaDate.toLocaleDateString()}
            </Text>
          </View>
        )}

        {/* Resolution Banner */}
        {['AUTO_RESOLVED', 'CLOSED'].includes(status) && (
          <View style={styles.resolvedBanner}>
            <Text style={styles.resolvedTitle}>✅ Dispute Resolved</Text>
            {caseFile.resolution && (
              <Text style={styles.resolvedOutcome}>
                Outcome: {String(caseFile.resolution.outcome ?? 'Decision recorded')}
              </Text>
            )}
          </View>
        )}

        {/* Lifecycle Progress Stepper */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Lifecycle Progress</Text>
          <View style={styles.stepper}>
            {LIFECYCLE_STEPS.map((step, index) => {
              const isPast = currentStepIndex > index;
              const isCurrent = currentStepIndex === index;
              return (
                <View key={step} style={styles.stepRow}>
                  <View style={styles.stepLeft}>
                    <View style={[
                      styles.stepDot,
                      isPast && styles.stepDotDone,
                      isCurrent && styles.stepDotActive,
                    ]}>
                      <Text style={styles.stepDotText}>
                        {isPast ? '✓' : isCurrent ? '●' : '○'}
                      </Text>
                    </View>
                    {index < LIFECYCLE_STEPS.length - 1 && (
                      <View style={[styles.stepLine, isPast && styles.stepLineDone]} />
                    )}
                  </View>
                  <Text style={[
                    styles.stepLabel,
                    isCurrent && styles.stepLabelActive,
                    isPast && styles.stepLabelDone,
                  ]}>
                    {STATUS_LABELS[step] ?? step}
                  </Text>
                </View>
              );
            })}
          </View>
        </View>

        {/* Evidence Items */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>
            Evidence Items ({caseFile.evidence_items.length})
          </Text>
          {caseFile.evidence_items.length === 0 ? (
            <Text style={styles.noEvidence}>No evidence submitted yet.</Text>
          ) : (
            caseFile.evidence_items.map((item, idx) => (
              <View key={idx} style={styles.evidenceItem}>
                <Text style={styles.evidenceType}>📄 {item.evidence_type}</Text>
                <Text style={styles.evidenceFile}>{item.file_name ?? 'Structured payload'}</Text>
              </View>
            ))
          )}
        </View>

        {/* Cardholder Statement */}
        {caseFile.cardholder_statement && (
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Your Statement</Text>
            <View style={styles.statementBox}>
              <Text style={styles.statementText}>{caseFile.cardholder_statement}</Text>
            </View>
          </View>
        )}

        {/* Audit Chain Info */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>🔐 Audit Chain</Text>
          <View style={styles.auditBox}>
            <Text style={styles.auditText}>
              Chain Length: {caseFile.audit_chain_length} events
            </Text>
            <Text style={styles.auditText}>
              Case Sealed: {caseFile.header.is_sealed ? '✅ Yes' : '⏳ Pending'}
            </Text>
          </View>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Colors.bgDeep },
  center: { flex: 1, alignItems: 'center', justifyContent: 'center', gap: Spacing.md },
  loadingText: { color: Colors.textSecondary },
  errorIcon: { fontSize: 40 },
  errorText: { color: Colors.error, textAlign: 'center', fontSize: Typography.base },
  retryBtn: { backgroundColor: Colors.primary, borderRadius: Radius.md, paddingHorizontal: Spacing.xl, paddingVertical: Spacing.md },
  retryText: { color: '#fff', fontWeight: Typography.bold },
  navHeader: {
    flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between',
    paddingHorizontal: Spacing.xl, paddingVertical: Spacing.base,
  },
  backBtn: { padding: Spacing.sm },
  backIcon: { fontSize: 22, color: Colors.textPrimary },
  navTitle: { fontSize: Typography.md, fontWeight: Typography.semibold, color: Colors.textPrimary },
  scrollContent: { padding: Spacing.xl, gap: Spacing.base, paddingBottom: Spacing['3xl'] },
  identityCard: {
    backgroundColor: Colors.bgCard, borderRadius: Radius.lg, padding: Spacing.xl,
    borderWidth: 1, borderColor: Colors.border, gap: Spacing.xs, ...Shadow.card,
  },
  merchantName: { fontSize: Typography.xl, fontWeight: Typography.bold, color: Colors.textPrimary },
  caseRef: { fontSize: Typography.sm, color: Colors.primary, fontWeight: Typography.medium },
  disputedAmount: { fontSize: Typography['2xl'], fontWeight: Typography.extrabold, color: Colors.textPrimary, marginTop: Spacing.sm },
  caseHash: { fontSize: Typography.xs, color: Colors.textMuted, marginTop: Spacing.xs },
  slaCard: {
    backgroundColor: '#1A1200', borderRadius: Radius.lg, padding: Spacing.base,
    borderWidth: 1, borderColor: Colors.statusSubmitted, gap: Spacing.xs,
  },
  slaTitle: { fontSize: Typography.sm, color: Colors.statusSubmitted, fontWeight: Typography.semibold },
  slaTime: { fontSize: Typography.xl, fontWeight: Typography.extrabold, color: Colors.textPrimary },
  slaNote: { fontSize: Typography.xs, color: Colors.textMuted },
  resolvedBanner: {
    backgroundColor: '#0A1F14', borderRadius: Radius.lg, padding: Spacing.base,
    borderWidth: 1, borderColor: Colors.statusResolved, gap: Spacing.xs,
  },
  resolvedTitle: { fontSize: Typography.md, fontWeight: Typography.bold, color: Colors.statusResolved },
  resolvedOutcome: { fontSize: Typography.sm, color: Colors.textSecondary },
  section: {
    backgroundColor: Colors.bgCard, borderRadius: Radius.lg, padding: Spacing.base,
    borderWidth: 1, borderColor: Colors.border, gap: Spacing.md,
  },
  sectionTitle: { fontSize: Typography.base, fontWeight: Typography.semibold, color: Colors.textPrimary },
  stepper: { gap: 0 },
  stepRow: { flexDirection: 'row', alignItems: 'flex-start', gap: Spacing.md, minHeight: 40 },
  stepLeft: { alignItems: 'center', width: 24 },
  stepDot: {
    width: 24, height: 24, borderRadius: 12,
    backgroundColor: Colors.bgSurface, borderWidth: 1.5, borderColor: Colors.border,
    alignItems: 'center', justifyContent: 'center',
  },
  stepDotActive: { borderColor: Colors.primary, backgroundColor: Colors.bgElevated },
  stepDotDone: { borderColor: Colors.statusResolved, backgroundColor: '#0A2A1A' },
  stepDotText: { fontSize: 10, color: Colors.textSecondary },
  stepLine: { width: 2, flex: 1, backgroundColor: Colors.border, minHeight: 16, marginTop: 2 },
  stepLineDone: { backgroundColor: Colors.statusResolved },
  stepLabel: { fontSize: Typography.sm, color: Colors.textMuted, paddingTop: 4, flex: 1 },
  stepLabelActive: { color: Colors.primary, fontWeight: Typography.semibold },
  stepLabelDone: { color: Colors.textSecondary },
  noEvidence: { fontSize: Typography.sm, color: Colors.textMuted },
  evidenceItem: {
    flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center',
    paddingVertical: Spacing.sm, borderBottomWidth: 1, borderBottomColor: Colors.divider,
  },
  evidenceType: { fontSize: Typography.sm, color: Colors.textPrimary, fontWeight: Typography.medium },
  evidenceFile: { fontSize: Typography.xs, color: Colors.textMuted },
  statementBox: {
    backgroundColor: Colors.bgSurface, borderRadius: Radius.md, padding: Spacing.md,
    borderLeftWidth: 3, borderLeftColor: Colors.primary,
  },
  statementText: { fontSize: Typography.sm, color: Colors.textSecondary, lineHeight: 20 },
  auditBox: { gap: Spacing.sm },
  auditText: { fontSize: Typography.sm, color: Colors.textSecondary },
});
