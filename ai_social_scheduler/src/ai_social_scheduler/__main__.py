"""CLI 入口"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

if __name__ == "__main__":
    # TODO: 实现 CLI 入口逻辑
    print("小红书运营 Agent CLI")
    print("使用 --help 查看可用命令")

