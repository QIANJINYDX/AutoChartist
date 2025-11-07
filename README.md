# AutoChartist

<div align="center">

<img width="64" height="64" alt="logo" src="https://github.com/user-attachments/assets/42882da3-71b1-452f-afee-2668b440b217" />

**自然语言 + 数据文件 → Matplotlib 代码 + 高质量图表**

AutoChartist 是一个跨平台工具，帮助数据分析新手、科研人员和运营同学快速生成专业的数据可视化图表，同时产出可复用的 Python 代码。

</div>

---

## 📸 界面预览

<div align="center">

![AutoChartist 界面](screenshot.png)

*AutoChartist 主界面 - 数据概览、AI 推荐、图表生成一体化*

</div>

---

## ✨ 核心特性

- 🎯 **自然语言生成图表**：用简单的中文或英文描述，自动生成 Matplotlib 代码和图表
- 📊 **自动数据理解**：智能识别字段类型、缺失值、统计信息
- 🤖 **AI 智能推荐**：基于数据特征自动推荐合适的图表类型
- ✨ **查询增强**：AI 辅助优化和增强您的查询描述
- 💾 **多格式导出**：支持 PNG/SVG/PDF 图片、Python 脚本、Jupyter Notebook 片段
- 🔒 **完全本地化**：基于 Ollama 本地模型，数据隐私完全保护
- 🖥️ **跨平台支持**：Windows、macOS、Linux 全平台支持
- 🇨🇳 **中文友好**：完美支持中文数据展示和图表标注

## 🚀 快速开始

### 前置要求

1. **安装 Python 3.8+**
2. **安装并运行 Ollama**
   ```bash
   # 访问 https://ollama.ai 下载并安装 Ollama
   # 或使用包管理器安装
   
   # 启动 Ollama 服务（通常会自动启动）
   ollama serve
   
   # 下载推荐模型（qwen3:4b 轻量高效，中文支持优秀）
   ollama pull qwen3:4b
   # 或其他模型：llama3.2, mistral, gemma 等
   ```

### 安装依赖

```bash
# 克隆或下载项目
cd AutoChartist

# 安装依赖
pip install -r requirements.txt
```

### 运行应用

```bash
# 方式 1: 使用 run.py
python run.py

# 方式 2: 直接运行 Streamlit
streamlit run src/autochartist/app.py
```

应用会在浏览器中自动打开（默认地址：http://localhost:8501）

## 📖 使用流程

1. **配置 Ollama**：在侧边栏选择或输入 Ollama 模型名称
2. **导入数据**：拖拽或选择 CSV/XLSX 文件到侧边栏
3. **查看数据概览**：自动分析字段类型、缺失值、统计信息
4. **获取 AI 推荐**（可选）：点击"获取 AI 智能推荐"查看基于数据的图表建议
5. **输入查询**：用自然语言描述想要的图表
   - 示例："画一个每月销售额的折线图，加上 95% 置信区间"
   - 或使用"查询增强"功能优化您的描述
6. **生成图表**：点击"生成图表"，自动生成代码和预览
7. **编辑和导出**：
   - 可以编辑生成的代码并重新渲染
   - 导出为 PNG/SVG/PDF 图片
   - 导出为 Python 脚本或 Jupyter Notebook

## 🛠️ 技术栈

- **前端**：Streamlit
- **数据处理**：Pandas
- **可视化**：Matplotlib
- **AI 模型**：Ollama（本地大语言模型）
- **代码执行**：沙箱环境，安全执行生成的代码

## 📁 项目结构

```
AutoChartist/
├── src/autochartist/
│   ├── app.py          # Streamlit 主应用
│   ├── codegen.py      # LLM 代码生成（Ollama 集成）
│   ├── profiling.py    # 数据理解和分析
│   ├── render.py       # 代码执行与图表渲染
│   ├── exporters.py    # 多格式导出功能
│   └── platform.py     # 平台适配（字体、路径等）
├── assets/
│   └── examples/       # 示例数据文件
├── outputs/            # 生成的图表文件（自动创建）
├── tests/              # 测试用例
├── run.py              # 启动脚本
└── requirements.txt     # 依赖列表
```

## 🔧 配置

### Ollama 配置

1. **安装 Ollama**：访问 [ollama.ai](https://ollama.ai) 下载安装
2. **下载模型**：推荐使用 `qwen3:4b`（轻量高效，中文支持优秀）
   ```bash
   ollama pull qwen3:4b
   ```
   其他可选模型：`llama3.2`、`mistral`、`gemma` 等
3. **在应用中配置**：
   - 侧边栏输入 Ollama API 地址（默认：http://localhost:11434）
   - 选择已安装的模型
   - 点击"刷新模型列表"更新可用模型

### 输出目录

生成的图表文件会自动保存到项目根目录的 `outputs/` 文件夹中，文件名格式：`chart_YYYYMMDD_HHMMSS_<hash>.<format>`

### 字体配置

应用会自动检测系统并配置中文字体：
- **Windows**：Microsoft YaHei, SimHei
- **macOS**：PingFang SC, Arial Unicode MS
- **Linux**：WenQuanYi Micro Hei, Noto Sans CJK SC

## 📝 支持的图表类型

- **单变量分析**：直方图、密度曲线、箱线图、条形图
- **时间序列**：折线图、面积图（支持按天/周/月聚合）
- **多变量分析**：散点图、气泡图、分组条形图、堆叠条形图、热力图
- **统计增强**：误差线、置信区间、回归拟合线
- **自定义样式**：支持颜色、标签、图例等完整自定义

## 💡 功能亮点

### AI 智能推荐
- 基于数据特征自动分析
- 提供多个图表建议及理由
- 一键应用推荐到查询框

### 查询增强
- AI 辅助优化查询描述
- 提供意图分析和关键概念提取
- 显示查询理解置信度

### 代码生成
- 生成完整、可复用的 Matplotlib 代码
- 自动处理中文显示
- 支持代码编辑和重新渲染

### 多格式导出
- **PNG**：高质量位图（200 DPI）
- **SVG**：矢量图，无损缩放
- **PDF**：打印级质量（300 DPI）
- **Python 脚本**：包含完整代码和数据加载
- **Jupyter Notebook**：可直接运行的 notebook 片段

## 📋 使用示例

### 示例 1：时间序列图
```
画一个每月销售额的折线图，加上 95% 置信区间
```

### 示例 2：分布图
```
展示年龄的直方图，分成 20 个区间，使用蓝色填充
```

### 示例 3：对比图
```
画一个按类别分组的销售额条形图，横向显示，添加数值标签
```

### 示例 4：散点图
```
绘制身高和体重的散点图，用颜色区分性别，添加趋势线
```

## ⚠️ 注意事项

1. **Ollama 服务**：确保 Ollama 服务正在运行，否则无法生成图表
2. **模型选择**：不同模型的效果可能不同，建议尝试多个模型
3. **数据格式**：支持 CSV 和 Excel（.xlsx, .xls）格式
4. **代码安全**：生成的代码在沙箱环境中执行，确保安全性

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

MIT License

