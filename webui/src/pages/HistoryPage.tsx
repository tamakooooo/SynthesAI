import React, { useState, useEffect } from 'react';
import { getHistory, HistoryRecord } from '../services/api';

const HistoryPage: React.FC = () => {
  const [records, setRecords] = useState<HistoryRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState('');
  const [moduleFilter, setModuleFilter] = useState('');

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
            <div key={record.id} className="card">
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
    </div>
  );
};

export default HistoryPage;