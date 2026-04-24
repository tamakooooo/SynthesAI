import React, { useState, useEffect } from 'react';
import {
  submitVideoTask,
  cancelVideoTask,
  getVideoTaskResult,
  VideoResult,
  TaskSubmitResponse,
} from '../services/api';
import { useTaskPolling } from '../hooks/useTaskPolling';
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

const VideoPage: React.FC = () => {
  const [url, setUrl] = useState('');
  const [format, setFormat] = useState('markdown');
  const [language, setLanguage] = useState('zh');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [currentTask, setCurrentTask] = useState<TaskInfo | null>(null);
  const [tasks, setTasks] = useState<TaskInfo[]>([]);
  const [result, setResult] = useState<VideoResult | null>(null);

  // Task polling
  const { status, isPolling } = useTaskPolling({
    taskId: currentTask?.taskId || null,
    intervalMs: 5000,
    onComplete: async (taskStatus) => {
      if (taskStatus.task_id) {
        try {
          const videoResult = await getVideoTaskResult(taskStatus.task_id);
          setResult(videoResult);
        } catch (err) {
          setError('获取结果失败');
        }
      }
    },
    onError: (err) => {
      setError(err.message);
    },
  });

  // Load tasks from localStorage
  useEffect(() => {
    const savedTasks = localStorage.getItem('video_tasks');
    if (savedTasks) {
      setTasks(JSON.parse(savedTasks));
    }
  }, []);

  // Save tasks to localStorage
  const saveTasks = (newTasks: TaskInfo[]) => {
    setTasks(newTasks);
    localStorage.setItem('video_tasks', JSON.stringify(newTasks));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!url) return;

    setSubmitting(true);
    setError(null);
    setResult(null);

    try {
      const response: TaskSubmitResponse = await submitVideoTask(url, {
        format,
        language,
      });

      const newTask: TaskInfo = {
        taskId: response.task_id,
        url,
        submittedAt: new Date(),
      };

      setCurrentTask(newTask);
      saveTasks([...tasks, newTask]);
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
    } catch (err) {
      setError(err instanceof Error ? err.message : '取消失败');
    }
  };

  const handleViewTask = async (taskId: string) => {
    setCurrentTask({ taskId, url: '', submittedAt: new Date() });
    setResult(null);
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

  return (
    <div className="space-y-lg">
      {/* Header */}
      <div>
        <h1 className="text-h1 text-primary">视频内容总结</h1>
        <p className="text-secondary mt-sm">
          输入视频链接，自动下载、转录并生成学习笔记
        </p>
      </div>

      {/* Form */}
      <form onSubmit={handleSubmit} className="space-y-md">
        <div>
          <label className="block text-sm font-medium text-primary mb-xs">
            视频链接 (B站/YouTube/抖音)
          </label>
          <input
            type="url"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="https://www.bilibili.com/video/BV..."
            className="input w-full"
            required
          />
        </div>

        {/* Settings */}
        <div className="flex flex-wrap gap-lg">
          <div>
            <label className="block text-sm font-medium text-primary mb-xs">
              输出格式
            </label>
            <select
              value={format}
              onChange={(e) => setFormat(e.target.value)}
              className="input"
            >
              <option value="markdown">Markdown</option>
              <option value="pdf">PDF</option>
              <option value="both">两者</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-primary mb-xs">
              总结语言
            </label>
            <select
              value={language}
              onChange={(e) => setLanguage(e.target.value)}
              className="input"
            >
              <option value="zh">中文</option>
              <option value="en">英文</option>
            </select>
          </div>
        </div>

        <button
          type="submit"
          disabled={submitting || !url || isPolling}
          className="btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {submitting ? '提交中...' : '提交任务'}
        </button>
      </form>

      {/* Error */}
      {error && (
        <div className="bg-highlight-red rounded-md p-md">
          <p className="text-error">{error}</p>
        </div>
      )}

      {/* Task status */}
      {status && (
        <div className="card">
          <div className="flex items-center justify-between mb-md">
            <div>
              <h3 className="text-h3 text-primary">任务状态</h3>
              <p className="text-sm text-secondary">Task ID: {status.task_id}</p>
            </div>
            <div className={`px-md py-sm rounded-full text-sm font-medium ${
              status.status === 'completed' ? 'bg-highlight-green text-success' :
              status.status === 'running' ? 'bg-highlight-blue text-info' :
              status.status === 'failed' ? 'bg-highlight-red text-error' :
              'bg-surface text-secondary'
            }`}>
              {status.status === 'completed' ? '已完成' :
               status.status === 'running' ? '处理中' :
               status.status === 'failed' ? '失败' :
               status.status === 'cancelled' ? '已取消' : '等待中'}
            </div>
          </div>

          {/* Progress bar */}
          {status.status === 'running' && (
            <div className="mb-md">
              <div className="flex items-center justify-between mb-xs">
                <span className="text-sm text-secondary">{status.message}</span>
                <span className="text-sm text-accent">{Math.round(status.progress * 100)}%</span>
              </div>
              <div className="w-full h-2 bg-border rounded-full overflow-hidden">
                <div
                  className="h-full bg-accent transition-all duration-300"
                  style={{ width: `${status.progress * 100}%` }}
                />
              </div>
            </div>
          )}

          {/* Cancel button */}
          {status.status === 'running' && (
            <button
              onClick={handleCancelTask}
              className="btn-secondary text-error"
            >
              取消任务
            </button>
          )}

          {/* Error message */}
          {status.error && (
            <p className="text-error">{status.error}</p>
          )}
        </div>
      )}

      {/* Task list */}
      {tasks.length > 0 && (
        <div className="card">
          <h3 className="text-h3 text-primary mb-md">历史任务</h3>
          <div className="space-y-xs">
            {tasks.slice(0, 5).map((task) => (
              <div
                key={task.taskId}
                className="flex items-center justify-between p-sm bg-white rounded-md border border-border"
              >
                <div className="flex items-center gap-sm">
                  <span className="text-xs text-secondary font-mono">
                    #{task.taskId.slice(0, 8)}
                  </span>
                  <span className="text-sm text-primary truncate max-w-[200px]">
                    {task.url}
                  </span>
                </div>
                <button
                  onClick={() => handleViewTask(task.taskId)}
                  className="text-sm text-accent hover:underline"
                >
                  查看
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Result */}
      {result && (
        <div className="card space-y-md">
          <div>
            <h2 className="text-h2 text-primary">{result.title}</h2>
            <p className="text-sm text-secondary mt-xs">
              {(result.metadata?.duration as string | number | undefined)?.toString() || ''} · {(result.metadata?.platform as string | undefined) || ''}
            </p>
          </div>

          {/* Summary */}
          <div>
            <h3 className="text-h3 text-primary mb-sm">内容总结</h3>
            <p className="text-primary leading-relaxed whitespace-pre-wrap">
              {result.summary?.content || ''}
            </p>
          </div>

          {/* Key points */}
          {result.summary?.key_points && result.summary.key_points.length > 0 && (
            <div>
              <h3 className="text-h3 text-primary mb-sm">核心要点</h3>
              <ul className="space-y-xs">
                {result.summary.key_points.map((point, i) => (
                  <li key={i} className="flex items-start gap-sm">
                    <span className="text-accent">•</span>
                    <span className="text-primary">{point}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Transcript preview */}
          {result.transcript && (
            <div>
              <h3 className="text-h3 text-primary mb-sm">字幕预览</h3>
              <div className="bg-highlight-yellow rounded-md p-md font-mono text-sm text-primary max-h-[200px] overflow-y-auto whitespace-pre-wrap">
                {result.transcript.slice(0, 500)}...
              </div>
            </div>
          )}

          {/* Actions */}
          <div className="flex gap-sm pt-md border-t border-border">
            <button
              onClick={handleExportMarkdown}
              className="btn-secondary hover:bg-highlight-yellow"
            >
              导出 Markdown
            </button>
            <button
              onClick={handleExportPdf}
              className="btn-secondary hover:bg-highlight-blue"
            >
              导出 PDF
            </button>
            <button
              onClick={handleDownloadTranscript}
              disabled={!result?.transcript}
              className="btn-secondary hover:bg-highlight-green disabled:opacity-50 disabled:cursor-not-allowed"
            >
              下载字幕
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default VideoPage;