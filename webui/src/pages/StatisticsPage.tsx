import React, { useState, useEffect } from 'react';
import { getStatistics, Statistics } from '../services/api';

const StatisticsPage: React.FC = () => {
  const [stats, setStats] = useState<Statistics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadStatistics();
  }, []);

  const loadStatistics = async () => {
    setLoading(true);
    setError(null);

    try {
      const data = await getStatistics();
      setStats(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : '加载失败');
    } finally {
      setLoading(false);
    }
  };

  const formatDuration = (seconds: number) => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    if (hours > 0) {
      return `${hours}小时${minutes}分钟`;
    }
    return `${minutes}分钟`;
  };

  return (
    <div className="space-y-lg">
      {/* Header */}
      <div>
        <h1 className="text-h1 text-primary">学习统计</h1>
        <p className="text-secondary mt-sm">
          查看您的学习数据和进度
        </p>
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

      {/* Stats */}
      {!loading && stats && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-lg">
          {/* Total videos */}
          <div className="card text-center">
            <div className="text-4xl font-semibold text-accent mb-sm">
              {stats.total_videos}
            </div>
            <div className="text-secondary">视频总数</div>
          </div>

          {/* Total duration */}
          <div className="card text-center">
            <div className="text-4xl font-semibold text-accent-secondary mb-sm">
              {formatDuration(stats.total_duration)}
            </div>
            <div className="text-secondary">学习时长</div>
          </div>

          {/* Most watched platform */}
          <div className="card text-center">
            <div className="text-4xl font-semibold text-primary mb-sm">
              {stats.most_watched_platform || '-'}
            </div>
            <div className="text-secondary">常用平台</div>
          </div>
        </div>
      )}

      {/* Recent activity */}
      {!loading && stats && stats.recent_activity && stats.recent_activity.length > 0 && (
        <div className="card">
          <h3 className="text-h3 text-primary mb-md">最近活动</h3>
          <div className="space-y-xs">
            {stats.recent_activity.slice(0, 7).map((_activity, i) => (
              <div key={i} className="flex items-center gap-sm p-sm bg-white rounded-md">
                <span className="text-xs text-secondary">
                  {new Date().toLocaleDateString('zh-CN', { weekday: 'short' })}
                </span>
                <div className="flex-1 h-2 bg-border rounded-full overflow-hidden">
                  <div
                    className="h-full bg-accent"
                    style={{ width: '50%' }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Empty state */}
      {!loading && !stats && (
        <div className="text-center py-xl text-secondary">
          <p>暂无统计数据，开始学习后将自动记录</p>
        </div>
      )}
    </div>
  );
};

export default StatisticsPage;