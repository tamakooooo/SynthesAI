"""
Batch Processing Examples - Learning Assistant API 批量处理示例

这些示例展示了如何高效地批量处理多个视频、文章和单词。
重点介绍并行处理和错误处理。
"""

import asyncio
import time
from pathlib import Path
from learning_assistant.api import (
    summarize_video,
    process_link,
    extract_vocabulary,
)
from learning_assistant.api.exceptions import (
    VideoNotFoundError,
    VideoDownloadError,
    TranscriptionError,
    LLMAPIError,
)


async def example_1_serial_processing(urls):
    """
    示例 1: 串行处理 (不推荐)

    逐个处理，效率低，适合对比测试。
    """
    print("\n" + "="*60)
    print("示例 1: 串行处理 (不推荐)")
    print("="*60)

    print(f"\n处理 {len(urls)} 个视频 (串行):")
    start_time = time.time()

    results = []
    for i, url in enumerate(urls, 1):
        print(f"\n处理第 {i}/{len(urls)} 个: {url}")

        try:
            result = await summarize_video(url=url)
            results.append(result)
            print(f"  ✅ 成功: {result['title']}")

        except Exception as e:
            results.append(None)
            print(f"  ❌ 失败: {e}")

    elapsed_time = time.time() - start_time
    successes = sum(1 for r in results if r is not None)

    print(f"\n统计:")
    print(f"  成功: {successes}/{len(urls)}")
    print(f"  失败: {len(urls) - successes}/{len(urls)}")
    print(f"  总耗时: {elapsed_time:.1f} 秒")
    print(f"  平均耗时: {elapsed_time/len(urls):.1f} 秒/视频")

    return results


async def example_2_parallel_processing(urls):
    """
    示例 2: 并行处理 (推荐)

    使用 asyncio.gather 并发处理，效率高。
    """
    print("\n" + "="*60)
    print("示例 2: 并行处理 (推荐)")
    print("="*60)

    print(f"\n处理 {len(urls)} 个视频 (并行):")
    start_time = time.time()

    # 创建所有任务
    tasks = [summarize_video(url=url) for url in urls]

    # 并发执行所有任务
    results = await asyncio.gather(*tasks, return_exceptions=True)

    elapsed_time = time.time() - start_time
    successes = sum(1 for r in results if not isinstance(r, Exception))

    print(f"\n统计:")
    print(f"  成功: {successes}/{len(urls)}")
    print(f"  失败: {len(urls) - successes}/{len(urls)}")
    print(f"  总耗时: {elapsed_time:.1f} 秒")
    print(f"  平均耗时: {elapsed_time/len(urls):.1f} 秒/视频")
    print(f"  性能提升: {(elapsed_time/len(urls))/10:.1f}x")  # 假设串行平均 10 秒

    # 显示结果
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            print(f"\n{i+1}. ❌ 失败: {urls[i]} - {result}")
        else:
            print(f"\n{i+1}. ✅ 成功: {result['title']}")

    return results


async def example_3_batch_with_error_handling(urls):
    """
    示例 3: 批量处理 - 完整错误处理

    展示如何处理各种类型的错误。
    """
    print("\n" + "="*60)
    print("示例 3: 批量处理 - 完整错误处理")
    print("="*60)

    print(f"\n处理 {len(urls)} 个视频 (带错误处理):")

    results = await asyncio.gather(
        *[summarize_video(url=url) for url in urls],
        return_exceptions=True
    )

    # 分类错误类型
    success_count = 0
    error_stats = {
        "VideoNotFoundError": 0,
        "VideoDownloadError": 0,
        "TranscriptionError": 0,
        "LLMAPIError": 0,
        "OtherError": 0,
    }

    for i, result in enumerate(results):
        if isinstance(result, Exception):
            if isinstance(result, VideoNotFoundError):
                error_stats["VideoNotFoundError"] += 1
                print(f"  {i+1}. ❌ 视频不存在: {urls[i]}")

            elif isinstance(result, VideoDownloadError):
                error_stats["VideoDownloadError"] += 1
                print(f"  {i+1}. ❌ 下载失败: {urls[i]} - {result}")

            elif isinstance(result, TranscriptionError):
                error_stats["TranscriptionError"] += 1
                print(f"  {i+1}. ❌ 转录失败: {urls[i]} - {result}")

            elif isinstance(result, LLMAPIError):
                error_stats["LLMAPIError"] += 1
                print(f"  {i+1}. ❌ LLM 错误: {urls[i]} - {result}")

            else:
                error_stats["OtherError"] += 1
                print(f"  {i+1}. ❌ 其他错误: {urls[i]} - {result}")

        else:
            success_count += 1
            print(f"  {i+1}. ✅ 成功: {result['title']}")

    print(f"\n统计:")
    print(f"  成功: {success_count}/{len(urls)}")
    print(f"\n错误类型分布:")
    for error_type, count in error_stats.items():
        if count > 0:
            print(f"  {error_type}: {count}")

    return results


async def example_4_mixed_batch_processing(video_urls, article_urls):
    """
    示例 4: 混合批量处理

    同时处理视频和文章，展示多任务并行。
    """
    print("\n" + "="*60)
    print("示例 4: 混合批量处理")
    print("="*60)

    print(f"\n处理 {len(video_urls)} 个视频 + {len(article_urls)} 个文章 (并行):")
    start_time = time.time()

    # 创建所有任务
    video_tasks = [summarize_video(url=url) for url in video_urls]
    article_tasks = [process_link(url=url) for url in article_urls]

    # 并发执行所有任务
    all_results = await asyncio.gather(
        *video_tasks,
        *article_tasks,
        return_exceptions=True
    )

    elapsed_time = time.time() - start_time

    # 分离结果
    video_results = all_results[:len(video_urls)]
    article_results = all_results[len(video_urls):]

    # 统计
    video_success = sum(1 for r in video_results if not isinstance(r, Exception))
    article_success = sum(1 for r in article_results if not isinstance(r, Exception))

    print(f"\n统计:")
    print(f"  视频处理: {video_success}/{len(video_urls)}")
    print(f"  文章处理: {article_success}/{len(article_urls)}")
    print(f"  总成功: {video_success + article_success}/{len(all_results)}")
    print(f"  总耗时: {elapsed_time:.1f} 秒")

    return {
        "videos": video_results,
        "articles": article_results,
    }


async def example_5_limited_concurrency(urls, max_concurrent=3):
    """
    示例 5: 限制并发数

    控制并发任务数量，避免资源过载。
    """
    print("\n" + "="*60)
    print(f"示例 5: 限制并发数 (max={max_concurrent})")
    print("="*60)

    print(f"\n处理 {len(urls)} 个视频 (并发限制: {max_concurrent}):")
    start_time = time.time()

    # 分批处理
    batches = [
        urls[i:i + max_concurrent]
        for i in range(0, len(urls), max_concurrent)
    ]

    print(f"\n分为 {len(batches)} 批:")

    all_results = []
    for batch_idx, batch in enumerate(batches, 1):
        print(f"\n批次 {batch_idx}/{len(batches)} ({len(batch)} 个视频):")

        tasks = [summarize_video(url=url) for url in batch]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        batch_success = sum(1 for r in results if not isinstance(r, Exception))
        print(f"  成功: {batch_success}/{len(batch)}")

        all_results.extend(results)

    elapsed_time = time.time() - start_time
    total_success = sum(1 for r in all_results if not isinstance(r, Exception))

    print(f"\n总计:")
    print(f"  成功: {total_success}/{len(urls)}")
    print(f"  总耗时: {elapsed_time:.1f} 秒")
    print(f"  平均耗时: {elapsed_time/len(urls):.1f} 秒/视频")

    return all_results


async def example_6_with_progress_tracking(urls):
    """
    示例 6: 批量处理 - 进度跟踪

    显示实时处理进度。
    """
    print("\n" + "="*60)
    print("示例 6: 批量处理 - 进度跟踪")
    print("="*60)

    print(f"\n处理 {len(urls)} 个视频 (带进度跟踪):")

    results = []
    total = len(urls)

    async def process_with_progress(url, index):
        """处理单个视频并显示进度"""
        progress = (index + 1) / total * 100
        print(f"\n[{progress:.1f}%] 处理: {url}")

        try:
            result = await summarize_video(url=url)
            print(f"  ✅ 完成: {result['title']}")
            return result

        except Exception as e:
            print(f"  ❌ 失败: {e}")
            return None

    # 并发处理
    tasks = [
        process_with_progress(url, i)
        for i, url in enumerate(urls)
    ]

    results = await asyncio.gather(*tasks)

    successes = sum(1 for r in results if r is not None)
    print(f"\n完成! 成功: {successes}/{total}")

    return results


async def example_7_with_output_collection(urls, output_dir="batch_outputs"):
    """
    示例 7: 批量处理 - 收集输出文件

    处理多个视频，统一收集和管理输出文件。
    """
    print("\n" + "="*60)
    print("示例 7: 批量处理 - 收集输出文件")
    print("="*60)

    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)

    print(f"\n处理 {len(urls)} 个视频:")
    print(f"输出目录: {output_path}")

    results = await asyncio.gather(
        *[summarize_video(url=url) for url in urls],
        return_exceptions=True
    )

    # 收集输出文件信息
    output_files = []

    for i, result in enumerate(results):
        if not isinstance(result, Exception):
            files = result['files']
            output_files.append({
                "title": result['title'],
                "summary": files.get('summary_path'),
                "subtitle": files.get('subtitle_path'),
            })
            print(f"\n{i+1}. ✅ {result['title']}")
            print(f"  总结: {files.get('summary_path')}")
            print(f"  字幕: {files.get('subtitle_path')}")

    print(f"\n输出文件总数: {len(output_files)}")
    print(f"总结文件: {sum(1 for f in output_files if f['summary'])}")
    print(f"字幕文件: {sum(1 for f in output_files if f['subtitle'])}")

    return {
        "results": results,
        "output_files": output_files,
    }


async def run_all_examples():
    """
    运行所有批量处理示例

    展示不同的批量处理策略和优化方法。
    """
    print("\n" + "="*60)
    print("Learning Assistant API - 批量处理示例")
    print("="*60)
    print("\n这些示例展示了如何高效地批量处理多个任务。")
    print("\n注意: 示例中的 URL 是演示用途，实际使用时请替换为真实 URL。")
    print("\n开始执行所有示例...\n")

    # 测试 URLs (演示用途)
    video_urls = [
        "https://www.bilibili.com/video/BV1G49MBLE4D",
        "https://www.bilibili.com/video/BV1Another",
        "https://www.bilibili.com/video/BV1Third",
    ]

    article_urls = [
        "https://example.com/article1",
        "https://example.com/article2",
    ]

    # 执行示例
    # await example_1_serial_processing(video_urls[:2])  # 只用 2 个演示
    await example_2_parallel_processing(video_urls[:2])
    await example_3_batch_with_error_handling(video_urls[:2])
    # await example_4_mixed_batch_processing(video_urls[:2], article_urls[:1])
    await example_5_limited_concurrency(video_urls[:3], max_concurrent=2)
    await example_6_with_progress_tracking(video_urls[:2])
    await example_7_with_output_collection(video_urls[:2])

    print("\n" + "="*60)
    print("✅ 所有批量处理示例执行完成!")
    print("="*60)
    print("\n性能对比总结:")
    print("  - 串行处理: 低效率，适合少量任务")
    print("  - 并行处理: 高效率，推荐用于批量任务")
    print("  - 限制并发: 避免资源过载，适合大批量任务")
    print("\n建议:")
    print("  - <5 个任务: 直接并行处理")
    print("  - 5-20 个任务: 限制并发 (max_concurrent=3-5)")
    print("  - >20 个任务: 分批处理 + 进度跟踪")


if __name__ == "__main__":
    """
    主程序入口
    """
    print("\n警告: 这些示例使用演示 URL，实际使用时请替换为真实 URL。")
    print("请确保已配置 API Key 和环境变量。")
    print("\nexport OPENAI_API_KEY='your-key'")

    try:
        asyncio.run(run_all_examples())
    except KeyboardInterrupt:
        print("\n\n用户中断，退出...")
    except Exception as e:
        print(f"\n\n执行失败: {e}")
        print("\n可能的原因:")
        print("  1. API Key 未配置")
        print("  2. 网络连接问题")
        print("  3. URL 无效")
        print("\n请检查配置和环境后重试。")