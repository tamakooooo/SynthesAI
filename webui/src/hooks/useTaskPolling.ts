import { useState, useEffect, useCallback, useRef } from 'react';
import { getVideoTaskStatus, TaskStatusResponse } from '../services/api';

interface UseTaskPollingOptions {
  taskId: string | null;
  intervalMs?: number;
  onComplete?: (result: TaskStatusResponse) => void;
  onError?: (error: Error) => void;
}

export function useTaskPolling(options: UseTaskPollingOptions) {
  const { taskId, intervalMs = 5000, onComplete, onError } = options;
  const [status, setStatus] = useState<TaskStatusResponse | null>(null);
  const [isPolling, setIsPolling] = useState(false);
  const intervalRef = useRef<number | null>(null);

  const stopPolling = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
    setIsPolling(false);
  }, []);

  const startPolling = useCallback(async () => {
    if (!taskId) return;

    setIsPolling(true);

    const poll = async () => {
      try {
        const taskStatus = await getVideoTaskStatus(taskId);
        setStatus(taskStatus);

        if (taskStatus.status === 'completed') {
          stopPolling();
          onComplete?.(taskStatus);
        } else if (taskStatus.status === 'failed') {
          stopPolling();
          onError?.(new Error(taskStatus.error || 'Task failed'));
        } else if (taskStatus.status === 'cancelled') {
          stopPolling();
        }
      } catch (error) {
        console.error('Polling error:', error);
        // Don't stop polling on network errors, keep retrying
      }
    };

    // Initial poll
    await poll();

    // Set up interval
    intervalRef.current = window.setInterval(poll, intervalMs);
  }, [taskId, intervalMs, onComplete, onError, stopPolling]);

  useEffect(() => {
    if (taskId && taskId !== status?.task_id) {
      startPolling();
    }

    return () => stopPolling();
  }, [taskId, startPolling, stopPolling, status?.task_id]);

  return { status, isPolling, startPolling, stopPolling };
}