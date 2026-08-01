import { GenerationRequest, GenerationResponse, JobStatusResponse } from './types';

const API_BASE_URL = 'http://127.0.0.1:4317/api';

export async function requestMapGeneration(
  request: GenerationRequest
): Promise<GenerationResponse> {
  const response = await fetch(`${API_BASE_URL}/generate`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    const errText = await response.text().catch(() => 'Server error');
    throw new Error(`Generation error (${response.status}): ${errText}`);
  }

  return await response.json();
}

export async function fetchJobStatus(jobId: string): Promise<JobStatusResponse> {
  const response = await fetch(`${API_BASE_URL}/jobs/${jobId}`, {
    method: 'GET',
    headers: {
      'Accept': 'application/json',
    },
  });

  if (!response.ok) {
    const errText = await response.text().catch(() => 'Server error');
    throw new Error(`Job status error (${response.status}): ${errText}`);
  }

  return await response.json();
}

export function getJobDownloadUrl(jobId: string): string {
  return `${API_BASE_URL}/jobs/${jobId}/download`;
}
