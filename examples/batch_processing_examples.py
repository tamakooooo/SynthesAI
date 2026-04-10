"""
Batch Processing Examples - 批量处理示例

展示如何使用 Learning Assistant 的批量处理功能。
"""

import asyncio
from learning_assistant.api import summarize_video, process_link
from learning_assistant.core.batch import BatchTaskManager, TaskPriority


async def example_1_basic_batch_processing():
    """
    示例 1: 基础批量视频处理

    使用 BatchTaskManager 批量处理多个视频。
    """
    print("\n" + "="*60)
    print("示例 1: 基础批量视频处理")
    print("="*60)

    # 创建批量任务管理器
    manager = BatchTaskManager(
        max_workers=3,           # 最多 3 个并发
        memory_limit_mb=500,     # 内存限制 500MB
        retry_failed=True,       # 自动重试失败任务
        max_retries=2,           # 最多重试 2 次
    )

    # 视频列表
    video_urls = [
        "https://www.bilibili.com/video/BV1...",
        "https://www.bilibili.com/video/BV2...",
        "https://www.youtube.com/watch?v=...",
    ]

    # 添加任务
    print(f"\n添加 {len(video_urls)} 个视频处理任务...")

    for i, url in enumerate(video_urls, 1):
        await manager.add_task(
            task_id=f"video_{i}",
            func=summarize_video,
            args=(url,),
            kwargs={
                "format": "markdown",
                "language": "zh",
            },
            priority=TaskPriority.NORMAL,
        )

    # 设置进度回调
    def on_progress(stats):
        print(f"进度: {stats.completed}/{stats.total_tasks} 完成, "
              f"失败: {stats.failed}, "
              f"吞吐量: {stats.throughput:.2f} tasks/s")

    manager.set_progress_callback(on_progress)

    # 处理所有任务
    print("\n开始处理...")
    results = await manager.process_all()

    # 显示结果
    print("\n处理结果:")
    for task_id, result in results.items():
        if result.status.value == "completed":
            print(f"  ✅ {task_id}: {result.result.get('title', 'N/A')}")
        else:
            print(f"  ❌ {task_id}: {result.error}")

    # 显示统计信息
    stats = manager.get_statistics()
    print(f"\n统计:")
    print(f"  总任务: {stats.total_tasks}")
    print(f"  完成: {stats.completed}")
    print(f"  失败: {stats.failed}")
    print(f"  总耗时: {stats.total_duration:.2f}s")
    print(f"  平均耗时: {stats.average_task_duration:.2f}s")
    print(f"  峰值内存: {stats.peak_memory_mb:.1f}MB")
    print(f"  吞吐量: {stats.throughput:.2f} tasks/s")


async def example_2_mixed_batch_processing():
    """
    示例 2: 混合批量处理

    同时处理视频和文章，使用不同优先级。
    """
    print("\n" + "="*60)
    print("示例 2: 混合批量处理")
    print("="*60)

    manager = BatchTaskManager(max_workers=4)

    # 添加视频任务（高优先级）
    video_urls = ["https://www.bilibili.com/video/BV1..."]

    for i, url in enumerate(video_urls, 1):
        await manager.add_task(
            task_id=f"video_{i}",
            func=summarize_video,
            args=(url,),
            priority=TaskPriority.HIGH,  # 高优先级
        )

    # 添加文章任务（普通优先级）
    article_urls = [
        "https://example.com/article1",
        "https://example.com/article2",
    ]

    for i, url in enumerate(article_urls, 1):
        await manager.add_task(
            task_id=f"article_{i}",
            func=process_link,
            args=(url,),
            priority=TaskPriority.NORMAL,  # 普通优先级
        )

    # 处理所有任务
    print(f"\n处理 {len(video_urls)} 个视频 + {len(article_urls)} 个文章...")
    results = await manager.process_all()

    # 显示结果统计
    video_completed = sum(
        1 for tid, r in results.items()
        if tid.startswith("video_") and r.status.value == "completed"
    )
    article_completed = sum(
        1 for tid, r in results.items()
        if tid.startswith("article_") and r.status.value == "completed"
    )

    print(f"\n结果:")
    print(f"  视频完成: {video_completed}/{len(video_urls)}")
    print(f"  文章完成: {article_completed}/{len(article_urls)}")


async def example_3_resource_aware_processing():
    """
    示例 3: 资源感知处理

    监控资源使用，动态调整并发数。
    """
    print("\n" + "="*60)
    print("示例 3: 资源感知处理")
    print("="*60)

    # 设置资源限制
    manager = BatchTaskManager(
        max_workers=5,
        memory_limit_mb=300,      # 较低的内存限制
        cpu_limit_percent=70,    # CPU 限制
    )

    # 添加任务
    urls = [f"https://example.com/video{i}" for i in range(10)]

    for i, url in enumerate(urls, 1):
        await manager.add_task(
            task_id=f"task_{i}",
            func=summarize_video,
            args=(url,),
        )

    # 监控资源使用
    from learning_assistant.core.batch import ResourceMonitor

    monitor = ResourceMonitor(memory_limit_mb=300)

    print("\n资源监控:")
    usage = monitor.get_current_usage()
    print(f"  当前内存: {usage.memory_mb:.1f}MB ({usage.memory_percent:.1f}%)")
    print(f"  当前 CPU: {usage.cpu_percent:.1f}%")

    # 处理任务
    results = await manager.process_all()

    # 显示资源统计
    stats = manager.get_statistics()
    print(f"\n峰值内存使用: {stats.peak_memory_mb:.1f}MB")


async def example_4_error_handling_and_retry():
    """
    示例 4: 错误处理和重试

    展示如何处理失败任务和重试机制。
    """
    print("\n" + "="*60)
    print("示例 4: 错误处理和重试")
    print("="*60)

    manager = BatchTaskManager(
        max_workers=2,
        retry_failed=True,       # 启用自动重试
        max_retries=2,           # 最多重试 2 次
    )

    # 添加任务（包括可能失败的）
    urls = [
        "https://valid-url.com/video",
        "https://invalid-url-12345.com/video",  # 会失败
        "https://another-valid-url.com/video",
    ]

    # 设置错误回调
    def on_error(task_id, error):
        print(f"  ⚠️ 任务 {task_id} 失败: {error}")

    manager.set_error_callback(on_error)

    # 添加任务
    for i, url in enumerate(urls, 1):
        await manager.add_task(
            task_id=f"task_{i}",
            func=summarize_video,
            args=(url,),
        )

    # 处理所有任务
    print("\n开始处理...")
    results = await manager.process_all()

    # 分析结果
    failed = [tid for tid, r in results.items() if r.status.value == "failed"]

    print(f"\n失败任务: {len(failed)}")
    for task_id in failed:
        result = results[task_id]
        print(f"  ❌ {task_id}: {result.error}")


async def example_5_progress_tracking():
    """
    示例 5: 进度跟踪

    实时显示批量处理进度。
    """
    print("\n" + "="*60)
    print("示例 5: 进度跟踪")
    print("="*60)

    manager = BatchTaskManager(max_workers=3)

    # 添加任务
    urls = [f"https://example.com/video{i}" for i in range(5)]

    for i, url in enumerate(urls, 1):
        await manager.add_task(
            task_id=f"task_{i}",
            func=summarize_video,
            args=(url,),
        )

    # 进度回调
    def on_progress(stats):
        progress = (stats.completed / stats.total_tasks) * 100 if stats.total_tasks > 0 else 0
        print(f"\r进度: [{progress:.0f}%] "
              f"完成: {stats.completed}/{stats.total_tasks} "
              f"失败: {stats.failed} "
              f"速度: {stats.throughput:.2f} tasks/s", end="")

    manager.set_progress_callback(on_progress)

    # 处理
    print("\n处理中...")
    await manager.process_all()
    print("\n\n完成！")


async def run_all_examples():
    """运行所有示例"""
    print("\n" + "="*60)
    print("Learning Assistant - 批量处理示例")
    print("="*60)

    await example_1_basic_batch_processing()
    await example_2_mixed_batch_processing()
    await example_3_resource_aware_processing()
    await example_4_error_handling_and_retry()
    await example_5_progress_tracking()

    print("\n" + "="*60)
    print("✅ 所有示例完成!")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(run_all_examples())