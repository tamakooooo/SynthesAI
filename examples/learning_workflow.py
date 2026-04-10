"""
Learning Workflow Examples - 完整学习工作流示例

这些示例展示了如何整合视频、文章、单词学习，
创建完整的学习流程和笔记。
"""

import asyncio
from pathlib import Path
from datetime import datetime
from learning_assistant.api import (
    summarize_video,
    process_link,
    extract_vocabulary,
    get_recent_history,
)


async def workflow_1_video_to_vocabulary(video_url):
    """
    工作流 1: 视频学习 → 单词提取

    从视频总结中提取单词，巩固学习。
    """
    print("\n" + "="*60)
    print("工作流 1: 视频学习 → 单词提取")
    print("="*60)

    # 1. 视频总结
    print("\n步骤 1: 视频总结")
    video_result = await summarize_video(url=video_url)
    print(f"  ✅ 视频标题: {video_result['title']}")
    print(f"  ✅ 总结文件: {video_result['files']['summary_path']}")

    # 2. 提取单词
    print("\n步骤 2: 提取单词")
    vocab_result = await extract_vocabulary(
        content=video_result['summary']['content'],
        word_count=10,
        generate_story=False
    )
    print(f"  ✅ 提取单词数: {len(vocab_result['vocabulary_cards'])}")

    print("\n单词卡片:")
    for i, card in enumerate(vocab_result['vocabulary_cards'][:5], 1):
        print(f"  {i}. {card['word']} - {card['definition']['zh']}")

    return {
        "video": video_result,
        "vocabulary": vocab_result,
    }


async def workflow_2_article_to_vocabulary(article_url):
    """
    工作流 2: 文章学习 → 单词提取

    从文章内容中提取单词。
    """
    print("\n" + "="*60)
    print("工作流 2: 文章学习 → 单词提取")
    print("="*60)

    # 1. 文章处理
    print("\n步骤 1: 文章处理")
    article_result = await process_link(url=article_url)
    print(f"  ✅ 文章标题: {article_result['title']}")
    print(f"  ✅ 阅读时间: {article_result['reading_time']} 分钟")

    # 2. 提取单词
    print("\n步骤 2: 提取单词")
    vocab_result = await extract_vocabulary(
        content=article_result['summary'],
        word_count=8,
        generate_story=True  # 生成故事
    )
    print(f"  ✅ 提取单词数: {len(vocab_result['vocabulary_cards'])}")

    if vocab_result['context_story']:
        print(f"\n📖 故事标题: {vocab_result['context_story']['title']}")
        print(f"故事内容预览:")
        print(vocab_result['context_story']['content'][:150] + "...")

    return {
        "article": article_result,
        "vocabulary": vocab_result,
    }


async def workflow_3_full_learning_session(video_url, article_urls):
    """
    工作流 3: 完整学习会话

    视频 + 多篇文章 + 单词学习，整合为一个完整的学习会话。
    """
    print("\n" + "="*60)
    print("工作流 3: 完整学习会话")
    print("="*60)

    start_time = datetime.now()
    print(f"开始时间: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")

    # 1. 视频学习
    print("\n步骤 1: 视频学习")
    video_result = await summarize_video(url=video_url)
    print(f"  ✅ {video_result['title']}")

    # 2. 扩展阅读
    print(f"\n步骤 2: 扩展阅读 ({len(article_urls)} 篇)")
    article_results = await asyncio.gather(
        *[process_link(url=url) for url in article_urls]
    )
    for i, article in enumerate(article_results, 1):
        print(f"  {i}. ✅ {article['title']}")

    # 3. 整合内容，提取单词
    print("\n步骤 3: 整合内容，提取单词")
    combined_content = "\n\n".join([
        video_result['summary']['content'],
        *[r['summary'] for r in article_results]
    ])

    vocab_result = await extract_vocabulary(
        content=combined_content,
        word_count=15,
        generate_story=True
    )
    print(f"  ✅ 提取单词数: {len(vocab_result['vocabulary_cards'])}")

    end_time = datetime.now()
    elapsed = (end_time - start_time).total_seconds()

    print(f"\n学习会话完成!")
    print(f"结束时间: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"总耗时: {elapsed:.1f} 秒")

    return {
        "video": video_result,
        "articles": article_results,
        "vocabulary": vocab_result,
        "elapsed_time": elapsed,
    }


async def workflow_4_create_learning_note(video_url, article_urls, output_path):
    """
    工作流 4: 创建学习笔记

    整合所有学习内容，创建一份完整的 Markdown 学习笔记。
    """
    print("\n" + "="*60)
    print("工作流 4: 创建学习笔记")
    print("="*60)

    print(f"输出文件: {output_path}")

    # 1. 处理视频
    print("\n步骤 1: 处理视频")
    video_result = await summarize_video(url=video_url)
    print(f"  ✅ {video_result['title']}")

    # 2. 处理文章
    print(f"\n步骤 2: 处理文章")
    article_results = await asyncio.gather(
        *[process_link(url=url) for url in article_urls]
    )
    for i, article in enumerate(article_results, 1):
        print(f"  {i}. ✅ {article['title']}")

    # 3. 提取单词
    print("\n步骤 3: 提取单词")
    combined_content = "\n\n".join([
        video_result['summary']['content'],
        *[r['summary'] for r in article_results]
    ])

    vocab_result = await extract_vocabulary(
        content=combined_content,
        word_count=10,
        generate_story=True
    )
    print(f"  ✅ 提取 {len(vocab_result['vocabulary_cards'])} 个单词")

    # 4. 创建笔记
    print("\n步骤 4: 创建笔记")
    note_content = f"""# 学习笔记 - {datetime.now().strftime('%Y年%m月%d日')}

> 自动生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---

## 🎬 视频总结

**标题**: {video_result['title']}
**平台**: {video_result['metadata']['platform']}
**时长**: {video_result['metadata']['duration']} 秒

### 内容摘要

{video_result['summary']['content']}

---

## 📚 扩展阅读

"""

    for i, article in enumerate(article_results, 1):
        note_content += f"""
### 文章 {i}: {article['title']}

**来源**: {article['source']}
**阅读时间**: {article['reading_time']} 分钟
**难度**: {article['difficulty']}

**摘要**: {article['summary']}

**关键点**:
"""
        for point in article['key_points']:
            note_content += f"- {point}\n"

    note_content += "\n---\n\n## 📝 单词学习\n\n"

    for i, card in enumerate(vocab_result['vocabulary_cards'], 1):
        note_content += f"""
### {i}. {card['word']}

**音标**: {card['phonetic']['us']}
**释义**: {card['definition']['zh']}

**例句**:
"""
        for sentence in card['example_sentences'][:2]:
            note_content += f"- {sentence['sentence']}\n"

    if vocab_result['context_story']:
        note_content += f"""

---

## 📖 上下文故事

**标题**: {vocab_result['context_story']['title']}

{vocab_result['context_story']['content']}

**目标单词**: {', '.join(vocab_result['context_story']['target_words'])}
"""

    note_content += f"""

---

## 📊 学习统计

- 视频总结: 1 个
- 文章处理: {len(article_results)} 篇
- 单词学习: {len(vocab_result['vocabulary_cards'])} 个
- 总字数: {len(combined_content)} 字

---

**学习完成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""

    # 5. 保存笔记
    Path(output_path).parent.mkdir(exist_ok=True)
    Path(output_path).write_text(note_content, encoding="utf-8")
    print(f"  ✅ 笔记已保存: {output_path}")

    return {
        "note_path": output_path,
        "video": video_result,
        "articles": article_results,
        "vocabulary": vocab_result,
    }


async def workflow_5_daily_learning_routine():
    """
    工作流 5: 每日学习例行程序

    展示一个完整的每日学习流程。
    """
    print("\n" + "="*60)
    print("工作流 5: 每日学习例行程序")
    print("="*60)

    print("\n今日学习计划:")
    print("  1. 观看一个技术视频")
    print("  2. 阅读两篇相关文章")
    print("  3. 学习关键单词")
    print("  4. 创建学习笔记")
    print("  5. 查看学习历史")

    # 示例 URLs (实际使用时替换)
    video_url = "https://www.bilibili.com/video/BV1G49MBLE4D"
    article_urls = [
        "https://example.com/article1",
        "https://example.com/article2",
    ]

    # 执行完整学习流程
    note_path = f"data/outputs/daily_note_{datetime.now().strftime('%Y%m%d')}.md"

    result = await workflow_4_create_learning_note(
        video_url=video_url,
        article_urls=article_urls,
        output_path=note_path
    )

    # 查看学习历史
    print("\n步骤 5: 查看学习历史")
    history = get_recent_history(limit=5)
    print(f"  ✅ 最近 {len(history)} 条学习记录")

    print("\n学习历史:")
    for i, record in enumerate(history, 1):
        print(f"  {i}. [{record['module']}] {record['title']}")

    print("\n" + "="*60)
    print("✅ 每日学习例行程序完成!")
    print("="*60)
    print(f"\n学习笔记已保存: {note_path}")
    print("建议:")
    print("  - 定期复习笔记")
    print("  - 重复学习单词")
    print("  - 继续深入学习")

    return result


async def run_all_workflows():
    """
    运行所有学习工作流示例
    """
    print("\n" + "="*60)
    print("Learning Assistant API - 学习工作流示例")
    print("="*60)
    print("\n这些示例展示了完整的学习流程和笔记创建。")
    print("\n注意: 示例中的 URL 是演示用途，实际使用时请替换为真实 URL。")
    print("\n开始执行所有工作流...\n")

    # 测试 URLs (演示用途)
    video_url = "https://www.bilibili.com/video/BV1G49MBLE4D"
    article_urls = [
        "https://example.com/article1",
        "https://example.com/article2",
    ]

    # 执行工作流
    await workflow_1_video_to_vocabulary(video_url)
    await workflow_2_article_to_vocabulary(article_urls[0])
    await workflow_3_full_learning_session(video_url, article_urls)
    await workflow_4_create_learning_note(
        video_url=video_url,
        article_urls=article_urls,
        output_path="data/outputs/demo_note.md"
    )
    # await workflow_5_daily_learning_routine()

    print("\n" + "="*60)
    print("✅ 所有学习工作流示例执行完成!")
    print("="*60)
    print("\n工作流总结:")
    print("  1. 视频 → 单词: 快速从视频学习单词")
    print("  2. 文章 → 单词: 从文章提取单词")
    print("  3. 完整会话: 视频 + 多文章 + 单词")
    print("  4. 学习笔记: 整合所有内容为 Markdown")
    print("  5. 每日例行: 完整的每日学习流程")
    print("\n建议:")
    print("  - 根据需求选择合适的工作流")
    print("  - 定期复习学习笔记")
    print("  - 结合实际学习计划调整")


if __name__ == "__main__":
    """
    主程序入口
    """
    print("\n警告: 这些示例使用演示 URL，实际使用时请替换为真实 URL。")
    print("请确保已配置 API Key 和环境变量。")
    print("\nexport OPENAI_API_KEY='your-key'")

    try:
        asyncio.run(run_all_workflows())
    except KeyboardInterrupt:
        print("\n\n用户中断，退出...")
    except Exception as e:
        print(f"\n\n执行失败: {e}")
        print("\n可能的原因:")
        print("  1. API Key 未配置")
        print("  2. 网络连接问题")
        print("  3. URL 无效")
        print("\n请检查配置和环境后重试。")