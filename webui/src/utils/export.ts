/**
 * 导出工具模块 - 支持 Markdown/PDF 导出和文件下载
 */

import { LinkResult, VocabularyResult, VideoResult } from '../services/api';

// ==================== Markdown 导出 ====================

/**
 * 将知识卡片结果转换为 Markdown 格式
 */
export function linkResultToMarkdown(result: LinkResult): string {
  const lines: string[] = [
    `# ${result.title}`,
    '',
    `> 来源: ${result.source} | 字数: ${result.word_count} | 阅读时间: ${result.reading_time}`,
    '',
  ];

  // Tags
  if (result.tags.length > 0) {
    lines.push(`**标签:** ${result.tags.map(t => `\`${t}\``).join(' ')}`);
    lines.push('');
  }

  // Summary
  lines.push('## 概要');
  lines.push('');
  lines.push(result.summary);
  lines.push('');

  // Key points
  if (result.key_points.length > 0) {
    lines.push('## 核心要点');
    lines.push('');
    result.key_points.forEach((point, i) => {
      lines.push(`${i + 1}. ${point}`);
    });
    lines.push('');
  }

  // Q&A
  if (result.qa_pairs.length > 0) {
    lines.push('## 问答');
    lines.push('');
    result.qa_pairs.forEach((qa, i) => {
      lines.push(`### Q${i + 1}: ${qa.question}`);
      lines.push('');
      lines.push(qa.answer);
      lines.push('');
    });
  }

  // Quiz
  if (result.quiz.length > 0) {
    lines.push('## 测验题');
    lines.push('');
    result.quiz.forEach((q, i) => {
      lines.push(`### ${i + 1}. ${q.question}`);
      lines.push('');
      q.options.forEach((opt) => {
        lines.push(`- [ ] ${opt}`);
      });
      lines.push('');
    });
  }

  return lines.join('\n');
}

/**
 * 将词汇结果转换为 Markdown 格式
 */
export function vocabularyResultToMarkdown(result: VocabularyResult): string {
  const lines: string[] = [
    '# 词汇学习卡片',
    '',
    `> 共 ${result.vocabulary_cards.length} 个词汇`,
    '',
  ];

  // Vocabulary cards
  lines.push('## 词汇列表');
  lines.push('');

  result.vocabulary_cards.forEach((card, i) => {
    const phonetic = card.phonetic.us || card.phonetic.uk || '';
    lines.push(`### ${i + 1}. ${card.word}`);
    if (phonetic) {
      lines.push(`**音标:** ${phonetic}`);
    }
    lines.push(`**词性:** ${card.part_of_speech}`);
    lines.push('');
    lines.push(`**释义 (中文):** ${card.definition.zh}`);
    if (card.definition.en) {
      lines.push(`**释义 (英文):** ${card.definition.en}`);
    }
    lines.push('');

    // Examples
    if (card.example_sentences.length > 0) {
      lines.push('**例句:**');
      lines.push('');
      card.example_sentences.forEach((ex) => {
        lines.push(`- "${ex.sentence}"`);
        lines.push(`  ${ex.translation}`);
      });
      lines.push('');
    }

    lines.push(`**难度:** ${card.difficulty}`);
    lines.push('');
    lines.push('---');
    lines.push('');
  });

  // Context story
  if (result.context_story) {
    lines.push('## 上下文故事');
    lines.push('');
    lines.push(`> 包含词汇: ${result.context_story.target_words.join(', ')}`);
    lines.push('');
    lines.push(result.context_story.content);
    lines.push('');
  }

  return lines.join('\n');
}

/**
 * 将视频总结结果转换为 Markdown 格式
 */
export function videoResultToMarkdown(result: VideoResult): string {
  const lines: string[] = [
    `# ${result.title || '视频内容总结'}`,
    '',
  ];

  // Metadata
  if (result.metadata) {
    const metaInfo = [];
    if (result.metadata.duration) metaInfo.push(`时长: ${result.metadata.duration}`);
    if (result.metadata.platform) metaInfo.push(`平台: ${result.metadata.platform}`);
    if (metaInfo.length > 0) {
      lines.push(`> ${metaInfo.join(' | ')}`);
      lines.push('');
    }
  }

  // Summary
  if (result.summary) {
    lines.push('## 内容总结');
    lines.push('');
    if (result.summary.content) {
      lines.push(result.summary.content);
      lines.push('');
    }

    // Key points
    if (result.summary.key_points && result.summary.key_points.length > 0) {
      lines.push('### 核心要点');
      lines.push('');
      result.summary.key_points.forEach((point, i) => {
        lines.push(`${i + 1}. ${point}`);
      });
      lines.push('');
    }
  }

  // Transcript
  if (result.transcript) {
    lines.push('## 字幕原文');
    lines.push('');
    lines.push('```text');
    lines.push(result.transcript);
    lines.push('```');
    lines.push('');
  }

  return lines.join('\n');
}

// ==================== 文件下载 ====================

/**
 * 下载文本文件
 */
export function downloadTextFile(content: string, filename: string, mimeType: string = 'text/plain'): void {
  const blob = new Blob([content], { type: mimeType });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

/**
 * 导出为 Markdown 文件
 */
export function exportMarkdown(content: string, filename: string): void {
  downloadTextFile(content, filename, 'text/markdown');
}

/**
 * 下载字幕文件
 */
export function downloadTranscript(transcript: string, title: string): void {
  const filename = `${sanitizeFilename(title)}_transcript.txt`;
  downloadTextFile(transcript, filename);
}

// ==================== PDF 导出 ====================

/**
 * 使用浏览器打印功能导出 PDF
 * 这是一个轻量级方案，不需要额外依赖库
 */
export function exportPdfViaPrint(content: string, title: string): void {
  // 创建一个临时窗口用于打印
  const printWindow = window.open('', '_blank');
  if (!printWindow) {
    alert('无法打开打印窗口，请检查浏览器弹窗设置');
    return;
  }

  // 构建打印页面内容
  const html = `
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>${title}</title>
  <style>
    body {
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
      line-height: 1.6;
      max-width: 800px;
      margin: 0 auto;
      padding: 40px;
      color: #333;
    }
    h1 { font-size: 24px; margin-bottom: 16px; }
    h2 { font-size: 20px; margin-top: 24px; margin-bottom: 12px; }
    h3 { font-size: 16px; margin-top: 20px; margin-bottom: 8px; }
    p { margin: 8px 0; }
    ul, ol { margin: 8px 0; padding-left: 24px; }
    li { margin: 4px 0; }
    blockquote {
      border-left: 4px solid #ddd;
      margin: 16px 0;
      padding-left: 16px;
      color: #666;
    }
    code {
      background: #f5f5f5;
      padding: 2px 6px;
      border-radius: 4px;
      font-size: 14px;
    }
    pre {
      background: #f5f5f5;
      padding: 16px;
      border-radius: 8px;
      overflow-x: auto;
      white-space: pre-wrap;
    }
    hr { border: none; border-top: 1px solid #ddd; margin: 24px 0; }
    @media print {
      body { padding: 20px; }
      @page { margin: 2cm; }
    }
  </style>
</head>
<body>
${markdownToHtml(content)}
</body>
</html>
  `;

  printWindow.document.write(html);
  printWindow.document.close();

  // 等待内容加载完成后打印
  printWindow.onload = () => {
    printWindow.print();
    // 打印后关闭窗口（用户可以取消）
    setTimeout(() => printWindow.close(), 100);
  };
}

/**
 * 将 Markdown 转换为简单的 HTML
 * 这是一个轻量级转换，处理基本格式
 */
function markdownToHtml(md: string): string {
  let html = md;

  // Headers
  html = html.replace(/^### (.+)$/gm, '<h3>$1</h3>');
  html = html.replace(/^## (.+)$/gm, '<h2>$1</h2>');
  html = html.replace(/^# (.+)$/gm, '<h1>$1</h1>');

  // Blockquote
  html = html.replace(/^> (.+)$/gm, '<blockquote>$1</blockquote>');

  // Bold
  html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');

  // Code (inline)
  html = html.replace(/`(.+?)`/g, '<code>$1</code>');

  // Code block
  html = html.replace(/```(\w*)\n([\s\S]+?)```/g, '<pre>$2</pre>');

  // Lists
  html = html.replace(/^- (.+)$/gm, '<li>$1</li>');
  html = html.replace(/(<li>.*<\/li>\n?)+/g, '<ul>$&</ul>');

  // Numbered lists
  html = html.replace(/^\d+\. (.+)$/gm, '<li>$1</li>');
  html = html.replace(/(<li>.*<\/li>\n?)+/g, (match) => {
    if (match.includes('<ul>')) return match;
    return `<ol>${match}</ol>`;
  });

  // Horizontal rule
  html = html.replace(/^---$/gm, '<hr>');

  // Paragraphs
  html = html.split('\n\n').map(block => {
    if (block.startsWith('<')) return block;
    return `<p>${block}</p>`;
  }).join('\n');

  return html;
}

// ==================== 辅助函数 ====================

/**
 * 清理文件名，移除特殊字符
 */
export function sanitizeFilename(name: string): string {
  return name
    .replace(/[<>:"/\\|?*]/g, '')
    .replace(/\s+/g, '_')
    .slice(0, 100);
}

/**
 * 获取当前日期时间字符串
 */
export function getTimestamp(): string {
  const now = new Date();
  return now.toISOString().slice(0, 19).replace(/[T:]/g, '-');
}