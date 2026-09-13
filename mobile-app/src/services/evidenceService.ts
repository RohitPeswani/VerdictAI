/**
 * Evidence Service
 * Connects to: backend/app/api/v1/evidence.py (Darshan Prajapati)
 * Endpoints: POST /evidence/upload, GET /evidence/:dispute_id/items
 * File size limit: 10MB for cardholders (SRS FR-08)
 */

import apiClient from './apiClient';
import { EvidenceItem } from '../types';

const CARDHOLDER_MAX_MB = 10;
const CARDHOLDER_MAX_BYTES = CARDHOLDER_MAX_MB * 1024 * 1024;

export interface EvidenceUploadParams {
  disputeId: string;
  evidenceType: string;
  fileUri: string;
  fileName: string;
  mimeType: string;
  fileSize: number;
}

/** Upload a file as evidence for a dispute */
export const uploadEvidence = async (
  params: EvidenceUploadParams
): Promise<EvidenceItem> => {
  // Enforce 10MB client-side limit before sending (SRS FR-08, AC-04)
  if (params.fileSize > CARDHOLDER_MAX_BYTES) {
    throw new Error(
      `File exceeds the maximum allowed size of ${CARDHOLDER_MAX_MB}MB for cardholders.`
    );
  }

  const formData = new FormData();
  formData.append('dispute_id', params.disputeId);
  formData.append('evidence_type', params.evidenceType);
  formData.append('source', 'CARDHOLDER');
  formData.append('actor', 'CARDHOLDER_MOBILE_APP');
  formData.append('file', {
    uri: params.fileUri,
    name: params.fileName,
    type: params.mimeType,
  } as unknown as Blob);

  const response = await apiClient.post('/evidence/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return response.data;
};

/** List all evidence items attached to a dispute */
export const getEvidenceItems = async (
  disputeId: string
): Promise<EvidenceItem[]> => {
  const response = await apiClient.get(`/evidence/${disputeId}/items`);
  return response.data;
};
