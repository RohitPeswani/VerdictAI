import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  TextInput,
  SafeAreaView,
  StatusBar,
  Alert,
  ActivityIndicator,
  Platform,
} from 'react-native';
import * as DocumentPicker from 'expo-document-picker';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { FileDisputeStackParamList, Transaction, DisputeReason } from '../../types';
import { Colors, Typography, Spacing, Radius, Shadow } from '../../theme';
import { getCardholderTransactions } from '../../services/transactionsService';
import { createDispute } from '../../services/disputesService';
import { uploadEvidence } from '../../services/evidenceService';

type Props = {
  navigation: NativeStackNavigationProp<FileDisputeStackParamList, 'DisputeWizard'>;
};

const DEMO_CARDHOLDER_ID = 'usr_alice_01';
const DEMO_CARDHOLDER_NAME = 'Alice Smith';

const DISPUTE_REASONS: { value: DisputeReason; label: string; icon: string }[] = [
  { value: 'PRODUCT_NOT_RECEIVED', label: 'Item Not Received', icon: '📦' },
  { value: 'PRODUCT_DAMAGED_OR_DEFECTIVE', label: 'Defective / Damaged', icon: '🔧' },
  { value: 'DUPLICATE_PROCESSING', label: 'Duplicate Charge', icon: '🔁' },
  { value: 'FRAUD_UNRECOGNIZED_CHARGE', label: 'Fraudulent / Unrecognized', icon: '🚨' },
  { value: 'SUBSCRIPTION_CANCELLED_CHARGED', label: 'Cancelled Subscription', icon: '❌' },
  { value: 'INCORRECT_AMOUNT_CHARGED', label: 'Incorrect Amount', icon: '💸' },
];

type WizardStep = 1 | 2 | 3 | 4;

export default function DisputeWizardScreen({ navigation }: Props) {
  const [step, setStep] = useState<WizardStep>(1);
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [loadingTxns, setLoadingTxns] = useState(true);

  // Form state
  const [selectedTxn, setSelectedTxn] = useState<Transaction | null>(null);
  const [selectedReason, setSelectedReason] = useState<DisputeReason | null>(null);
  const [statement, setStatement] = useState('');
  const [evidenceFile, setEvidenceFile] = useState<{ name: string; uri: string; size: number; mimeType: string } | null>(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    loadTransactions();
  }, []);

  const loadTransactions = async () => {
    setLoadingTxns(true);
    try {
      const txns = await getCardholderTransactions(DEMO_CARDHOLDER_ID);
      setTransactions(txns.filter((t) => !t.is_disputed));
    } catch {
      setTransactions([]);
    } finally {
      setLoadingTxns(false);
    }
  };

  const pickDocument = async () => {
    try {
      const result = await DocumentPicker.getDocumentAsync({
        type: ['application/pdf', 'image/jpeg', 'image/png'],
        copyToCacheDirectory: true,
      });
      if (!result.canceled && result.assets[0]) {
        const asset = result.assets[0];
        const sizeMB = (asset.size ?? 0) / (1024 * 1024);
        if (sizeMB > 10) {
          Alert.alert('File Too Large', 'Maximum file size is 10MB for cardholders (SRS FR-08).');
          return;
        }
        setEvidenceFile({ name: asset.name, uri: asset.uri, size: asset.size ?? 0, mimeType: asset.mimeType ?? 'application/octet-stream' });
      }
    } catch {
      Alert.alert('Error', 'Could not pick document. Please try again.');
    }
  };

  const handleSubmit = async () => {
    if (!selectedTxn || !selectedReason) {
      Alert.alert('Incomplete', 'Please select a transaction and reason.');
      return;
    }
    setSubmitting(true);
    try {
      // Step 1: Create dispute case
      const caseFile = await createDispute({
        transaction_id: selectedTxn.id,
        cardholder_id: DEMO_CARDHOLDER_ID,
        dispute_reason: selectedReason,
        disputed_amount: selectedTxn.amount,
        cardholder_statement: statement.trim() || undefined,
        merchant_sla_hours: 48,
      });

      // Step 2: Upload evidence file if provided
      if (evidenceFile) {
        await uploadEvidence({
          disputeId: caseFile.header.dispute_id,
          evidenceType: 'RECEIPT',
          fileUri: evidenceFile.uri,
          fileName: evidenceFile.name,
          mimeType: evidenceFile.mimeType,
          fileSize: evidenceFile.size,
        });
      }

      navigation.replace('DisputeSuccess', {
        caseId: caseFile.header.dispute_id,
        referenceNumber: caseFile.header.case_reference_number,
      });
    } catch (err) {
      Alert.alert('Submission Failed', err instanceof Error ? err.message : 'Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  const canProceed = () => {
    if (step === 1) return !!selectedTxn;
    if (step === 2) return !!selectedReason;
    if (step === 3) return true; // evidence is optional
    return true;
  };

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar barStyle="light-content" backgroundColor={Colors.bgDeep} />

      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity onPress={() => (step === 1 ? navigation.goBack() : setStep((s) => (s - 1) as WizardStep))}>
          <Text style={styles.backIcon}>←</Text>
        </TouchableOpacity>
        <Text style={styles.headerTitle}>File a Dispute</Text>
        <Text style={styles.stepCounter}>Step {step}/4</Text>
      </View>

      {/* Progress Bar */}
      <View style={styles.progressBar}>
        <View style={[styles.progressFill, { width: `${(step / 4) * 100}%` }]} />
      </View>

      <ScrollView contentContainerStyle={styles.scrollContent} keyboardShouldPersistTaps="handled">
        {/* Step 1: Select Transaction */}
        {step === 1 && (
          <View style={styles.stepContent}>
            <Text style={styles.stepTitle}>Select Transaction</Text>
            <Text style={styles.stepSubtitle}>Which charge do you want to dispute?</Text>
            {loadingTxns ? (
              <ActivityIndicator color={Colors.primary} style={{ marginTop: Spacing.xl }} />
            ) : transactions.length === 0 ? (
              <Text style={styles.noData}>No transactions available to dispute.</Text>
            ) : (
              transactions.map((txn) => (
                <TouchableOpacity
                  key={txn.id}
                  style={[styles.txnCard, selectedTxn?.id === txn.id && styles.txnCardSelected]}
                  onPress={() => setSelectedTxn(txn)}
                  activeOpacity={0.8}
                >
                  <View style={styles.txnLeft}>
                    <Text style={styles.txnMerchant}>{txn.merchant_name}</Text>
                    <Text style={styles.txnDate}>
                      {new Date(txn.transaction_timestamp).toLocaleDateString()}
                    </Text>
                    <Text style={styles.txnMethod}>{txn.payment_method}</Text>
                  </View>
                  <View style={styles.txnRight}>
                    <Text style={styles.txnAmount}>${txn.amount.toFixed(2)}</Text>
                    {selectedTxn?.id === txn.id && (
                      <Text style={styles.checkmark}>✓</Text>
                    )}
                  </View>
                </TouchableOpacity>
              ))
            )}
          </View>
        )}

        {/* Step 2: Select Reason */}
        {step === 2 && (
          <View style={styles.stepContent}>
            <Text style={styles.stepTitle}>Dispute Reason</Text>
            <Text style={styles.stepSubtitle}>Why are you disputing this charge?</Text>
            {DISPUTE_REASONS.map((reason) => (
              <TouchableOpacity
                key={reason.value}
                style={[styles.reasonCard, selectedReason === reason.value && styles.reasonCardSelected]}
                onPress={() => setSelectedReason(reason.value)}
                activeOpacity={0.8}
              >
                <Text style={styles.reasonIcon}>{reason.icon}</Text>
                <Text style={[styles.reasonLabel, selectedReason === reason.value && styles.reasonLabelSelected]}>
                  {reason.label}
                </Text>
                {selectedReason === reason.value && <Text style={styles.checkmark}>✓</Text>}
              </TouchableOpacity>
            ))}
          </View>
        )}

        {/* Step 3: Evidence Upload */}
        {step === 3 && (
          <View style={styles.stepContent}>
            <Text style={styles.stepTitle}>Attach Evidence</Text>
            <Text style={styles.stepSubtitle}>
              Upload supporting documents (optional but strengthens your case)
            </Text>

            <TouchableOpacity style={styles.uploadBox} onPress={pickDocument} activeOpacity={0.8}>
              <Text style={styles.uploadIcon}>📎</Text>
              <Text style={styles.uploadTitle}>
                {evidenceFile ? evidenceFile.name : 'Tap to attach document'}
              </Text>
              <Text style={styles.uploadSubtext}>PDF, JPG, PNG · Max 10MB</Text>
            </TouchableOpacity>

            {evidenceFile && (
              <TouchableOpacity
                style={styles.removeFile}
                onPress={() => setEvidenceFile(null)}
              >
                <Text style={styles.removeFileText}>Remove file ✕</Text>
              </TouchableOpacity>
            )}

            <Text style={styles.statementLabel}>Your Statement (Optional)</Text>
            <TextInput
              style={styles.statementInput}
              placeholder="Describe what happened in your own words..."
              placeholderTextColor={Colors.textMuted}
              multiline
              numberOfLines={4}
              value={statement}
              onChangeText={setStatement}
              textAlignVertical="top"
            />
          </View>
        )}

        {/* Step 4: Review & Confirm */}
        {step === 4 && selectedTxn && selectedReason && (
          <View style={styles.stepContent}>
            <Text style={styles.stepTitle}>Review & Confirm</Text>
            <Text style={styles.stepSubtitle}>
              Please verify your dispute details before submitting.
            </Text>

            <View style={styles.reviewCard}>
              <ReviewRow label="Merchant" value={selectedTxn.merchant_name} />
              <ReviewRow label="Amount" value={`$${selectedTxn.amount.toFixed(2)} ${selectedTxn.currency}`} />
              <ReviewRow label="Transaction Date" value={new Date(selectedTxn.transaction_timestamp).toLocaleDateString()} />
              <ReviewRow label="Reason" value={DISPUTE_REASONS.find(r => r.value === selectedReason)?.label ?? selectedReason} />
              <ReviewRow label="Evidence" value={evidenceFile ? evidenceFile.name : 'None attached'} />
              <ReviewRow label="SLA Window" value="48 hours (merchant response)" />
            </View>

            <View style={styles.warningBox}>
              <Text style={styles.warningText}>
                ⚠️ By submitting, you confirm this dispute is filed in good faith. VerdictAI will create an immutable, cryptographically sealed case record.
              </Text>
            </View>
          </View>
        )}
      </ScrollView>

      {/* Bottom Action */}
      <View style={styles.bottomBar}>
        {step < 4 ? (
          <TouchableOpacity
            style={[styles.nextBtn, !canProceed() && styles.nextBtnDisabled]}
            onPress={() => setStep((s) => (s + 1) as WizardStep)}
            disabled={!canProceed()}
            activeOpacity={0.85}
          >
            <Text style={styles.nextBtnText}>Continue →</Text>
          </TouchableOpacity>
        ) : (
          <TouchableOpacity
            style={[styles.submitBtn, submitting && styles.submitBtnDisabled]}
            onPress={handleSubmit}
            disabled={submitting}
            activeOpacity={0.85}
          >
            {submitting ? (
              <ActivityIndicator color="#fff" />
            ) : (
              <Text style={styles.submitBtnText}>Submit Dispute Claim ⚖️</Text>
            )}
          </TouchableOpacity>
        )}
      </View>
    </SafeAreaView>
  );
}

function ReviewRow({ label, value }: { label: string; value: string }) {
  return (
    <View style={styles.reviewRow}>
      <Text style={styles.reviewLabel}>{label}</Text>
      <Text style={styles.reviewValue}>{value}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Colors.bgDeep },
  header: {
    flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between',
    paddingHorizontal: Spacing.xl, paddingVertical: Spacing.md,
  },
  backIcon: { fontSize: 22, color: Colors.textPrimary },
  headerTitle: { fontSize: Typography.md, fontWeight: Typography.semibold, color: Colors.textPrimary },
  stepCounter: { fontSize: Typography.sm, color: Colors.textSecondary },
  progressBar: { height: 3, backgroundColor: Colors.border, marginHorizontal: Spacing.xl },
  progressFill: { height: '100%', backgroundColor: Colors.primary, borderRadius: Radius.full },
  scrollContent: { padding: Spacing.xl, paddingBottom: 100 },
  stepContent: { gap: Spacing.md },
  stepTitle: { fontSize: Typography.xl, fontWeight: Typography.bold, color: Colors.textPrimary },
  stepSubtitle: { fontSize: Typography.sm, color: Colors.textSecondary },
  noData: { color: Colors.textMuted, fontSize: Typography.sm, textAlign: 'center', marginTop: Spacing.xl },
  txnCard: {
    flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center',
    backgroundColor: Colors.bgCard, borderRadius: Radius.lg, padding: Spacing.base,
    borderWidth: 1.5, borderColor: Colors.border, ...Shadow.card,
  },
  txnCardSelected: { borderColor: Colors.primary, backgroundColor: Colors.bgElevated },
  txnLeft: { gap: 2 },
  txnMerchant: { fontSize: Typography.base, fontWeight: Typography.semibold, color: Colors.textPrimary },
  txnDate: { fontSize: Typography.xs, color: Colors.textMuted },
  txnMethod: { fontSize: Typography.xs, color: Colors.textSecondary },
  txnRight: { alignItems: 'flex-end', gap: Spacing.xs },
  txnAmount: { fontSize: Typography.lg, fontWeight: Typography.bold, color: Colors.textPrimary },
  checkmark: { color: Colors.primary, fontWeight: Typography.bold, fontSize: Typography.base },
  reasonCard: {
    flexDirection: 'row', alignItems: 'center',
    backgroundColor: Colors.bgCard, borderRadius: Radius.lg, padding: Spacing.base,
    borderWidth: 1.5, borderColor: Colors.border, gap: Spacing.md, ...Shadow.card,
  },
  reasonCardSelected: { borderColor: Colors.primary, backgroundColor: Colors.bgElevated },
  reasonIcon: { fontSize: 22 },
  reasonLabel: { flex: 1, fontSize: Typography.base, color: Colors.textSecondary, fontWeight: Typography.medium },
  reasonLabelSelected: { color: Colors.textPrimary },
  uploadBox: {
    backgroundColor: Colors.bgCard, borderRadius: Radius.lg, borderWidth: 1.5,
    borderColor: Colors.border, borderStyle: 'dashed', padding: Spacing.xl,
    alignItems: 'center', gap: Spacing.sm,
  },
  uploadIcon: { fontSize: 36 },
  uploadTitle: { fontSize: Typography.base, color: Colors.textPrimary, fontWeight: Typography.medium, textAlign: 'center' },
  uploadSubtext: { fontSize: Typography.xs, color: Colors.textMuted },
  removeFile: { alignSelf: 'center' },
  removeFileText: { color: Colors.error, fontSize: Typography.sm },
  statementLabel: { fontSize: Typography.sm, fontWeight: Typography.medium, color: Colors.textSecondary, marginTop: Spacing.sm },
  statementInput: {
    backgroundColor: Colors.bgSurface, borderRadius: Radius.md, borderWidth: 1,
    borderColor: Colors.border, padding: Spacing.base, fontSize: Typography.base,
    color: Colors.textPrimary, minHeight: 100,
  },
  reviewCard: {
    backgroundColor: Colors.bgCard, borderRadius: Radius.lg, padding: Spacing.base,
    borderWidth: 1, borderColor: Colors.border, gap: Spacing.sm,
  },
  reviewRow: { flexDirection: 'row', justifyContent: 'space-between', paddingVertical: Spacing.xs },
  reviewLabel: { fontSize: Typography.sm, color: Colors.textSecondary, flex: 1 },
  reviewValue: { fontSize: Typography.sm, color: Colors.textPrimary, fontWeight: Typography.medium, flex: 2, textAlign: 'right' },
  warningBox: {
    backgroundColor: '#1A1200', borderRadius: Radius.md, padding: Spacing.base,
    borderWidth: 1, borderColor: Colors.warning,
  },
  warningText: { fontSize: Typography.xs, color: Colors.textSecondary, lineHeight: 18 },
  bottomBar: {
    position: 'absolute', bottom: 0, left: 0, right: 0,
    padding: Spacing.xl, backgroundColor: Colors.bgDeep,
    borderTopWidth: 1, borderTopColor: Colors.border,
  },
  nextBtn: { backgroundColor: Colors.primary, borderRadius: Radius.lg, paddingVertical: Spacing.base, alignItems: 'center' },
  nextBtnDisabled: { opacity: 0.4 },
  nextBtnText: { fontSize: Typography.md, fontWeight: Typography.bold, color: '#fff' },
  submitBtn: { backgroundColor: Colors.statusResolved, borderRadius: Radius.lg, paddingVertical: Spacing.base, alignItems: 'center' },
  submitBtnDisabled: { opacity: 0.6 },
  submitBtnText: { fontSize: Typography.md, fontWeight: Typography.bold, color: '#fff' },
});
