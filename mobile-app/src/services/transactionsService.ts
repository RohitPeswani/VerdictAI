/**
 * Transactions Service
 * Connects to: backend/app/api/v1/transactions.py (Darshan Prajapati)
 * Endpoints: GET /transactions/cardholder/:id, GET /transactions/:txn_id
 * Seed users: usr_alice_01, usr_bob_02
 */

import apiClient from './apiClient';
import { Transaction } from '../types';

/** Get all transactions for a cardholder (to pick from when filing dispute) */
export const getCardholderTransactions = async (
  cardholderId: string
): Promise<Transaction[]> => {
  const response = await apiClient.get(`/transactions/cardholder/${cardholderId}`);
  return response.data;
};

/** Get a single transaction by ID */
export const getTransactionById = async (
  transactionId: string
): Promise<Transaction> => {
  const response = await apiClient.get(`/transactions/${transactionId}`);
  return response.data;
};
