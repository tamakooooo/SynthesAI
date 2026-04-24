import React, { useState, useEffect } from 'react';
import QRCode from 'qrcode';
import {
  setApiKey,
  healthCheck,
  getLLMConfig,
  updateLLMConfig,
  testLLMConnection,
  setProviderAPIKey,
  fetchAvailableModels,
  LLMConfig,
  getAuthStatus,
  importCookies,
  logoutPlatform,
  getLoginHelp,
  getBilibiliQRCode,
  pollBilibiliQRStatus,
  AllPlatformsStatus,
} from '../services/api';
import { useApiKey } from '../hooks/useLocalStorage';

const SettingsPage: React.FC = () => {
  const { apiKey, setApiKey: updateApiKey } = useApiKey();
  const [inputKey, setInputKey] = useState(apiKey || '');
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState<string | null>(null);

  // LLM Config state
  const [llmConfig, setLLMConfig] = useState<LLMConfig | null>(null);
  const [selectedProvider, setSelectedProvider] = useState<string>('');
  const [selectedModel, setSelectedModel] = useState<string>('');
  const [baseUrl, setBaseUrl] = useState<string>('');
  const [llmApiKey, setLLMApiKey] = useState<string>('');
  const [fetchedModels, setFetchedModels] = useState<string[]>([]);
  const [loadingConfig, setLoadingConfig] = useState(true);
  const [savingLLM, setSavingLLM] = useState(false);
  const [testingLLM, setTestingLLM] = useState(false);
  const [savingApiKey, setSavingApiKey] = useState(false);
  const [fetchingModels, setFetchingModels] = useState(false);

  // Auth state
  const [authStatus, setAuthStatus] = useState<AllPlatformsStatus | null>(null);
  const [loadingAuth, setLoadingAuth] = useState(true);
  const [qrCodeImage, setQrCodeImage] = useState<string | null>(null);
  const [qrSessionKey, setQrSessionKey] = useState<string | null>(null);
  const [qrPlatform, setQrPlatform] = useState<string | null>(null);
  const [qrPolling, setQrPolling] = useState(false);
  const [importingCookies, setImportingCookies] = useState(false);
  const [cookieInput, setCookieInput] = useState<{ [key: string]: string }>({
    douyin: '',
    bilibili: '',
  });
  const [platformHelp, setPlatformHelp] = useState<{ [key: string]: any }>({});

  // Load configs on mount
  useEffect(() => {
    loadLLMConfig();
    loadAuthStatus();
    loadPlatformHelp();
  }, []);

  // QR polling effect - Backend proxy approach
  useEffect(() => {
    if (!qrPolling || !qrPlatform || !qrSessionKey) return;

    const pollInterval = setInterval(async () => {
      try {
        if (qrPlatform === 'bilibili') {
          const result = await pollBilibiliQRStatus(qrSessionKey);

          if (result.authenticated) {
            setQrPolling(false);
            setQrCodeImage(null);
            setQrSessionKey(null);
            setQrPlatform(null);
            setTestResult('B站 登录成功！');
            loadAuthStatus();
          } else if (result.status === 'expired') {
            setQrPolling(false);
            setQrCodeImage(null);
            setQrSessionKey(null);
            setQrPlatform(null);
            setTestResult('二维码已过期，请重新获取');
          } else if (result.status === 'scanned') {
            setTestResult('已扫码，请在手机上确认登录');
          }
        }
      } catch (err) {
        console.error('QR poll error:', err);
      }
    }, 2000);

    return () => clearInterval(pollInterval);
  }, [qrPolling, qrPlatform, qrSessionKey]);

  const loadLLMConfig = async () => {
    setLoadingConfig(true);
    try {
      const config = await getLLMConfig();
      setLLMConfig(config);
      setSelectedProvider(config.default_provider);
      const provider = config.providers.find(p => p.name === config.default_provider);
      if (provider) {
        setSelectedModel(provider.default_model);
        setBaseUrl(provider.base_url || '');
      }
    } catch (err) {
      console.error('Failed to load LLM config:', err);
    } finally {
      setLoadingConfig(false);
    }
  };

  const loadAuthStatus = async () => {
    setLoadingAuth(true);
    try {
      const status = await getAuthStatus();
      setAuthStatus(status);
    } catch (err) {
      console.error('Failed to load auth status:', err);
    } finally {
      setLoadingAuth(false);
    }
  };

  const loadPlatformHelp = async () => {
    const helps: { [key: string]: any } = {};
    for (const platform of ['bilibili', 'douyin', 'youtube']) {
      try {
        helps[platform] = await getLoginHelp(platform);
      } catch (err) {
        console.error(`Failed to load help for ${platform}:`, err);
      }
    }
    setPlatformHelp(helps);
  };

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

  const handleProviderChange = (providerName: string) => {
    setSelectedProvider(providerName);
    const provider = llmConfig?.providers.find(p => p.name === providerName);
    if (provider) {
      setSelectedModel(provider.default_model);
      setBaseUrl(provider.base_url || '');
    }
    setLLMApiKey(''); // Clear API key input when switching provider
  };

  const handleSaveLLMApiKey = async () => {
    if (!llmApiKey.trim()) {
      setTestResult('请输入 API Key');
      return;
    }
    setSavingApiKey(true);
    setTestResult(null);
    try {
      const result = await setProviderAPIKey(selectedProvider, llmApiKey);
      if (result.success) {
        setTestResult(`${selectedProvider} API Key 已保存到 settings.local.yaml`);
        // Keep the API key in the input field after saving
        loadLLMConfig(); // Reload config to update "configured" status
      } else {
        setTestResult(`保存失败: ${result.message}`);
      }
    } catch (err) {
      setTestResult(`保存失败: ${err instanceof Error ? err.message : '网络错误'}`);
    } finally {
      setSavingApiKey(false);
    }
  };

  const handleSaveLLMConfig = async () => {
    setSavingLLM(true);
    setTestResult(null);
    try {
      const result = await updateLLMConfig({
        provider: selectedProvider,
        base_url: baseUrl || undefined,
        default_model: selectedModel,
      });
      if (result.success) {
        setTestResult('LLM 配置已更新');
        if (result.config) {
          setLLMConfig(result.config);
        }
      } else {
        setTestResult(`更新失败: ${result.message}`);
      }
    } catch (err) {
      setTestResult(`更新失败: ${err instanceof Error ? err.message : '网络错误'}`);
    } finally {
      setSavingLLM(false);
    }
  };

  const handleTestLLM = async () => {
    setTestingLLM(true);
    setTestResult(null);
    try {
      const result = await testLLMConnection(selectedProvider, selectedModel);
      if (result.success) {
        setTestResult(`LLM 测试成功: ${result.message}`);
      } else {
        setTestResult(`LLM 测试失败: ${result.message}`);
      }
    } catch (err) {
      setTestResult(`测试失败: ${err instanceof Error ? err.message : '网络错误'}`);
    } finally {
      setTestingLLM(false);
    }
  };

  const handleFetchModels = async () => {
    setFetchingModels(true);
    setTestResult(null);
    try {
      const models = await fetchAvailableModels(selectedProvider);
      setFetchedModels(models);
      setTestResult(`获取到 ${models.length} 个模型`);
    } catch (err) {
      setTestResult(`获取模型失败: ${err instanceof Error ? err.message : '网络错误'}`);
    } finally {
      setFetchingModels(false);
    }
  };

  // Bilibili QR login - Backend proxy approach
  const handleQRLogin = async (platform: string) => {
    setTestResult(null);

    if (platform === 'bilibili') {
      try {
        setTestResult('正在获取二维码...');
        const result = await getBilibiliQRCode();

        // Generate QR code image from URL
        const qrImageData = await QRCode.toDataURL(result.qr_url, {
          width: 256,
          margin: 2,
        });

        setQrCodeImage(qrImageData);
        setQrSessionKey(result.session_key);
        setQrPlatform(platform);
        setQrPolling(true);
        setTestResult('请使用 B站 手机 App 扫描二维码');
      } catch (err: any) {
        setTestResult(err.message || '获取二维码失败');
      }
    }
  };

  const handleImportCookies = async (platform: string) => {
    const cookies = cookieInput[platform];
    if (!cookies.trim()) {
      setTestResult('请输入 Cookie 内容');
      return;
    }
    setImportingCookies(true);
    setTestResult(null);
    try {
      const result = await importCookies(platform, cookies);
      if (result.success) {
        setTestResult(`${platform} Cookie 导入成功`);
        setCookieInput({ ...cookieInput, [platform]: '' });
        loadAuthStatus();
      } else {
        setTestResult(`导入失败: ${result.message}`);
      }
    } catch (err) {
      setTestResult(`导入失败: ${err instanceof Error ? err.message : '网络错误'}`);
    } finally {
      setImportingCookies(false);
    }
  };

  const handleLogout = async (platform: string) => {
    setTestResult(null);
    try {
      const result = await logoutPlatform(platform);
      if (result.success) {
        setTestResult(`${platform} 已登出`);
        loadAuthStatus();
      } else {
        setTestResult(`登出失败: ${result.message}`);
      }
    } catch (err) {
      setTestResult(`登出失败: ${err instanceof Error ? err.message : '网络错误'}`);
    }
  };

  const getStatusBadge = (status: string) => {
    if (status === 'authenticated') {
      return <span className="bg-highlight-green text-success px-sm py-xs rounded-full text-xs">已登录 ✓</span>;
    } else if (status === 'expired') {
      return <span className="bg-highlight-yellow text-warning px-sm py-xs rounded-full text-xs">已过期</span>;
    } else if (status === 'error') {
      return <span className="bg-highlight-red text-error px-sm py-xs rounded-full text-xs">错误</span>;
    }
    return <span className="bg-border text-secondary px-sm py-xs rounded-full text-xs">未登录</span>;
  };

  const currentProvider = llmConfig?.providers.find(p => p.name === selectedProvider);

  return (
    <div className="space-y-lg">
      {/* Header */}
      <div>
        <h1 className="text-h1 text-primary">设置</h1>
        <p className="text-secondary mt-sm">
          配置 API Key、LLM 模型及平台登录
        </p>
      </div>

      {/* Platform Authentication */}
      <div className="card">
        <h3 className="text-h3 text-primary mb-md">平台登录认证</h3>

        {loadingAuth ? (
          <div className="text-center py-md">
            <div className="animate-spin w-6 h-6 border-2 border-accent border-t-transparent rounded-full mx-auto" />
            <p className="text-secondary mt-sm">加载登录状态...</p>
          </div>
        ) : authStatus ? (
          <div className="space-y-md">
            {authStatus.platforms.map((p) => (
              <div key={p.platform} className="bg-white rounded-md p-md border border-border">
                <div className="flex items-center justify-between mb-sm">
                  <div className="flex items-center gap-md">
                    <span className="text-primary font-medium capitalize">{p.platform}</span>
                    {getStatusBadge(p.status)}
                  </div>
                  {p.username && <span className="text-secondary text-sm">{p.username}</span>}
                </div>

                {p.message && <p className="text-xs text-secondary mb-sm">{p.message}</p>}

                {/* Bilibili - QR + Manual Cookie */}
                {p.platform === 'bilibili' && (
                  <div className="mt-sm space-y-sm">
                    {p.status !== 'authenticated' && (
                      <>
                        {/* Manual Cookie Import - Primary method */}
                        <div className="bg-highlight-yellow rounded-md p-sm mb-sm">
                          <p className="text-xs text-warning font-medium">
                            ⚠️ QR扫码登录需要服务器能访问B站API，如果网络受限请使用手动Cookie导入
                          </p>
                        </div>

                        {/* QR Login */}
                        <div className="flex gap-sm items-center">
                          <button
                            onClick={() => handleQRLogin('bilibili')}
                            disabled={qrPolling}
                            className="btn-secondary disabled:opacity-50"
                          >
                            {qrPolling ? '等待扫码...' : '尝试扫码登录'}
                          </button>
                          <span className="text-xs text-secondary">或使用手动导入</span>
                        </div>

                        {/* Manual Cookie Import */}
                        <textarea
                          value={cookieInput.bilibili}
                          onChange={(e) => setCookieInput({ ...cookieInput, bilibili: e.target.value })}
                          placeholder="粘贴 JSON Cookie (浏览器扩展导出的JSON数组) 或 Cookie字符串"
                          className="input w-full min-h-[120px] resize-y text-sm"
                        />
                        <div className="flex gap-sm">
                          <button
                            onClick={() => handleImportCookies('bilibili')}
                            disabled={importingCookies || !cookieInput.bilibili.trim()}
                            className="btn-primary disabled:opacity-50"
                          >
                            {importingCookies ? '导入中...' : '导入 Cookie'}
                          </button>
                        </div>
                      </>
                    )}
                    {p.status === 'authenticated' && (
                      <button
                        onClick={() => handleLogout('bilibili')}
                        className="btn-secondary"
                      >
                        登出
                      </button>
                    )}
                    {platformHelp.bilibili && (
                      <div className="mt-sm text-xs text-secondary bg-highlight-blue rounded-md p-sm">
                        <p className="font-medium mb-xs">获取 Cookie 方法:</p>
                        <p>1. 安装浏览器扩展「Get cookies.txt」</p>
                        <p>2. 登录 bilibili.com</p>
                        <p>3. 点击扩展导出 Cookie (JSON格式)</p>
                        <p>4. 粘贴到上方输入框并导入</p>
                        <p className="mt-xs">或手动复制: SESSDATA=xxx; DedeUserID=xxx; bili_jct=xxx</p>
                      </div>
                    )}
                  </div>
                )}

                {/* Manual import for Douyin */}
                {p.platform === 'douyin' && (
                  <div className="mt-sm space-y-sm">
                    {p.status !== 'authenticated' && (
                      <>
                        <textarea
                          value={cookieInput.douyin}
                          onChange={(e) => setCookieInput({ ...cookieInput, douyin: e.target.value })}
                          placeholder="粘贴从浏览器获取的 Cookie..."
                          className="input w-full min-h-[80px] resize-y text-sm"
                        />
                        <div className="flex gap-sm">
                          <button
                            onClick={() => handleImportCookies('douyin')}
                            disabled={importingCookies || !cookieInput.douyin.trim()}
                            className="btn-primary disabled:opacity-50"
                          >
                            {importingCookies ? '导入中...' : '导入 Cookie'}
                          </button>
                        </div>
                      </>
                    )}
                    {p.status === 'authenticated' && (
                      <button
                        onClick={() => handleLogout('douyin')}
                        className="btn-secondary"
                      >
                        登出
                      </button>
                    )}
                    {platformHelp.douyin && (
                      <div className="mt-sm text-xs text-secondary bg-highlight-yellow rounded-md p-sm">
                        <p className="font-medium mb-xs">获取 Cookie 方法:</p>
                        {platformHelp.douyin.steps?.map((step: string, i: number) => (
                          <p key={i}>{i + 1}. {step}</p>
                        ))}
                        {platformHelp.douyin.required_cookies && (
                          <p className="mt-xs">需要包含: {platformHelp.douyin.required_cookies.join(', ')}</p>
                        )}
                      </div>
                    )}
                  </div>
                )}

                {/* YouTube info */}
                {p.platform === 'youtube' && (
                  <div className="mt-sm text-xs text-secondary bg-highlight-blue rounded-md p-sm">
                    <p className="font-medium mb-xs">YouTube Cookie 配置:</p>
                    {platformHelp.youtube?.steps?.map((step: string, i: number) => (
                      <p key={i}>{i + 1}. {step}</p>
                    ))}
                    <p className="mt-xs">Cookie 文件路径: config/cookies/youtube_cookies.txt</p>
                  </div>
                )}
              </div>
            ))}
          </div>
        ) : (
          <p className="text-secondary">无法加载登录状态</p>
        )}

        {/* QR Code Display */}
        {qrCodeImage && (
          <div className="mt-md text-center">
            <div className="bg-white rounded-lg p-md border-2 border-accent inline-block">
              <img src={qrCodeImage} alt="QR Code" className="w-64 h-64 mx-auto" />
              <p className="text-sm text-secondary mt-sm">{qrPlatform} 扫码登录</p>
              {qrPolling && <p className="text-xs text-accent animate-pulse">等待扫码...</p>}
            </div>
          </div>
        )}
      </div>

      {/* LLM Configuration */}
      <div className="card">
        <h3 className="text-h3 text-primary mb-md">LLM 大模型配置</h3>

        {loadingConfig ? (
          <div className="text-center py-md">
            <div className="animate-spin w-6 h-6 border-2 border-accent border-t-transparent rounded-full mx-auto" />
            <p className="text-secondary mt-sm">加载配置...</p>
          </div>
        ) : llmConfig ? (
          <div className="space-y-md">
            {/* Provider Selection */}
            <div>
              <label className="block text-sm font-medium text-primary mb-xs">
                Provider (服务商)
              </label>
              <select
                value={selectedProvider}
                onChange={(e) => handleProviderChange(e.target.value)}
                className="input w-full"
              >
                {llmConfig.providers.map((p) => (
                  <option key={p.name} value={p.name}>
                    {p.name} {p.configured ? '✓' : '(未配置)'}
                  </option>
                ))}
              </select>
              {currentProvider && (
                <p className="text-xs mt-xs">
                  {currentProvider.configured
                    ? <span className="text-success">API Key 已配置 ✓</span>
                    : <span className="text-warning">API Key 未配置，请输入后保存</span>
                  }
                </p>
              )}
            </div>

            {/* API Key Input */}
            <div>
              <label className="block text-sm font-medium text-primary mb-xs">
                LLM API Key
              </label>
              <div className="flex gap-sm">
                <input
                  type="password"
                  value={llmApiKey}
                  onChange={(e) => setLLMApiKey(e.target.value)}
                  placeholder={`输入 ${selectedProvider} API Key...`}
                  className="input flex-1"
                />
                <button
                  onClick={handleSaveLLMApiKey}
                  disabled={savingApiKey || !llmApiKey.trim()}
                  className="btn-primary disabled:opacity-50"
                >
                  {savingApiKey ? '保存中...' : '保存 Key'}
                </button>
              </div>
              <p className="text-xs text-secondary mt-xs">
                API Key 将保存到 config/settings.local.yaml 文件中
              </p>
            </div>

            {/* Base URL */}
            <div>
              <label className="block text-sm font-medium text-primary mb-xs">
                API Base URL (接口地址)
              </label>
              <input
                type="url"
                value={baseUrl}
                onChange={(e) => setBaseUrl(e.target.value)}
                placeholder="https://api.openai.com/v1"
                className="input w-full"
              />
              <p className="text-xs text-secondary mt-xs">
                自定义 API 地址，支持 OpenAI 兼容接口
              </p>
            </div>

            {/* Model Selection */}
            <div>
              <label className="block text-sm font-medium text-primary mb-xs">
                Default Model (默认模型)
              </label>
              <div className="flex gap-sm mb-sm">
                <select
                  value={selectedModel}
                  onChange={(e) => setSelectedModel(e.target.value)}
                  className="input flex-1"
                >
                  {/* Use fetched models if available, otherwise use config models */}
                  {(fetchedModels.length > 0 ? fetchedModels : currentProvider?.models || []).map((m) => (
                    <option key={m} value={m}>{m}</option>
                  ))}
                </select>
                <input
                  type="text"
                  value={selectedModel}
                  onChange={(e) => setSelectedModel(e.target.value)}
                  placeholder="自定义模型名"
                  className="input"
                />
              </div>
              <button
                onClick={handleFetchModels}
                disabled={fetchingModels || !currentProvider?.configured}
                className="btn-secondary disabled:opacity-50 text-sm"
              >
                {fetchingModels ? '获取中...' : '🔄 从 API 获取模型列表'}
              </button>
              {!currentProvider?.configured && (
                <p className="text-xs text-warning mt-xs">需要先配置 API Key 才能获取模型</p>
              )}
              {fetchedModels.length > 0 && (
                <p className="text-xs text-success mt-xs">已获取 {fetchedModels.length} 个模型</p>
              )}
            </div>

            {/* Actions */}
            <div className="flex gap-sm">
              <button
                onClick={handleSaveLLMConfig}
                disabled={savingLLM}
                className="btn-primary disabled:opacity-50"
              >
                {savingLLM ? '保存中...' : '保存配置'}
              </button>
              <button
                onClick={handleTestLLM}
                disabled={testingLLM}
                className="btn-secondary disabled:opacity-50"
              >
                {testingLLM ? '测试中...' : '测试连接'}
              </button>
            </div>

            {/* Available Models Info */}
            {currentProvider && (
              <div className="bg-highlight-blue rounded-md p-md mt-md">
                <p className="text-sm text-primary font-medium mb-xs">
                  {currentProvider.name} 可用模型:
                </p>
                <div className="flex flex-wrap gap-xs">
                  {currentProvider.models.map((m) => (
                    <span
                      key={m}
                      className={`tag cursor-pointer ${m === selectedModel ? 'bg-accent text-white' : ''}`}
                      onClick={() => setSelectedModel(m)}
                    >
                      {m}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        ) : (
          <p className="text-secondary">无法加载 LLM 配置</p>
        )}
      </div>

      {/* API Key */}
      <div className="card">
        <h3 className="text-h3 text-primary mb-md">API Key</h3>
        <form onSubmit={handleSaveKey} className="space-y-md">
          <div>
            <label className="block text-sm font-medium text-primary mb-xs">
              SynthesAI Server API Key
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
        </form>
      </div>

      {/* Result Message */}
      {testResult && (
        <div className={`rounded-md p-md ${
          testResult.includes('成功') ? 'bg-highlight-green' :
          testResult.includes('失败') || testResult.includes('错误') ? 'bg-highlight-red' : 'bg-highlight-yellow'
        }`}>
          <p className={`${
            testResult.includes('成功') ? 'text-success' :
            testResult.includes('失败') || testResult.includes('错误') ? 'text-error' : 'text-warning'
          }`}>
            {testResult}
          </p>
        </div>
      )}

      {/* Info */}
      <div className="card">
        <h3 className="text-h3 text-primary mb-md">关于</h3>
        <div className="space-y-sm text-secondary">
          <p><strong className="text-primary">版本:</strong> v0.2.0</p>
          <p><strong className="text-primary">当前 Provider:</strong> {llmConfig?.default_provider || 'openai'}</p>
          <p><strong className="text-primary">当前 Model:</strong> {selectedModel || '未设置'}</p>
          <p className="text-sm">
            SynthesAI 是一个 AI 驱动的学习助手，支持 B站/抖音/YouTube 视频总结，
            网页知识卡片生成，词汇提取与学习。
          </p>
        </div>
      </div>
    </div>
  );
};

export default SettingsPage;