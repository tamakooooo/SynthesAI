import React, { useState } from 'react';
import { setApiKey, healthCheck } from '../services/api';
import { useApiKey } from '../hooks/useLocalStorage';

const SettingsPage: React.FC = () => {
  const { apiKey, setApiKey: updateApiKey } = useApiKey();
  const [inputKey, setInputKey] = useState(apiKey || '');
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState<string | null>(null);

  const handleSaveKey = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);

    try {
      setApiKey(inputKey);
      updateApiKey(inputKey);
      setTestResult('API Key 已保存');
    } catch (err) {
      setTestResult('保存失败');
    } finally {
      setSaving(false);
    }
  };

  const handleTestConnection = async () => {
    setTesting(true);
    setTestResult(null);

    try {
      const result = await healthCheck();
      setTestResult(`连接成功: ${result.status}`);
    } catch (err) {
      setTestResult(`连接失败: ${err instanceof Error ? err.message : '网络错误'}`);
    } finally {
      setTesting(false);
    }
  };

  return (
    <div className="space-y-lg">
      {/* Header */}
      <div>
        <h1 className="text-h1 text-primary">设置</h1>
        <p className="text-secondary mt-sm">
          配置 API Key 和连接设置
        </p>
      </div>

      {/* API Key */}
      <div className="card">
        <h3 className="text-h3 text-primary mb-md">API Key</h3>
        <form onSubmit={handleSaveKey} className="space-y-md">
          <div>
            <label className="block text-sm font-medium text-primary mb-xs">
              SynthesAI API Key
            </label>
            <input
              type="password"
              value={inputKey}
              onChange={(e) => setInputKey(e.target.value)}
              placeholder="输入 API Key..."
              className="input w-full"
            />
          </div>

          <div className="flex gap-sm">
            <button
              type="submit"
              disabled={saving}
              className="btn-primary disabled:opacity-50"
            >
              {saving ? '保存中...' : '保存'}
            </button>

            <button
              type="button"
              onClick={handleTestConnection}
              disabled={testing}
              className="btn-secondary disabled:opacity-50"
            >
              {testing ? '测试中...' : '测试连接'}
            </button>
          </div>

          {testResult && (
            <p className={`text-sm ${
              testResult.includes('成功') ? 'text-success' : 'text-error'
            }`}>
              {testResult}
            </p>
          )}
        </form>
      </div>

      {/* Info */}
      <div className="card">
        <h3 className="text-h3 text-primary mb-md">关于</h3>
        <div className="space-y-sm text-secondary">
          <p><strong className="text-primary">版本:</strong> v0.2.0</p>
          <p><strong className="text-primary">后端:</strong> http://localhost:8000</p>
          <p className="text-sm">
            SynthesAI 是一个 AI 驱动的学习助手，帮助您从视频、文章中提取知识，
            生成结构化的学习笔记和词汇卡片。
          </p>
        </div>
      </div>
    </div>
  );
};

export default SettingsPage;