"""
简单测试 generate_image 函数
"""

import asyncio
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

from image_video_mcp.clients import WanT2IClient


async def test_generate_image():
    """测试图像生成"""
    print("=" * 60)
    print("测试 generate_image 函数")
    print("=" * 60)
    
    # 测试参数
    prompt = "一只坐着的橙色猫，表情开心，活泼可爱，真实准确。"
    negative_prompt = "低分辨率、错误、最差质量、低质量、残缺、多余的手指、比例不良、模糊、失真"
    width = 1280
    height = 1280
    seed = None
    size = f"{width}*{height}"
    
    print(f"\n提示词: {prompt}")
    print(f"尺寸: {size} ({width}x{height})")
    print(f"负面提示词: {negative_prompt}")
    print(f"随机种子: {seed}")
    print("\n开始生成图像...")
    
    try:
        async with WanT2IClient() as client:
            # 步骤1：创建任务
            result = await client.generate_image(
                prompt=prompt,
                negative_prompt=negative_prompt,
                size=size,
                seed=seed,
            )
        
        print("\n" + "=" * 60)
        print("任务创建成功:")
        print("=" * 60)
        print(f"✅ 请求成功")
        
        # 打印 API 响应
        print(f"\n请求 ID: {result.get('request_id', 'N/A')}")
        
        output = result.get('output', {})
        if isinstance(output, dict):
            task_id = output.get('task_id', 'N/A')
            task_status = output.get('task_status', 'N/A')
            print(f"任务 ID: {task_id}")
            print(f"任务状态: {task_status}")
            
            # 如果任务还在处理中，轮询获取结果
            if task_status in ['PENDING', 'RUNNING']:
                print("\n" + "=" * 60)
                print("轮询任务结果（每10秒查询一次）...")
                print("=" * 60)
                
                import asyncio
                max_polls = 30  # 最多轮询30次（5分钟）
                poll_count = 0
                
                async with WanT2IClient() as poll_client:
                    while poll_count < max_polls:
                        await asyncio.sleep(10)  # 等待10秒
                        poll_count += 1
                        
                        try:
                            status_result = await poll_client.get_task_status(task_id)
                            status_output = status_result.get('output', {})
                            current_status = status_output.get('task_status', 'UNKNOWN')
                            
                            print(f"\n[{poll_count}] 查询结果: {current_status}")
                            
                            if current_status == 'SUCCEEDED':
                                print("\n" + "=" * 60)
                                print("✅ 任务完成！")
                                print("=" * 60)
                                
                                results = status_output.get('results', [])
                                if results:
                                    print(f"\n生成了 {len(results)} 张图片:")
                                    for i, img_result in enumerate(results, 1):
                                        print(f"\n图片 {i}:")
                                        print(f"  - URL: {img_result.get('url', 'N/A')}")
                                        print(f"  - 原始提示词: {img_result.get('orig_prompt', 'N/A')}")
                                        if 'actual_prompt' in img_result:
                                            print(f"  - 实际提示词: {img_result.get('actual_prompt', 'N/A')}")
                                
                                # 打印完整响应
                                import json
                                print("\n完整响应:")
                                print(json.dumps(status_result, indent=2, ensure_ascii=False))
                                break
                            elif current_status == 'FAILED':
                                print("\n❌ 任务失败")
                                print(f"错误信息: {status_output.get('message', 'N/A')}")
                                break
                            elif current_status in ['PENDING', 'RUNNING']:
                                continue
                            else:
                                print(f"未知状态: {current_status}")
                                break
                        except Exception as e:
                            print(f"查询任务状态时出错: {e}")
                            continue
                    
                    if poll_count >= max_polls:
                        print(f"\n⚠️ 轮询超时（已查询 {max_polls} 次），请稍后手动查询任务状态")
                        print(f"任务 ID: {task_id}")
            
            # 打印输出字段
            print("\n初始响应输出字段:")
            for key, value in output.items():
                if isinstance(value, (str, int, float, bool, type(None))):
                    print(f"  - {key}: {value}")
                else:
                    print(f"  - {key}: {type(value).__name__}")
        else:
            print(f"输出: {output}")
            
        # 打印完整响应（JSON 格式）
        import json
        print("\n初始完整响应:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
            
    except ValueError as e:
        print(f"\n❌ 配置错误: {e}")
        print("请确保已设置 DASHSCOPE_API_KEY 环境变量或在 .env 文件中配置")
        return False
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)
    return True


if __name__ == "__main__":
    success = asyncio.run(test_generate_image())
    sys.exit(0 if success else 1)

