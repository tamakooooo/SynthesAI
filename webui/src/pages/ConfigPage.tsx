import React, { useEffect, useState } from 'react';
import {
  checkFeishuConfiguration,
  fetchAvailableModels,
  FeishuConfiguration,
  FeishuCheckResult,
  ModuleConfiguration,
  publishFeishuTestDocument,
  ServerConfiguration,
  verifyFeishuConfiguration,
  FrontendConfiguration,
  FrontendProviderConfig,
  getFrontendConfiguration,
  healthCheck,
  saveFrontendConfiguration,
  setApiKey,
} from '../services/api';
import { useApiKey } from '../hooks/useLocalStorage';

const ConfigPage: React.FC = () => {
  const { apiKey, setApiKey: persistApiKey } = useApiKey();
  const [inputApiKey, setInputApiKey] = useState(apiKey || '');
  const [config, setConfig] = useState<FrontendConfiguration | null>(null);
  const [providers, setProviders] = useState<FrontendProviderConfig[]>([]);
  const [defaultProvider, setDefaultProvider] = useState('');
  const [feishuConfig, setFeishuConfig] = useState<FeishuConfiguration>({
    enabled: false,
    app_id: null,
    app_id_env: 'FEISHU_APP_ID',
    app_secret: null,
    app_secret_env: 'FEISHU_APP_SECRET',
    space_id: '',
    root_node_token: '',
    publish_modules: [],
    title_template: '{module} | {title}',
    overwrite_strategy: 'create_new',
  });
  const [modules, setModules] = useState<ModuleConfiguration[]>([]);
  const [serverConfig, setServerConfig] = useState<ServerConfiguration>({
    host: '0.0.0.0',
    port: 8000,
    auth_enabled: true,
    api_key_env: 'SYNTHESAI_API_KEY',
    sync_request_timeout: 120,
    task_polling_timeout: 10,
    max_concurrent: 3,
    max_queue_size: 100,
    result_ttl: 3600,
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);
  const [checkingFeishu, setCheckingFeishu] = useState(false);
  const [publishingFeishuTest, setPublishingFeishuTest] = useState(false);
  const [fetchingModelsFor, setFetchingModelsFor] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [feishuCheck, setFeishuCheck] = useState<FeishuCheckResult | null>(null);

  useEffect(() => {
    void loadConfiguration();
  }, []);

  async function loadConfiguration() {
    setLoading(true);
    try {
      const result = await getFrontendConfiguration();
      setConfig(result);
      setProviders(result.providers);
      setDefaultProvider(result.default_provider);
      setFeishuConfig(result.feishu);
      setModules(result.modules);
      setServerConfig(result.server);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : '配置加载失败');
    } finally {
      setLoading(false);
    }
  }

  function updateProvider(name: string, updater: (provider: FrontendProviderConfig) => FrontendProviderConfig) {
    setProviders((current) =>
      current.map((provider) => (provider.name === name ? updater(provider) : provider))
    );
  }

  function handleModelsChange(name: string, value: string) {
    const models = value
      .split('\n')
      .map((item) => item.trim())
      .filter(Boolean);
    updateProvider(name, (provider) => ({ ...provider, models }));
  }

  async function handleSaveFrontendApiKey(event: React.FormEvent) {
    event.preventDefault();
    setApiKey(inputApiKey);
    persistApiKey(inputApiKey);
    setMessage('WebUI 访问 Key 已保存到浏览器本地存储');
  }

  async function handleSaveConfiguration() {
    setSaving(true);
    setMessage(null);
    try {
      const result = await saveFrontendConfiguration({
        default_provider: defaultProvider,
        providers,
        feishu: feishuConfig,
        modules,
        server: serverConfig,
      });
      if (!result.success) {
        setMessage(result.message);
        return;
      }

      if (result.config) {
        setConfig(result.config);
        setProviders(result.config.providers);
        setDefaultProvider(result.config.default_provider);
        setFeishuConfig(result.config.feishu);
        setModules(result.config.modules);
        setServerConfig(result.config.server);
      }
      setMessage('配置文件已更新');
    } catch (error) {
      setMessage(error instanceof Error ? error.message : '配置保存失败');
    } finally {
      setSaving(false);
    }
  }

  async function handleHealthCheck() {
    setTesting(true);
    setMessage(null);
    try {
      const result = await healthCheck();
      setMessage(`服务连接正常：${result.status}`);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : '服务检查失败');
    } finally {
      setTesting(false);
    }
  }

  async function handleFeishuCheck(verifyToken: boolean) {
    setCheckingFeishu(true);
    setMessage(null);
    try {
      const result = verifyToken
        ? await verifyFeishuConfiguration()
        : await checkFeishuConfiguration();
      setFeishuCheck(result);
      setMessage(result.message);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : '飞书配置检查失败');
    } finally {
      setCheckingFeishu(false);
    }
  }

  async function handleFeishuPublishTest() {
    setPublishingFeishuTest(true);
    setMessage(null);
    try {
      const result = await publishFeishuTestDocument();
      setMessage(result.message);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : '飞书测试发布失败');
    } finally {
      setPublishingFeishuTest(false);
    }
  }

  function togglePublishModule(moduleName: string) {
    setFeishuConfig((current) => {
      const exists = current.publish_modules.includes(moduleName);
      return {
        ...current,
        publish_modules: exists
          ? current.publish_modules.filter((item) => item !== moduleName)
          : [...current.publish_modules, moduleName],
      };
    });
  }

  function updateModule(name: string, updater: (module: ModuleConfiguration) => ModuleConfiguration) {
    setModules((current) => current.map((module) => (module.name === name ? updater(module) : module)));
  }

  async function handleFetchProviderModels(providerName: string) {
    const provider = providers.find((p) => p.name === providerName);
    if (!provider) return;

    setFetchingModelsFor(providerName);
    setMessage(null);
    try {
      const models = await fetchAvailableModels(providerName, provider.api_key);
      updateProvider(providerName, (current) => ({
        ...current,
        models,
      }));
      setMessage(`${providerName} 模型列表已更新，请记得保存配置文件`);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : `${providerName} 模型列表获取失败`);
    } finally {
      setFetchingModelsFor(null);
    }
  }

  return (
    <div className="space-y-lg">
      <section className="card">
        <h1 className="text-2xl font-semibold text-primary">集中配置</h1>
        <p className="mt-sm text-secondary">
          前端只负责维护一个本地配置文件，当前写入目标为
          {config ? ` ${config.file_path}` : ' config/settings.local.yaml'}。
        </p>
        {message && (
          <div className="mt-md rounded-md border border-border bg-neutral-warm px-md py-sm text-sm text-primary">
            {message}
          </div>
        )}
      </section>

      
      <section className="card">
        <div className="flex items-start justify-between gap-md">
          <div>
            <h2 className="text-xl font-semibold text-primary">LLM 配置（模型 / API Key / Base URL）</h2>
            <p className="mt-xs text-sm text-secondary">
              所有 Agent 相关模型配置集中维护在同一个文件，避免前端继续承担业务执行入口。
            </p>
          </div>
          <button className="btn-primary" onClick={() => void handleSaveConfiguration()} disabled={saving || loading}>
            {saving ? '保存中...' : '保存配置文件'}
          </button>
        </div>

        {loading ? (
          <div className="mt-md text-secondary">正在加载配置...</div>
        ) : (
          <div className="mt-lg space-y-lg">
            <div>
              <label className="mb-xs block text-sm font-medium text-primary">默认 Provider</label>
              <select
                className="input w-full"
                value={defaultProvider}
                onChange={(event) => setDefaultProvider(event.target.value)}
              >
                {providers.map((provider) => (
                  <option key={provider.name} value={provider.name}>
                    {provider.name}
                  </option>
                ))}
              </select>
            </div>

            {providers.map((provider) => (
              <section key={provider.name} className="rounded-lg border border-border p-lg">
                <div className="mb-md flex items-center justify-between gap-md">
                  <div>
                    <h3 className="text-lg font-semibold text-primary">{provider.name}</h3>
                    <p className="mt-xs text-sm text-secondary">
                      该 Provider 的配置会写入 `settings.local.yaml`。
                    </p>
                  </div>
                  <button
                    className="btn-secondary"
                    onClick={() => void handleFetchProviderModels(provider.name)}
                    disabled={fetchingModelsFor === provider.name}
                    type="button"
                  >
                    {fetchingModelsFor === provider.name ? '获取中...' : '获取模型'}
                  </button>
                </div>

                <div className="grid gap-md lg:grid-cols-2">
                  <div>
                    <label className="mb-xs block text-sm font-medium text-primary">API Key</label>
                    <input
                      className="input w-full"
                      value={provider.api_key || ''}
                      onChange={(event) =>
                        updateProvider(provider.name, (current) => ({
                          ...current,
                          api_key: event.target.value || null,
                        }))
                      }
                      placeholder="仅保存在本地配置文件"
                    />
                  </div>

                  <div>
                    <label className="mb-xs block text-sm font-medium text-primary">默认模型</label>
                    <select
                      className="input w-full"
                      value={provider.default_model}
                      onChange={(event) =>
                        updateProvider(provider.name, (current) => ({
                          ...current,
                          default_model: event.target.value,
                        }))
                      }
                    >
                      {provider.models.length === 0 ? (
                        <option value={provider.default_model}>
                          {provider.default_model || '请先填写或获取模型列表'}
                        </option>
                      ) : (
                        provider.models.map((model) => (
                          <option key={model} value={model}>
                            {model}
                          </option>
                        ))
                      )}
                    </select>
                  </div>

                  <div>
                    <label className="mb-xs block text-sm font-medium text-primary">Base URL</label>
                    <input
                      className="input w-full"
                      value={provider.base_url || ''}
                      onChange={(event) =>
                        updateProvider(provider.name, (current) => ({
                          ...current,
                          base_url: event.target.value || null,
                        }))
                      }
                    />
                  </div>
                </div>

                <div className="mt-md">
                  <label className="mb-xs block text-sm font-medium text-primary">模型列表</label>
                  <textarea
                    className="input min-h-32 w-full"
                    value={provider.models.join('\n')}
                    onChange={(event) => handleModelsChange(provider.name, event.target.value)}
                    placeholder="每行一个模型名"
                  />
                </div>
              </section>
            ))}
          </div>
        )}
      </section>

      <section className="card">
        <div className="flex items-start justify-between gap-md">
          <div>
            <h2 className="text-xl font-semibold text-primary">模块配置</h2>
            <p className="mt-xs text-sm text-secondary">
              模块启用状态和加载优先级现在也统一写入 `settings.local.yaml`。
            </p>
          </div>
        </div>
        <div className="mt-lg space-y-md">
          {modules.map((module) => (
            <div key={module.name} className="rounded-lg border border-border p-md">
              <div className="grid gap-md lg:grid-cols-[1fr_120px]">
                <label className="flex items-center gap-sm text-sm font-medium text-primary">
                  <input
                    type="checkbox"
                    checked={module.enabled}
                    onChange={(event) =>
                      updateModule(module.name, (current) => ({
                        ...current,
                        enabled: event.target.checked,
                      }))
                    }
                  />
                  {module.name}
                </label>
                <div>
                  <label className="mb-xs block text-sm font-medium text-primary">优先级</label>
                  <input
                    className="input w-full"
                    type="number"
                    value={module.priority}
                    onChange={(event) =>
                      updateModule(module.name, (current) => ({
                        ...current,
                        priority: Number(event.target.value),
                      }))
                    }
                  />
                </div>
              </div>
            </div>
          ))}
        </div>
      </section>

      <section className="card">
        <div className="flex items-start justify-between gap-md">
          <div>
            <h2 className="text-xl font-semibold text-primary">服务端配置</h2>
            <p className="mt-xs text-sm text-secondary">
              服务监听、鉴权和任务队列参数也改为从同一个本地配置文件覆盖。
              保存后新配置会在服务重启后生效。
            </p>
          </div>
        </div>
        <div className="mt-lg grid gap-md lg:grid-cols-2">
          <div>
            <label className="mb-xs block text-sm font-medium text-primary">Host</label>
            <input
              className="input w-full"
              value={serverConfig.host}
              onChange={(event) =>
                setServerConfig((current) => ({ ...current, host: event.target.value }))
              }
            />
          </div>
          <div>
            <label className="mb-xs block text-sm font-medium text-primary">Port</label>
            <input
              className="input w-full"
              type="number"
              value={serverConfig.port}
              onChange={(event) =>
                setServerConfig((current) => ({ ...current, port: Number(event.target.value) }))
              }
            />
          </div>
          <div className="flex items-center gap-sm pt-lg">
            <input
              type="checkbox"
              checked={serverConfig.auth_enabled}
              onChange={(event) =>
                setServerConfig((current) => ({ ...current, auth_enabled: event.target.checked }))
              }
            />
            <span className="text-sm font-medium text-primary">启用 API Key 鉴权</span>
          </div>
          <div>
            <label className="mb-xs block text-sm font-medium text-primary">同步请求超时</label>
            <input
              className="input w-full"
              type="number"
              value={serverConfig.sync_request_timeout}
              onChange={(event) =>
                setServerConfig((current) => ({
                  ...current,
                  sync_request_timeout: Number(event.target.value),
                }))
              }
            />
          </div>
          <div>
            <label className="mb-xs block text-sm font-medium text-primary">轮询间隔</label>
            <input
              className="input w-full"
              type="number"
              value={serverConfig.task_polling_timeout}
              onChange={(event) =>
                setServerConfig((current) => ({
                  ...current,
                  task_polling_timeout: Number(event.target.value),
                }))
              }
            />
          </div>
          <div>
            <label className="mb-xs block text-sm font-medium text-primary">最大并发任务</label>
            <input
              className="input w-full"
              type="number"
              value={serverConfig.max_concurrent}
              onChange={(event) =>
                setServerConfig((current) => ({
                  ...current,
                  max_concurrent: Number(event.target.value),
                }))
              }
            />
          </div>
          <div>
            <label className="mb-xs block text-sm font-medium text-primary">队列上限</label>
            <input
              className="input w-full"
              type="number"
              value={serverConfig.max_queue_size}
              onChange={(event) =>
                setServerConfig((current) => ({
                  ...current,
                  max_queue_size: Number(event.target.value),
                }))
              }
            />
          </div>
          <div>
            <label className="mb-xs block text-sm font-medium text-primary">结果保留秒数</label>
            <input
              className="input w-full"
              type="number"
              value={serverConfig.result_ttl}
              onChange={(event) =>
                setServerConfig((current) => ({
                  ...current,
                  result_ttl: Number(event.target.value),
                }))
              }
            />
          </div>
        </div>
      </section>

      <section className="card">
        <div className="flex items-start justify-between gap-md">
          <div>
            <h2 className="text-xl font-semibold text-primary">飞书知识库发布</h2>
            <p className="mt-xs text-sm text-secondary">
              这里配置模块执行完成后的飞书知识库自动发布行为，配置将一并写入
              `settings.local.yaml`。
            </p>
          </div>
          <div className="flex gap-sm">
            <button
              className="btn-secondary"
              onClick={() => void handleFeishuCheck(false)}
              disabled={checkingFeishu}
            >
              {checkingFeishu ? '检查中...' : '检查配置'}
            </button>
            <button
              className="btn-secondary"
              onClick={() => void handleFeishuCheck(true)}
              disabled={checkingFeishu}
            >
              {checkingFeishu ? '验证中...' : '验证 Token'}
            </button>
            <button
              className="btn-secondary"
              onClick={() => void handleFeishuPublishTest()}
              disabled={publishingFeishuTest}
            >
              {publishingFeishuTest ? '发布中...' : '测试发布'}
            </button>
          </div>
        </div>

        <div className="mt-lg space-y-md">
          <label className="flex items-center gap-sm text-sm font-medium text-primary">
            <input
              type="checkbox"
              checked={feishuConfig.enabled}
              onChange={(event) =>
                setFeishuConfig((current) => ({
                  ...current,
                  enabled: event.target.checked,
                }))
              }
            />
            启用飞书知识库发布
          </label>

          <div className="grid gap-md lg:grid-cols-2">
            <div>
              <label className="mb-xs block text-sm font-medium text-primary">App ID</label>
              <input
                className="input w-full"
                type="password"
                value={feishuConfig.app_id || ''}
                onChange={(event) =>
                  setFeishuConfig((current) => ({ ...current, app_id: event.target.value || null }))
                }
                placeholder="cli_xxxxxxxxx"
              />
            </div>

            <div>
              <label className="mb-xs block text-sm font-medium text-primary">App Secret</label>
              <input
                className="input w-full"
                type="password"
                value={feishuConfig.app_secret || ''}
                onChange={(event) =>
                  setFeishuConfig((current) => ({ ...current, app_secret: event.target.value || null }))
                }
                placeholder="仅保存在本地配置文件"
              />
            </div>

            <div>
              <label className="mb-xs block text-sm font-medium text-primary">知识库 Space ID</label>
              <input
                className="input w-full"
                value={feishuConfig.space_id}
                onChange={(event) =>
                  setFeishuConfig((current) => ({ ...current, space_id: event.target.value }))
                }
                placeholder="wikcnxxxxxxxx"
              />
            </div>

            <div>
              <label className="mb-xs block text-sm font-medium text-primary">根节点 Token</label>
              <input
                className="input w-full"
                value={feishuConfig.root_node_token}
                onChange={(event) =>
                  setFeishuConfig((current) => ({ ...current, root_node_token: event.target.value }))
                }
                placeholder="wikntxxxxxxxx"
              />
            </div>

            <div>
              <label className="mb-xs block text-sm font-medium text-primary">标题模板</label>
              <input
                className="input w-full"
                value={feishuConfig.title_template}
                onChange={(event) =>
                  setFeishuConfig((current) => ({ ...current, title_template: event.target.value }))
                }
              />
            </div>

            <div>
              <label className="mb-xs block text-sm font-medium text-primary">发布策略</label>
              <select
                className="input w-full"
                value={feishuConfig.overwrite_strategy}
                onChange={(event) =>
                  setFeishuConfig((current) => ({
                    ...current,
                    overwrite_strategy: event.target.value,
                  }))
                }
              >
                <option value="create_new">create_new</option>
              </select>
            </div>
          </div>

          <div>
            <label className="mb-xs block text-sm font-medium text-primary">允许自动发布的模块</label>
            <div className="flex flex-wrap gap-sm">
              {['video_summary', 'link_learning', 'vocabulary'].map((moduleName) => (
                <label
                  key={moduleName}
                  className="flex items-center gap-xs rounded-full border border-border px-md py-sm text-sm text-primary"
                >
                  <input
                    type="checkbox"
                    checked={feishuConfig.publish_modules.includes(moduleName)}
                    onChange={() => togglePublishModule(moduleName)}
                  />
                  {moduleName}
                </label>
              ))}
            </div>
          </div>

          {feishuCheck && (
            <div className="rounded-md border border-border bg-neutral-warm p-md text-sm text-primary">
              <p>配置完整：{feishuCheck.configured ? '是' : '否'}</p>
              <p>插件已加载：{feishuCheck.adapter_loaded ? '是' : '否'}</p>
              <p>已启用：{feishuCheck.enabled ? '是' : '否'}</p>
              <p>Token 验证：{feishuCheck.token_verified ? '成功' : '未验证/失败'}</p>
              <p>知识库可访问：{feishuCheck.space_accessible ? '是' : '否'}</p>
              <p>根节点可访问：{feishuCheck.root_node_accessible ? '是' : '否'}</p>
            </div>
          )}
        </div>
      </section>

      <section className="card">
        <div className="flex items-start justify-between gap-md">
          <div>
            <h2 className="text-xl font-semibold text-primary">WebUI 访问控制</h2>
            <p className="mt-xs text-sm text-secondary">
              这里的 Key 只保存在浏览器本地，用于请求受保护的服务接口。
            </p>
          </div>
          <button className="btn-secondary" onClick={() => void handleHealthCheck()} disabled={testing}>
            {testing ? '检测中...' : '检测服务'}
          </button>
        </div>
        <form className="mt-md flex flex-col gap-sm lg:flex-row" onSubmit={(event) => void handleSaveFrontendApiKey(event)}>
          <input
            className="input flex-1"
            value={inputApiKey}
            onChange={(event) => setInputApiKey(event.target.value)}
            placeholder="输入 WebUI 访问 Key"
          />
          <button className="btn-primary" type="submit">
            保存访问 Key
          </button>
        </form>
      </section>

    </div>
  );
};

export default ConfigPage;
