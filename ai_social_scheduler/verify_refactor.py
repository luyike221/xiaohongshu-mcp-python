#!/usr/bin/env python3
"""快速验证重构后的架构（不运行完整测试）"""

import sys


def verify_imports():
    """验证关键模块可以导入"""
    print("验证模块导入...")
    
    try:
        # 验证 graph 模块
        from ai_social_scheduler.ai_agent.graph import (
            create_content_publish_graph,
            create_workflow_by_name,
            AgentState,
        )
        print("✅ graph 模块导入成功")
        
        # 验证 workflow 模块
        from ai_social_scheduler.ai_agent.workflows.content_publish import (
            ContentPublishWorkflow
        )
        print("✅ ContentPublishWorkflow 导入成功")
        
        # 验证 agent 模块
        from ai_social_scheduler.ai_agent.agents.content.content_generator_agent import (
            ContentGeneratorAgent
        )
        print("✅ ContentGeneratorAgent 导入成功")
        
        return True
        
    except ImportError as e:
        print(f"❌ 导入失败: {e}")
        return False


def verify_structure():
    """验证代码结构"""
    print("\n验证代码结构...")
    
    try:
        from ai_social_scheduler.ai_agent.graph.factory import create_content_publish_graph
        from ai_social_scheduler.ai_agent.workflows.content_publish import ContentPublishWorkflow
        from ai_social_scheduler.ai_agent.agents.content.content_generator_agent import ContentGeneratorAgent
        
        # 检查函数签名
        import inspect
        
        # 检查 create_content_publish_graph
        sig = inspect.signature(create_content_publish_graph)
        assert 'llm_model' in sig.parameters
        assert 'llm_temperature' in sig.parameters
        print("✅ create_content_publish_graph 签名正确")
        
        # 检查 ContentPublishWorkflow
        sig = inspect.signature(ContentPublishWorkflow.__init__)
        params = list(sig.parameters.keys())
        assert 'workflow_graph' in params
        print("✅ ContentPublishWorkflow 构造函数签名正确")
        
        # 检查 ContentGeneratorAgent.run
        assert hasattr(ContentGeneratorAgent, 'run')
        sig = inspect.signature(ContentGeneratorAgent.run)
        assert 'state' in sig.parameters
        print("✅ ContentGeneratorAgent.run 方法存在且签名正确")
        
        return True
        
    except Exception as e:
        print(f"❌ 结构验证失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def verify_workflow_definition():
    """验证工作流定义"""
    print("\n验证工作流定义...")
    
    try:
        from ai_social_scheduler.ai_agent.graph.workflow import create_content_publish_workflow
        import inspect
        
        sig = inspect.signature(create_content_publish_workflow)
        params = list(sig.parameters.keys())
        
        required_params = [
            'decision_engine',
            'strategy_manager',
            'material_agent',
            'content_agent',
            'publisher_agent',
            'state_manager',
        ]
        
        for param in required_params:
            assert param in params, f"缺少参数: {param}"
        
        print("✅ create_content_publish_workflow 参数完整")
        
        return True
        
    except Exception as e:
        print(f"❌ 工作流定义验证失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主函数"""
    print("="*60)
    print("重构验证脚本 - 不运行完整测试")
    print("="*60)
    print()
    
    all_passed = True
    
    # 验证导入
    if not verify_imports():
        all_passed = False
    
    # 验证结构
    if not verify_structure():
        all_passed = False
    
    # 验证工作流定义
    if not verify_workflow_definition():
        all_passed = False
    
    print("\n" + "="*60)
    if all_passed:
        print("🎉 所有验证通过！重构成功完成。")
        print("\n架构说明：")
        print("✨ 使用 LangGraph StateGraph 进行显式节点编排")
        print("✨ 每个步骤都是独立节点，通过共享状态传递数据")
        print("✨ Agent 返回结构化结果而非自然语言")
        print("✨ 按需加载 Agent，避免不必要的初始化")
        print("\n下一步：")
        print("1. 运行完整测试：python3 test_content_publish.py --single")
        print("2. 查看重构指南：cat REFACTOR_GUIDE.md")
        print("="*60)
        sys.exit(0)
    else:
        print("❌ 验证失败，请检查上述错误。")
        print("="*60)
        sys.exit(1)


if __name__ == "__main__":
    main()

