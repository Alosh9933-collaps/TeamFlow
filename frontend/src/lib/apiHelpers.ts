import axios from 'axios';

export function listFromResponse<T>(data: unknown): T[] {
  if (Array.isArray(data)) return data as T[];
  if (data && typeof data === 'object' && 'results' in data) {
    const results = (data as { results?: unknown }).results;
    if (Array.isArray(results)) return results as T[];
  }
  return [];
}

export function getErrorMessage(error: unknown, fallback = 'Something went wrong. Please try again.') {
  if (axios.isAxiosError(error)) {
    const data: unknown = error.response?.data;
    if (data && typeof data === 'object') {
      const record = data as Record<string, unknown>;
      if (typeof record.detail === 'string') return record.detail;
      if (typeof record.message === 'string') return record.message;
      for (const value of Object.values(record)) {
        if (typeof value === 'string') return value;
        if (Array.isArray(value) && typeof value[0] === 'string') return value[0];
      }
    }
    if (!error.response) return 'Could not reach Django. Check that the backend is running.';
  }
  return fallback;
}

export function formatDate(value?: string | null) {
  if (!value) return '—';
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleDateString();
}

export function projectIdOf(value: number | { id: number }) {
  return typeof value === 'number' ? value : value.id;
}

export function humanize(value?: string | null) {
  if (!value) return 'Unknown';
  return value.replaceAll('_', ' ').replaceAll('-', ' ').toLowerCase().replace(/\b\w/g, (char) => char.toUpperCase());
}
