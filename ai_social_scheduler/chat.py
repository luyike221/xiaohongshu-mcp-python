#!/usr/bin/env python3
"""交互式聊天客户端"""

import sys
from typing import Optional

import httpx

API_URL = "http://localhost:8012/api/v1/chat"


def send_message(message: str, thread_id: Optional[str] = None) -> dict:
    """发送消息到 API"""
    data = {"message": message}
    if thread_id:
        data["thread_id"] = thread_id
    
    response = httpx.post(API_URL, json=data, timeout=300)
    response.raise_for_status()
    return response.json()


def main():
    """主函数"""
    print("=" * 60)
    print("小红书运营 Agent 交互式聊天")
    print("=" * 60)
    print()
    print("提示:")
    print("  - 输入消息后按 Enter 发送")
    print("  - 输入 'quit' 或 'exit' 退出")
    print("  - 输入 'reset' 重置对话")
    print()
    
    thread_id: Optional[str] = None
    
    while True:
        try:
            if thread_id:
                prompt = f"[对话 ID: {thread_id[:8]}...] 请输入消息: "
            else:
                prompt = "[新对话] 请输入消息: "
            
            user_input = input(prompt).strip()
            
            # 检查退出命令
            if user_input.lower() in ["quit", "exit", "q"]:
                print("\n再见！")
                break
            
            # 检查重置命令
            if user_input.lower() in ["reset", "r"]:
                thread_id = None
                print("✅ 对话已重置\n")
                continue
            
            # 检查空输入
            if not user_input:
                print("⚠️  请输入消息\n")
                continue
            
            # 发送消息
            print("\n📤 发送中...")
            try:
                result = send_message(user_input, thread_id)
                
                thread_id = result.get("thread_id")
                ai_response = result.get("response", "")
                message_count = result.get("message_count", 0)
                
                print(f"\n📥 AI 回复:")
                print(f"{ai_response}")
                print(f"\n消息数: {message_count}")
                print()
                
            except httpx.HTTPStatusError as e:
                print(f"❌ HTTP 错误: {e.response.status_code}")
                print(f"响应: {e.response.text}")
                print()
            except Exception as e:
                print(f"❌ 错误: {e}")
                print()
                
        except KeyboardInterrupt:
            print("\n\n再见！")
            break
        except EOFError:
            print("\n\n再见！")
            break


if __name__ == "__main__":
    main()

