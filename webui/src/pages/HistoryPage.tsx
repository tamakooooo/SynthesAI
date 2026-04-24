import React, { useState, useEffect } from 'react';
import { getHistory, getVideoTaskResult, HistoryRecord, VideoResult } from '../services/api';
import {
  videoResultToMarkdown,
  exportMarkdown,
  exportPdfViaPrint,
  downloadTranscript,
  sanitizeFilename,
  getTimestamp,
} from '../utils/export';

const HistoryPage: React.FC = () => {
  const [records, setRecords] = useState<HistoryRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState('');
  const [moduleFilter, setModuleFilter] = useState('');
  const [selectedRecord, setSelectedRecord] = useState<HistoryRecord | null>(null);
  const [result, setResult] = useState<VideoResult | null>(null);
  const [loadingResult, setLoadingResult] = useState(false);

  useEffect(() => {
    loadHistory();
  }, [search, moduleFilter]);

  const loadHistory = async () => {
    setLoading(true);
    setError(null);

    try {
      const data = await getHistory({
        limit: 50,
        search: search || undefined,
        module: moduleFilter || undefined,
      });
      setRecords(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : '加载失败');
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'bg-highlight-green text-success';
      case 'in_progress':
        return 'bg-highlight-blue text-info';
      case 'failed':
        return 'bg-highlight-red text-error';
      default:
        return 'bg-surface text-secondary';
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

  const handleViewRecord = async (record: HistoryRecord) => {
    setSelectedRecord(record);
    setResult(null);
    setError(null);

    if (record.module === 'video_summary') {
      setLoadingResult(true);
      try {
        const videoResult = await getVideoTaskResult(record.id);
        setResult(videoResult);
      } catch (err) {
        setError(err instanceof Error ? err.message : '获取结果失败');
      } finally {
        setLoadingResult(false);
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

  return (
    <div className="space-y-lg">
      {/* Header */}
      <div>
        <h1 className="text-h1 text-primary">学习历史</h1>
        <p className="text-secondary mt-sm">
          查看您的学习记录和进度
        </p>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-md">
        <div className="flex-1 min-w-[200px]">
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="搜索..."
            className="input w-full"
          />
        </div>

        <select
          value={moduleFilter}
          onChange={(e) => setModuleFilter(e.target.value)}
          className="input"
        >
          <option value="">全部类型</option>
          <option value="video_summary">视频</option>
          <option value="link_learning">链接</option>
          <option value="vocabulary">词汇</option>
        </select>
      </div>

      {/* Error */}
      {error && (
        <div className="bg-highlight-red rounded-md p-md">
          <p className="text-error">{error}</p>
        </div>
      )}

      {/* Loading */}
      {loading && (
        <div className="text-center py-xl">
          <div className="animate-spin w-8 h-8 border-2 border-accent border-t-transparent rounded-full mx-auto" />
        </div>
      )}

      {/* Records */}
      {!loading && records.length === 0 && (
        <div className="text-center py-xl text-secondary">
          <p>暂无学习记录</p>
        </div>
      )}

      {!loading && records.length > 0 && (
        <div className="space-y-sm">
          {records.map((record) => (
            <div
              key={record.id}
              onClick={() => handleViewRecord(record)}
              className={`card cursor-pointer transition-all ${
                selectedRecord?.id === record.id
                  ? 'border-blue-500 bg-blue-50 ring-2 ring-blue-200'
                  : 'hover:border-gray-300 hover:bg-gray-50'
              }`}
            >
              <div className="flex items-start justify-between gap-md">
                {/* Status and info */}
                <div className="flex items-center gap-sm">
                  <span className={`px-sm py-xs rounded-full text-xs font-medium ${getStatusColor(record.status)}`}>
                    {record.status === 'completed' ? '已完成' :
                     record.status === 'in_progress' ? '进行中' : '失败'}
                  </span>
                  <span className="tag">{getModuleLabel(record.module)}</span>
                </div>

                {/* Timestamp */}
                <span className="text-sm text-secondary">
                  {new Date(record.timestamp).toLocaleString('zh-CN')}
                </span>
              </div>

              {/* Title */}
              <h3 className="text-lg font-medium text-primary mt-sm">
                {record.title || '(无标题)'}
              </h3>

              {/* URL */}
              {record.url && (
                <p className="text-sm text-secondary truncate mt-xs">
                  {record.url}
                </p>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Loading result */}
      {loadingResult && (
        <div className="text-center py-xl">
          <div className="animate-spin w-8 h-8 border-2 border-accent border-t-transparent rounded-full mx-auto" />
          <p className="text-secondary mt-sm">加载结果中...</p>
        </div>
      )}

      {/* Result Display */}
      {result && selectedRecord && (
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

export default HistoryPage;