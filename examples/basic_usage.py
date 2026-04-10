"""
Basic Usage Examples - Learning Assistant API 基础使用示例

这些示例展示了 Learning Assistant API 的基本使用方法。
适合新手快速上手。
"""

import asyncio
from learning_assistant.api import (
    summarize_video,
    process_link,
    extract_vocabulary,
    list_available_skills,
    get_recent_history,
)


async def example_1_basic_video_summary():
    """
    示例 1: 基础视频总结

    最简单的使用方式，只需提供视频 URL。
    """
    print("\n" + "="*60)
    print("示例 1: 基础视频总结")
    print("="*60)

    url = "https://www.bilibili.com/video/BV1G49MBLE4D"

    print(f"处理视频: {url}")

    result = await summarize_video(url=url)

    print(f"\n✅ 视频标题: {result['title']}")
    print(f"✅ 平台: {result['metadata']['platform']}")
    print(f"✅ 时长: {result['metadata']['duration']} 秒")
    print(f"✅ 总结文件: {result['files']['summary_path']}")
    print(f"✅ 字幕文件: {result['files']['subtitle_path']}")

    print("\n总结内容预览:")
    print(result['summary']['content'][:200] + "...")

    return result


async def example_2_video_with_options():
    """
    示例 2: 视频总结 - 自定义选项

    展示如何自定义输出格式、语言、目录等选项。
    """
    print("\n" + "="*60)
    print("示例 2: 视频总结 - 自定义选项")
    print("="*60)

    url = "https://www.bilibili.com/video/BV1G49MBLE4D"

    print(f"处理视频: {url}")
    print("自定义配置:")
    print("  - 输出格式: markdown")
    print("  - 总结语言: zh")
    print("  - 输出目录: ./my-outputs")

    result = await summarize_video(
        url=url,
        format="markdown",
        language="zh",
        output_dir="./my-outputs"
    )

    print(f"\n✅ 视频标题: {result['title']}")
    print(f"✅ 输出文件: {result['files']['summary_path']}")

    return result


async def example_3_link_learning():
    """
    示例 3: 链接学习 - 网页文章处理

    处理网页文章，生成知识卡片。
    """
    print("\n" + "="*60)
    print("示例 3: 链接学习 - 网页文章处理")
    print("="*60)

    url = "https://example.com/article"  # 替换为实际 URL

    print(f"处理文章: {url}")

    result = await process_link(url=url)

    print(f"\n✅ 文章标题: {result['title']}")
    print(f"✅ 来源: {result['source']}")
    print(f"✅ 阅读时间: {result['reading_time']} 分钟")
    print(f"✅ 难度: {result['difficulty']}")
    print(f"✅ 字数: {result['word_count']}")

    print("\n关键点:")
    for i, point in enumerate(result['key_points'], 1):
        print(f"  {i}. {point}")

    return result


async def example_4_vocabulary_extraction():
    """
    示例 4: 单词学习 - 词汇提取

    从文本中提取单词，生成单词卡。
    """
    print("\n" + "="*60)
    print("示例 4: 单词学习 - 词汇提取")
    print("="*60)

    content = """
    Machine learning is transforming industries across the globe.
    Deep learning algorithms are achieving unprecedented accuracy
    in tasks like image recognition and natural language processing.
    """

    print("从文本提取单词:")
    print(content.strip())

    result = await extract_vocabulary(
        content=content,
        word_count=5,
        difficulty="intermediate",
        generate_story=False  # 不生成故事，快速示例
    )

    print(f"\n✅ 提取单词数: {len(result['vocabulary_cards'])}")

    print("\n单词卡片:")
    for card in result['vocabulary_cards']:
        print(f"\n  单词: {card['word']}")
        print(f"  音标: {card['phonetic']['us']}")
        print(f"  释义: {card['definition']['zh']}")
        if card['example_sentences']:
            print(f"  例句: {card['example_sentences'][0]['sentence']}")

    return result


async def example_5_vocabulary_with_story():
    """
    示例 5: 单词学习 - 生成上下文故事

    提取单词并生成包含这些单词的上下文故事。
    """
    print("\n" + "="*60)
    print("示例 5: 单词学习 - 生成上下文故事")
    print("="*60)

    content = """
    Artificial intelligence is revolutionizing healthcare.
    Machine learning models can diagnose diseases with remarkable precision.
    Natural language processing enables chatbots to understand patient queries.
    """

    print("从文本提取单词并生成故事:")

    result = await extract_vocabulary(
        content=content,
        word_count=5,
        difficulty="intermediate",
        generate_story=True
    )

    print(f"\n✅ 提取单词数: {len(result['vocabulary_cards'])}")

    if result['context_story']:
        print(f"\n📖 故事标题: {result['context_story']['title']}")
        print(f"\n故事内容:")
        print(result['context_story']['content'])
        print(f"\n目标单词: {', '.join(result['context_story']['target_words'])}")

    return result


def example_6_list_skills():
    """
    示例 6: 列出可用技能

    查看所有已安装的模块和技能。
    """
    print("\n" + "="*60)
    print("示例 6: 列出可用技能")
    print("="*60)

    skills = list_available_skills()

    print(f"\n找到 {len(skills)} 个技能:")

    for skill in skills:
        print(f"\n  技能名称: {skill['name']}")
        print(f"  描述: {skill['description']}")
        print(f"  版本: {skill['version']}")
        print(f"  状态: {skill['status']}")

    return skills


def example_7_view_history():
    """
    示例 7: 查看学习历史

    查看最近的学习记录。
    """
    print("\n" + "="*60)
    print("示例 7: 查看学习历史")
    print("="*60)

    records = get_recent_history(limit=10)

    print(f"\n最近 {len(records)} 条学习记录:")

    for i, record in enumerate(records, 1):
        print(f"\n{i}. [{record['timestamp']}] {record['module']}")
        print(f"   标题: {record['title']}")
        print(f"   URL: {record['url']}")
        print(f"   状态: {record['status']}")

    return records


async def run_all_examples():
    """
    运行所有示例

    按顺序执行所有示例，展示 API 的完整功能。
    """
    print("\n" + "="*60)
    print("Learning Assistant API - 基础使用示例")
    print("="*60)
    print("\n这些示例展示了 API 的基本使用方法。")
    print("请确保已配置 API Key 和环境变量。")
    print("\n开始执行所有示例...\n")

    # 执行异步示例
    await example_1_basic_video_summary()
    await example_2_video_with_options()
    await example_3_link_learning()
    await example_4_vocabulary_extraction()
    await example_5_vocabulary_with_story()

    # 执行同步示例
    example_6_list_skills()
    example_7_view_history()

    print("\n" + "="*60)
    print("✅ 所有示例执行完成!")
    print("="*60)
    print("\n提示:")
    print("  - 查看 ./my-outputs/ 目录查看输出文件")
    print("  - 阅读 docs/API_EXAMPLES.md 了解更多高级用法")
    print("  - 阅读 docs/BEST_PRACTICES.md 了解最佳实践")


if __name__ == "__main__":
    """
    主程序入口

    使用 asyncio.run() 运行所有异步示例。
    """
    # 注意: 实际运行前，请先配置 API Key
    # export OPENAI_API_KEY="your-key"

    try:
        asyncio.run(run_all_examples())
    except KeyboardInterrupt:
        print("\n\n用户中断，退出...")
    except Exception as e:
        print(f"\n\n执行失败: {e}")
        print("\n可能的原因:")
        print("  1. API Key 未配置")
        print("  2. 网络连接问题")
        print("  3. URL 无效或视频不存在")
        print("\n请检查配置和环境后重试。")