"""启动脚本：运行 AutoChartist"""

import sys
from pathlib import Path

# 添加 src 目录到路径
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

if __name__ == "__main__":
    import streamlit.web.cli as stcli
    
    # 获取 app.py 的路径
    app_path = Path(__file__).parent / "src" / "autochartist" / "app.py"
    
    # 运行 Streamlit
    sys.argv = ["streamlit", "run", str(app_path)]
    stcli.main()

