import React, { useState } from 'react';
import { extractVocabulary, VocabularyResult } from '../services/api';
import {
  vocabularyResultToMarkdown,
  exportMarkdown,
  exportPdfViaPrint,
  getTimestamp,
} from '../utils/export';

const VocabularyPage: React.FC = () => {
  const [content, setContent] = useState('');
  const [url, setUrl] = useState('');
  const [wordCount, setWordCount] = useState(10);
  const [difficulty, setDifficulty] = useState('intermediate');
  const [generateStory, setGenerateStory] = useState(true);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<VocabularyResult | null>(null);

  const handleExportMarkdown = () => {
    if (!result) return;
    const md = vocabularyResultToMarkdown(result);
    const filename = `词汇卡片_${getTimestamp()}.md`;
    exportMarkdown(md, filename);
  };

  const handleExportPdf = () => {
    if (!result) return;
    const md = vocabularyResultToMarkdown(result);
    exportPdfViaPrint(md, '词汇学习卡片');
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!content && !url) return;

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const data = await extractVocabulary({
        content: content || undefined,
        url: url || undefined,
        word_count: wordCount,
        difficulty,
        generate_story: generateStory,
      });
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
        <h1 className="text-h1 text-primary">词汇提取器</h1>
        <p className="text-secondary mt-sm">
          从文本或网页中提取核心词汇，生成带音标和例句的单词卡
        </p>
      </div>

      {/* Form */}
      <form onSubmit={handleSubmit} className="space-y-md">
        {/* Content input */}
        <div>
          <label className="block text-sm font-medium text-primary mb-xs">
            文本内容
          </label>
          <textarea
            value={content}
            onChange={(e) => setContent(e.target.value)}
            placeholder="输入或粘贴文本内容..."
            className="input w-full min-h-[200px] resize-y"
            rows={8}
          />
        </div>

        {/* URL input */}
        <div>
          <label className="block text-sm font-medium text-primary mb-xs">
            或输入网页链接
          </label>
          <input
            type="url"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="https://example.com/article"
            className="input w-full"
          />
        </div>

        {/* Settings */}
        <div className="flex flex-wrap gap-lg">
          <div>
            <label className="block text-sm font-medium text-primary mb-xs">
              单词数量
            </label>
            <select
              value={wordCount}
              onChange={(e) => setWordCount(Number(e.target.value))}
              className="input"
            >
              {[5, 10, 15, 20, 30, 50].map((n) => (
                <option key={n} value={n}>{n}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-primary mb-xs">
              难度等级
            </label>
            <select
              value={difficulty}
              onChange={(e) => setDifficulty(e.target.value)}
              className="input"
            >
              <option value="beginner">初级</option>
              <option value="intermediate">中级</option>
              <option value="advanced">高级</option>
            </select>
          </div>

          <div className="flex items-center gap-sm">
            <input
              type="checkbox"
              checked={generateStory}
              onChange={(e) => setGenerateStory(e.target.checked)}
              className="accent-accent w-4 h-4"
            />
            <label className="text-sm text-primary">生成上下文故事</label>
          </div>
        </div>

        <button
          type="submit"
          disabled={loading || (!content && !url)}
          className="btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {loading ? '提取中...' : '提取词汇'}
        </button>
      </form>

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
          <p className="text-secondary mt-md">正在分析并提取词汇...</p>
        </div>
      )}

      {/* Result */}
      {result && (
        <div className="space-y-lg">
          {/* Vocabulary cards */}
          <div className="card">
            <h3 className="text-h3 text-primary mb-md">
              词汇卡片 ({result.vocabulary_cards.length} 词)
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-md">
              {result.vocabulary_cards.map((card, i) => (
                <div key={i} className="bg-white rounded-md p-md border border-border">
                  {/* Word and phonetic */}
                  <div className="text-h3 text-primary font-semibold">{card.word}</div>
                  <div className="text-sm text-secondary font-mono">
                    {card.phonetic.us || card.phonetic.uk || ''}
                  </div>

                  {/* Part of speech */}
                  <div className="text-sm text-accent mt-xs">{card.part_of_speech}</div>

                  {/* Definition */}
                  <div className="mt-sm">
                    <p className="text-primary">{card.definition.zh}</p>
                    {card.definition.en && (
                      <p className="text-sm text-secondary">{card.definition.en}</p>
                    )}
                  </div>

                  {/* Example */}
                  {card.example_sentences[0] && (
                    <div className="mt-sm text-sm">
                      <p className="text-secondary italic">
                        "{card.example_sentences[0].sentence}"
                      </p>
                      <p className="text-secondary">{card.example_sentences[0].translation}</p>
                    </div>
                  )}

                  {/* Difficulty tag */}
                  <div className="mt-sm">
                    <span className={`text-xs px-sm py-xs rounded-full ${
                      card.difficulty === 'beginner' ? 'bg-highlight-green text-success' :
                      card.difficulty === 'advanced' ? 'bg-highlight-purple text-purple-700' :
                      'bg-highlight-yellow text-warning'
                    }`}>
                      {card.difficulty}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Context story */}
          {result.context_story && (
            <div className="card">
              <h3 className="text-h3 text-primary mb-md">
                上下文故事 ({result.context_story.word_count} 词)
              </h3>
              <div className="bg-highlight-blue rounded-md p-lg">
                <p className="text-primary leading-relaxed whitespace-pre-wrap">
                  {result.context_story.content}
                </p>
              </div>
              <div className="mt-sm flex flex-wrap gap-xs">
                {result.context_story.target_words.map((word, i) => (
                  <span key={i} className="tag">{word}</span>
                ))}
              </div>
            </div>
          )}

          {/* Actions */}
          <div className="flex gap-sm">
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

export default VocabularyPage;