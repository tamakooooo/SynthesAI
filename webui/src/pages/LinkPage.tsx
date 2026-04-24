import React, { useState } from 'react';
import { processLink, LinkResult } from '../services/api';
import {
  linkResultToMarkdown,
  exportMarkdown,
  exportPdfViaPrint,
  sanitizeFilename,
  getTimestamp,
} from '../utils/export';

const LinkPage: React.FC = () => {
  const [url, setUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<LinkResult | null>(null);

  const handleExportMarkdown = () => {
    if (!result) return;
    const md = linkResultToMarkdown(result);
    const filename = `${sanitizeFilename(result.title)}_${getTimestamp()}.md`;
    exportMarkdown(md, filename);
  };

  const handleExportPdf = () => {
    if (!result) return;
    const md = linkResultToMarkdown(result);
    exportPdfViaPrint(md, result.title);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!url) return;

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const data = await processLink(url);
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : '处理失败');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-lg">
      {/* Header */}
      <div>
        <h1 className="text-h1 text-primary">知识卡片生成器</h1>
        <p className="text-secondary mt-sm">
          输入网页链接，自动提取核心知识并生成问答和测验
        </p>
      </div>

      {/* Form */}
      <form onSubmit={handleSubmit} className="space-y-md">
        <div>
          <label className="block text-sm font-medium text-primary mb-xs">
            网页链接
          </label>
          <input
            type="url"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="https://example.com/article"
            className="input w-full"
            required
          />
        </div>

        <button
          type="submit"
          disabled={loading || !url}
          className="btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {loading ? '处理中...' : '生成知识卡片'}
        </button>
      </form>

      {/* Error */}
      {error && (
        <div className="bg-highlight-red rounded-md p-md">
          <p className="text-error">{error}</p>
        </div>
      )}

      {/* Loading indicator */}
      {loading && (
        <div className="text-center py-xl">
          <div className="animate-spin w-8 h-8 border-2 border-accent border-t-transparent rounded-full mx-auto" />
          <p className="text-secondary mt-md">正在分析网页内容...</p>
        </div>
      )}

      {/* Result */}
      {result && (
        <div className="card space-y-md">
          {/* Title */}
          <div>
            <h2 className="text-h2 text-primary">{result.title}</h2>
            <p className="text-sm text-secondary">
              来源: {result.source} · {result.word_count} 字 · 阅读时间 {result.reading_time}
            </p>
          </div>

          {/* Tags */}
          {result.tags.length > 0 && (
            <div className="flex flex-wrap gap-xs">
              {result.tags.map((tag, i) => (
                <span key={i} className="tag">{tag}</span>
              ))}
            </div>
          )}

          {/* Summary */}
          <div>
            <h3 className="text-h3 text-primary mb-sm">概要</h3>
            <p className="text-primary leading-relaxed">{result.summary}</p>
          </div>

          {/* Key points */}
          {result.key_points.length > 0 && (
            <div>
              <h3 className="text-h3 text-primary mb-sm">核心要点</h3>
              <ul className="space-y-xs">
                {result.key_points.map((point, i) => (
                  <li key={i} className="flex items-start gap-sm">
                    <span className="text-accent">•</span>
                    <span className="text-primary">{point}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Q&A */}
          {result.qa_pairs.length > 0 && (
            <div>
              <h3 className="text-h3 text-primary mb-sm">问答</h3>
              <div className="space-y-md">
                {result.qa_pairs.map((qa, i) => (
                  <div key={i} className="bg-highlight-yellow rounded-md p-md">
                    <p className="font-medium text-primary">Q: {qa.question}</p>
                    <p className="text-secondary mt-xs">A: {qa.answer}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Quiz */}
          {result.quiz.length > 0 && (
            <div>
              <h3 className="text-h3 text-primary mb-sm">测验题</h3>
              <div className="space-y-md">
                {result.quiz.map((q, i) => (
                  <div key={i} className="bg-highlight-blue rounded-md p-md">
                    <p className="font-medium text-primary mb-sm">{i + 1}. {q.question}</p>
                    <div className="space-y-xs">
                      {q.options.map((opt, j) => (
                        <div key={j} className="flex items-center gap-sm">
                          <input type="radio" name={`quiz-${i}`} className="accent-accent" />
                          <span className="text-primary">{opt}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
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
          </div>
        </div>
      )}
    </div>
  );
};

export default LinkPage;