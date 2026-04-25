import React, { useEffect, useState } from 'react';
import QRCode from 'qrcode';
import {
  AllPlatformsStatus,
  getAuthStatus,
  getBilibiliQRCode,
  getLoginHelp,
  importCookies,
  logoutPlatform,
  pollBilibiliQRStatus,
} from '../services/api';

interface PlatformHelp {
  method: string;
  steps: string[];
  note?: string;
  required_cookies?: string[];
}

const LOGIN_PLATFORMS = ['bilibili', 'douyin', 'youtube'] as const;

const LoginPage: React.FC = () => {
  const [authStatus, setAuthStatus] = useState<AllPlatformsStatus | null>(null);
  const [platformHelp, setPlatformHelp] = useState<Record<string, PlatformHelp>>({});
  const [cookieInput, setCookieInput] = useState<Record<string, string>>({
    bilibili: '',
    douyin: '',
    youtube: '',
  });
  const [loading, setLoading] = useState(true);
  const [importingPlatform, setImportingPlatform] = useState<string | null>(null);
  const [qrCodeImage, setQrCodeImage] = useState<string | null>(null);
  const [qrSessionKey, setQrSessionKey] = useState<string | null>(null);
  const [pollingQr, setPollingQr] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  useEffect(() => {
    void loadPageData();
  }, []);

  useEffect(() => {
    if (!pollingQr || !qrSessionKey) {
      return undefined;
    }

    const timer = window.setInterval(async () => {
      try {
        const result = await pollBilibiliQRStatus(qrSessionKey);
        if (result.authenticated) {
          setMessage('Bilibili 登录成功');
          setPollingQr(false);
          setQrCodeImage(null);
          setQrSessionKey(null);
          void loadAuthStatus();
          return;
        }

        if (result.status === 'expired') {
          setMessage('二维码已过期，请重新获取');
          setPollingQr(false);
          setQrCodeImage(null);
          setQrSessionKey(null);
          return;
        }

        if (result.status === 'scanned') {
          setMessage('已扫码，请在手机上确认');
        }
      } catch (error) {
        setMessage(error instanceof Error ? error.message : '二维码轮询失败');
        setPollingQr(false);
      }
    }, 2000);

    return () => window.clearInterval(timer);
  }, [pollingQr, qrSessionKey]);

  async function loadPageData() {
    setLoading(true);
    await Promise.all([loadAuthStatus(), loadPlatformHelp()]);
    setLoading(false);
  }

  async function loadAuthStatus() {
    const status = await getAuthStatus();
    setAuthStatus(status);
  }

  async function loadPlatformHelp() {
    const entries = await Promise.all(
      LOGIN_PLATFORMS.map(async (platform) => {
        try {
          const help = await getLoginHelp(platform);
          return [platform, help as PlatformHelp] as const;
        } catch {
          return [platform, { method: 'Unavailable', steps: ['无法加载当前平台帮助信息'] }] as const;
        }
      })
    );
    setPlatformHelp(Object.fromEntries(entries));
  }

  async function handleBilibiliQrLogin() {
    try {
      setMessage('正在生成 Bilibili 二维码');
      const result = await getBilibiliQRCode();
      const qrImageData = await QRCode.toDataURL(result.qr_url, { width: 240, margin: 2 });
      setQrCodeImage(qrImageData);
      setQrSessionKey(result.session_key);
      setPollingQr(true);
      setMessage('请使用 Bilibili App 扫码登录');
    } catch (error) {
      setMessage(error instanceof Error ? error.message : '获取二维码失败');
    }
  }

  async function handleImportCookies(platform: string) {
    const cookies = cookieInput[platform]?.trim();
    if (!cookies) {
      setMessage('请先粘贴 Cookie 内容');
      return;
    }

    setImportingPlatform(platform);
    try {
      const result = await importCookies(platform, cookies);
      setMessage(result.success ? `${platform} Cookie 导入成功` : result.message);
      if (result.success) {
        setCookieInput((current) => ({ ...current, [platform]: '' }));
        await loadAuthStatus();
      }
    } catch (error) {
      setMessage(error instanceof Error ? error.message : '导入 Cookie 失败');
    } finally {
      setImportingPlatform(null);
    }
  }

  async function handleLogout(platform: string) {
    try {
      const result = await logoutPlatform(platform);
      setMessage(result.message);
      await loadAuthStatus();
    } catch (error) {
      setMessage(error instanceof Error ? error.message : '登出失败');
    }
  }

  function getStatusText(status: string) {
    if (status === 'authenticated') return '已登录';
    if (status === 'expired') return '已过期';
    if (status === 'error') return '异常';
    return '未登录';
  }

  return (
    <div className="space-y-lg">
      <section className="card">
        <div className="flex items-start justify-between gap-md">
          <div>
            <h1 className="text-2xl font-semibold text-primary">平台登录</h1>
            <p className="mt-sm text-secondary">
              WebUI 仅保留平台登录能力，供 Agent 使用前完成凭据准备。
            </p>
          </div>
          <button className="btn-secondary" onClick={() => void loadPageData()}>
            刷新状态
          </button>
        </div>
        {message && (
          <div className="mt-md rounded-md border border-border bg-neutral-warm px-md py-sm text-sm text-primary">
            {message}
          </div>
        )}
      </section>

      {loading ? (
        <section className="card text-secondary">正在加载登录状态...</section>
      ) : (
        <div className="grid gap-lg lg:grid-cols-[1.2fr_0.8fr]">
          <div className="space-y-lg">
            {authStatus?.platforms.map((platform) => {
              const help = platformHelp[platform.platform];
              return (
                <section key={platform.platform} className="card">
                  <div className="flex items-start justify-between gap-md">
                    <div>
                      <h2 className="text-xl font-semibold text-primary">{platform.platform}</h2>
                      <p className="mt-xs text-sm text-secondary">{platform.message || '暂无状态信息'}</p>
                    </div>
                    <span className="tag">{getStatusText(platform.status)}</span>
                  </div>

                  {platform.platform === 'bilibili' && (
                    <div className="mt-md flex flex-wrap gap-sm">
                      <button className="btn-primary" onClick={() => void handleBilibiliQrLogin()}>
                        扫码登录
                      </button>
                      <button className="btn-secondary" onClick={() => void handleLogout(platform.platform)}>
                        清除登录
                      </button>
                    </div>
                  )}

                  {platform.platform !== 'youtube' && (
                    <div className="mt-md">
                      <label className="mb-xs block text-sm font-medium text-primary">
                        手动导入 Cookie
                      </label>
                      <textarea
                        className="input min-h-32 w-full"
                        value={cookieInput[platform.platform] || ''}
                        onChange={(event) =>
                          setCookieInput((current) => ({
                            ...current,
                            [platform.platform]: event.target.value,
                          }))
                        }
                        placeholder="粘贴浏览器导出的 Cookie 内容"
                      />
                      <div className="mt-sm flex gap-sm">
                        <button
                          className="btn-secondary"
                          onClick={() => void handleImportCookies(platform.platform)}
                          disabled={importingPlatform === platform.platform}
                        >
                          {importingPlatform === platform.platform ? '导入中...' : '导入 Cookie'}
                        </button>
                        <button className="btn-secondary" onClick={() => void handleLogout(platform.platform)}>
                          清除登录
                        </button>
                      </div>
                    </div>
                  )}

                  {help && (
                    <div className="mt-md rounded-md border border-border p-md">
                      <p className="text-sm font-medium text-primary">登录方式：{help.method}</p>
                      <ol className="mt-sm list-decimal space-y-xs pl-lg text-sm text-secondary">
                        {help.steps.map((step) => (
                          <li key={step}>{step}</li>
                        ))}
                      </ol>
                      {help.note && <p className="mt-sm text-sm text-secondary">说明：{help.note}</p>}
                      {help.required_cookies && (
                        <p className="mt-sm text-sm text-secondary">
                          必需 Cookie：{help.required_cookies.join(', ')}
                        </p>
                      )}
                    </div>
                  )}
                </section>
              );
            })}
          </div>

          <section className="card">
            <h2 className="text-xl font-semibold text-primary">扫码面板</h2>
            <p className="mt-sm text-secondary">当前仅 Bilibili 支持服务端代理二维码登录。</p>
            {qrCodeImage ? (
              <div className="mt-lg flex flex-col items-center gap-md">
                <img src={qrCodeImage} alt="Bilibili QR Code" className="rounded-lg border border-border" />
                <p className="text-sm text-secondary">请在手机 App 内完成确认，页面会自动刷新状态。</p>
              </div>
            ) : (
              <div className="mt-lg rounded-md border border-dashed border-border p-lg text-sm text-secondary">
                点击左侧卡片中的“扫码登录”生成二维码。
              </div>
            )}
          </section>
        </div>
      )}
    </div>
  );
};

export default LoginPage;
