/**
 * Disputes Service
 * Connects to: backend/app/api/v1/disputes.py (Darshan Prajapati)
 * Endpoints: GET /disputes, GET /disputes/:id, POST /disputes, GET /disputes/:id/audit-trail
 */

import apiClient from './apiClient';
import { DisputeCreateRequest, DisputeListResponse, UnifiedCaseFile } from '../types';

/** List disputes — optionally filter by cardholder_id */
export const getDisputes = async (
  cardholder_id?: string
): Promise<DisputeListResponse> => {
  const params: Record<string, string | number> = { page: 1, page_size: 20 };
  if (cardholder_id) params.cardholder_id = cardholder_id;
  const response = await apiClient.get('/disputes', { params });
  return response.data;
};

/** Get a single dispute's unified case file */
export const getDisputeById = async (disputeId: string): Promise<UnifiedCaseFile> => {
  const response = await apiClient.get(`/disputes/${disputeId}`);
  return response.data;
};

/** File a new dispute — POST /disputes */
export const createDispute = async (
  payload: DisputeCreateRequest
): Promise<UnifiedCaseFile> => {
  const response = await apiClient.post('/disputes', payload);
  return response.data;
};

/** Get cryptographic audit trail for a dispute */
export const getAuditTrail = async (disputeId: string) => {
  const response = await apiClient.get(`/disputes/${disputeId}/audit-trail`);
  return response.data;
};
