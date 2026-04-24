import React, { useState, useEffect } from 'react';
import {
  submitVideoTask,
  cancelVideoTask,
  getVideoTaskStatus,
  getVideoTaskResult,
  getHistory,
  VideoResult,
  TaskSubmitResponse,
  TaskStatusResponse,
  HistoryRecord,
} from '../services/api';
import {
  videoResultToMarkdown,
  exportMarkdown,
  exportPdfViaPrint,
  downloadTranscript,
  sanitizeFilename,
  getTimestamp,
} from '../utils/export';

interface TaskInfo {
  taskId: string;
  url: string;
  submittedAt: Date;
}

const DashboardPage: React.FC = () => {
  const [url, setUrl] = useState('');
  const [format, setFormat] = useState('markdown');
  const [language, setLanguage] = useState('zh');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [currentTask, setCurrentTask] = useState<TaskInfo | null>(null);
  const [taskStatus, setTaskStatus] = useState<TaskStatusResponse | null>(null);
  const [polling, setPolling] = useState(false);
  const [result, setResult] = useState<VideoResult | null>(null);
  const [historyRecords, setHistoryRecords] = useState<HistoryRecord[]>([]);
  const [selectedRecord, setSelectedRecord] = useState<HistoryRecord | null>(null);
  const [loadingHistory, setLoadingHistory] = useState(true);

  // Load history on mount
  useEffect(() => {
    loadHistory();
  }, []);

  // Poll task status
  useEffect(() => {
    if (!currentTask?.taskId) return;

    const pollStatus = async () => {
      try {
        const status = await getVideoTaskStatus(currentTask.taskId);
        setTaskStatus(status);

        if (status.status === 'completed') {
          setPolling(false);
          try {
            const videoResult = await getVideoTaskResult(currentTask.taskId);
            setResult(videoResult);
            loadHistory();
          } catch (err) {
            setError('获取结果失败');
          }
        } else if (status.status === 'failed' || status.status === 'cancelled') {
          setPolling(false);
          if (status.error) {
            setError(status.error);
          }
        }
      } catch (err) {
        console.error('Polling error:', err);
      }
    };

    pollStatus();
    const interval = setInterval(pollStatus, 3000);
    setPolling(true);

    return () => clearInterval(interval);
  }, [currentTask?.taskId]);

  const loadHistory = async () => {
    setLoadingHistory(true);
    try {
      const data = await getHistory({ limit: 20 });
      setHistoryRecords(data);
    } catch (err) {
      console.error('Load history failed:', err);
    } finally {
      setLoadingHistory(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!url) return;

    setSubmitting(true);
    setError(null);
    setResult(null);
    setTaskStatus(null);

    try {
      const response: TaskSubmitResponse = await submitVideoTask(url, {
        format,
        language,
      });

      setCurrentTask({
        taskId: response.task_id,
        url,
        submittedAt: new Date(),
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : '提交失败');
    } finally {
      setSubmitting(false);
    }
  };

  const handleCancelTask = async () => {
    if (!currentTask) return;
    try {
      await cancelVideoTask(currentTask.taskId);
      setCurrentTask(null);
      setPolling(false);
      setTaskStatus(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : '取消失败');
    }
  };

  const handleViewRecord = async (record: HistoryRecord) => {
    setSelectedRecord(record);
    setError(null);
    setResult(null);

    if (record.module === 'video_summary') {
      try {
        const videoResult = await getVideoTaskResult(record.id);
        setResult(videoResult);
      } catch (err) {
        setError(err instanceof Error ? err.message : '获取结果失败');
      }
    }
  };

  const handleExportMarkdown = () => {
    if (!result) return;
    const md = videoResultToMarkdown(result);
    const filename = `${sanitizeFilename(result.title || '视频总结')}_${getTimestamp()}.md`;
    exportMarkdown(md, filename);
  };

  const handleExportPdf = () => {
    if (!result) return;
    const md = videoResultToMarkdown(result);
    exportPdfViaPrint(md, result.title || '视频内容总结');
  };

  const handleDownloadTranscript = () => {
    if (!result || !result.transcript) return;
    downloadTranscript(result.transcript, result.title || '视频字幕');
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'bg-green-100 text-green-700';
      case 'in_progress':
        return 'bg-blue-100 text-blue-700';
      case 'running':
        return 'bg-blue-100 text-blue-700';
      case 'failed':
        return 'bg-red-100 text-red-700';
      default:
        return 'bg-gray-100 text-gray-600';
    }
  };

  const getModuleLabel = (module: string) => {
    switch (module) {
      case 'video_summary':
        return '视频';
      case 'link_learning':
        return '链接';
      case 'vocabulary':
        return '词汇';
      default:
        return module;
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">学习看板</h1>
        <p className="text-gray-600 mt-1">
          提交视频任务，实时查看进度，浏览历史记录
        </p>
      </div>

      {/* Task Submission */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">提交新任务</h2>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              视频链接 (B站/YouTube/抖音)
            </label>
            <input
              type="url"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="https://www.bilibili.com/video/BV..."
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              required
            />
          </div>

          <div className="flex gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                输出格式
              </label>
              <select
                value={format}
                onChange={(e) => setFormat(e.target.value)}
                className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="markdown">Markdown</option>
                <option value="pdf">PDF</option>
                <option value="both">两者</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                总结语言
              </label>
              <select
                value={language}
                onChange={(e) => setLanguage(e.target.value)}
                className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="zh">中文</option>
                <option value="en">英文</option>
              </select>
            </div>
          </div>

          <button
            type="submit"
            disabled={submitting || !url || polling}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {submitting ? '提交中...' : polling ? '任务进行中' : '提交任务'}
          </button>
        </form>
      </div>

      {/* Error */}
      {error && (
        <div className="bg-red-50 rounded-lg p-4 border border-red-200">
          <p className="text-red-700">{error}</p>
        </div>
      )}

      {/* Task Progress */}
      {taskStatus && (
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-lg font-semibold text-gray-900">任务进度</h3>
              <p className="text-sm text-gray-500">Task ID: {taskStatus.task_id}</p>
            </div>
            <span className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(taskStatus.status)}`}>
              {taskStatus.status === 'completed' ? '已完成' :
               taskStatus.status === 'running' ? '处理中' :
               taskStatus.status === 'failed' ? '失败' :
               taskStatus.status === 'cancelled' ? '已取消' : '等待中'}
            </span>
          </div>

          {/* Progress bar */}
          {taskStatus.status === 'running' && (
            <div className="mb-4">
              <div className="flex items-center justify-between mb-1">
                <span className="text-sm text-gray-600">{taskStatus.message}</span>
                <span className="text-sm text-blue-600 font-medium">{Math.round(taskStatus.progress * 100)}%</span>
              </div>
              <div className="w-full h-2 bg-gray-200 rounded-full overflow-hidden">
                <div
                  className="h-full bg-blue-600 transition-all duration-300"
                  style={{ width: `${taskStatus.progress * 100}%` }}
                />
              </div>
            </div>
          )}

          {taskStatus.status === 'running' && (
            <button
              onClick={handleCancelTask}
              className="px-4 py-2 text-red-600 border border-red-300 rounded-md hover:bg-red-50"
            >
              取消任务
            </button>
          )}

          {taskStatus.error && (
            <p className="text-red-600 mt-2">{taskStatus.error}</p>
          )}
        </div>
      )}

      {/* Result Display */}
      {result && (
        <div className="bg-white rounded-lg shadow p-6 space-y-4">
          <div>
            <h2 className="text-xl font-bold text-gray-900">{result.title}</h2>
            <p className="text-sm text-gray-500 mt-1">
              {(result.metadata?.duration as string | number | undefined)?.toString() || ''} · {(result.metadata?.platform as string | undefined) || ''}
            </p>
          </div>

          {/* Summary */}
          <div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">内容总结</h3>
            <p className="text-gray-700 leading-relaxed whitespace-pre-wrap">
              {result.summary?.content || ''}
            </p>
          </div>

          {/* Key points */}
          {result.summary?.key_points && result.summary.key_points.length > 0 && (
            <div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">核心要点</h3>
              <ul className="space-y-1">
                {result.summary.key_points.map((point, i) => (
                  <li key={i} className="flex items-start gap-2">
                    <span className="text-blue-600">•</span>
                    <span className="text-gray-700">{point}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Transcript preview */}
          {result.transcript && (
            <div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">字幕预览</h3>
              <div className="bg-yellow-50 rounded-md p-4 font-mono text-sm text-gray-700 max-h-[200px] overflow-y-auto whitespace-pre-wrap">
                {result.transcript.slice(0, 500)}...
              </div>
            </div>
          )}

          {/* Actions */}
          <div className="flex gap-2 pt-4 border-t border-gray-200">
            <button
              onClick={handleExportMarkdown}
              className="px-4 py-2 text-gray-700 border border-gray-300 rounded-md hover:bg-gray-50"
            >
              导出 Markdown
            </button>
            <button
              onClick={handleExportPdf}
              className="px-4 py-2 text-gray-700 border border-gray-300 rounded-md hover:bg-gray-50"
            >
              导出 PDF
            </button>
            <button
              onClick={handleDownloadTranscript}
              disabled={!result?.transcript}
              className="px-4 py-2 text-gray-700 border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              下载字幕
            </button>
          </div>
        </div>
      )}

      {/* History */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">历史任务</h2>

        {loadingHistory && (
          <div className="text-center py-8">
            <div className="animate-spin w-8 h-8 border-2 border-blue-600 border-t-transparent rounded-full mx-auto" />
          </div>
        )}

        {!loadingHistory && historyRecords.length === 0 && (
          <div className="text-center py-8 text-gray-500">
            <p>暂无学习记录</p>
          </div>
        )}

        {!loadingHistory && historyRecords.length > 0 && (
          <div className="space-y-2">
            {historyRecords.map((record) => (
              <div
                key={record.id}
                onClick={() => handleViewRecord(record)}
                className={`p-4 rounded-lg border cursor-pointer transition-all ${
                  selectedRecord?.id === record.id
                    ? 'border-blue-500 bg-blue-50'
                    : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
                }`}
              >
                <div className="flex items-center justify-between gap-4">
                  <div className="flex items-center gap-2">
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(record.status)}`}>
                      {record.status === 'completed' ? '已完成' :
                       record.status === 'in_progress' ? '进行中' : '失败'}
                    </span>
                    <span className="px-2 py-1 rounded text-xs bg-gray-100 text-gray-600">
                      {getModuleLabel(record.module)}
                    </span>
                  </div>
                  <span className="text-sm text-gray-500">
                    {new Date(record.timestamp).toLocaleString('zh-CN')}
                  </span>
                </div>
                <h3 className="text-base font-medium text-gray-900 mt-2 truncate">
                  {record.title || '(无标题)'}
                </h3>
                {record.url && (
                  <p className="text-sm text-gray-500 truncate mt-1">
                    {record.url}
                  </p>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default DashboardPage;