"""代码生成模块：LLM 提示词构建、代码生成、安全检查"""

import os
import json
from typing import Dict, List, Optional, Any
from pathlib import Path

try:
    import openai
except ImportError:
    openai = None

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from .platform import get_config_dir, get_chart_font


class CodeGenerator:
    """代码生成器，支持多种 LLM 后端"""
    
    def __init__(self, model_type: str = "openai", api_key: Optional[str] = None, model_name: Optional[str] = None):
        """
        Args:
            model_type: 模型类型 ('openai', 'qwen', 'ollama')
            api_key: API 密钥（如果为 None，从环境变量或配置文件读取）
            model_name: 模型名称（用于 Ollama，例如 'llama3.2'）
        """
        self.model_type = model_type
        self.config_dir = get_config_dir()  # 必须先设置 config_dir
        self.api_key = api_key or self._load_api_key()
        self.model_name = model_name or os.getenv("OLLAMA_MODEL", "llama3.2")
        
    def _load_api_key(self) -> Optional[str]:
        """从环境变量或配置文件加载 API 密钥"""
        # 先尝试环境变量
        if self.model_type == "openai":
            key = os.getenv("OPENAI_API_KEY")
        elif self.model_type == "qwen":
            key = os.getenv("QWEN_API_KEY")
        else:
            key = None
        
        # 如果环境变量没有，尝试配置文件
        if not key:
            config_file = self.config_dir / "config.json"
            if config_file.exists():
                try:
                    with open(config_file, "r", encoding="utf-8") as f:
                        config = json.load(f)
                        key = config.get(f"{self.model_type}_api_key")
                except Exception:
                    pass
        
        return key
    
    def build_prompt(
        self,
        schema: List[Dict[str, Any]],
        sample_data: List[Dict[str, Any]],
        intent: str,
    ) -> str:
        """
        构建 LLM 提示词
        
        Args:
            schema: 数据模式（来自 profiling）
            sample_data: 样例数据（前 100 行）
            intent: 用户意图（自然语言）
        
        Returns:
            完整的提示词字符串
        """
        # 格式化列信息
        columns_info = []
        for col in schema:
            col_str = f"- {col['name']} ({col['dtype']})"
            if col.get("n_missing", 0) > 0:
                col_str += f", 缺失值: {col['n_missing']} ({col.get('missing_pct', 0):.1f}%)"
            columns_info.append(col_str)
        
        columns_text = "\n".join(columns_info)
        
        # 格式化样例数据（只显示前 5 行）
        sample_text = ""
        if sample_data:
            sample_df_text = "\n".join([
                f"  {i+1}. {row}" for i, row in enumerate(sample_data[:5])
            ])
            sample_text = f"数据样例（前 5 行）：\n{sample_df_text}"
        
        prompt = f"""你是专业的 Python 数据可视化工程师，专门使用 Matplotlib 和 Pandas 生成高质量的数据图表代码。

## 数据列信息：
{columns_text}

## {sample_text}

## 用户需求：
{intent}

## 代码要求：
1. **仅使用 pandas 和 matplotlib**，不要使用其他库（如 seaborn, plotly）
2. **必须生成 fig 和 ax 变量**：
   ```python
   fig, ax = plt.subplots(figsize=(8, 5))
   ```
3. **不要使用 plt.show()**，不要弹出窗口
4. **设置中文字体支持**：
   使用支持中文的字体，按平台自动选择：
   ```python
   import platform
   system = platform.system()
   if system == 'Windows':
       plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'DejaVu Sans']
   elif system == 'Darwin':
       plt.rcParams['font.sans-serif'] = ['PingFang SC', 'Arial Unicode MS', 'DejaVu Sans']
   else:
       plt.rcParams['font.sans-serif'] = ['WenQuanYi Micro Hei', 'Noto Sans CJK SC', 'DejaVu Sans']
   plt.rcParams['axes.unicode_minus'] = False
   ```
   或者直接使用通用设置（推荐，兼容性更好）：
   ```python
   plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'PingFang SC', 'WenQuanYi Micro Hei', 'DejaVu Sans']
   plt.rcParams['axes.unicode_minus'] = False
   ```
5. **数据变量名**：使用 `df` 作为 DataFrame 变量名
   **重要**：数据已经在 `df` 变量中，**不要**使用 `pd.read_csv()` 或 `pd.read_excel()` 等函数加载文件
6. **输出路径**：使用变量 `output_path` 保存图片（不要硬编码路径）
7. **图形尺寸**：默认 (8, 5)，可根据需要调整
8. **代码风格**：清晰、有注释，便于理解和修改

## 输出格式：
只输出 Python 代码，不要包含任何解释文字、markdown 代码块标记或其他内容。代码应该可以直接执行。

## 开始生成代码："""
        
        return prompt
    
    def generate_code(
        self,
        schema: List[Dict[str, Any]],
        sample_data: List[Dict[str, Any]],
        intent: str,
    ) -> Dict[str, Any]:
        """
        生成 Matplotlib 代码
        
        Returns:
            {
                'code': str,  # 生成的代码
                'error': Optional[str],  # 错误信息
                'warnings': List[str]  # 警告信息
            }
        """
        prompt = self.build_prompt(schema, sample_data, intent)
        
        try:
            if self.model_type == "openai":
                code = self._call_openai(prompt)
            elif self.model_type == "qwen":
                code = self._call_qwen(prompt)
            elif self.model_type == "ollama":
                code = self._call_ollama(prompt)
            else:
                return {
                    "code": "",
                    "error": f"不支持的模型类型: {self.model_type}",
                    "warnings": [],
                }
            
            # 清理代码（移除 markdown 代码块标记）
            code = self._clean_code(code)
            
            # 安全检查
            warnings = self.guardrails_check(code)
            
            return {
                "code": code,
                "error": None,
                "warnings": warnings,
            }
        except Exception as e:
            return {
                "code": "",
                "error": f"代码生成失败: {str(e)}",
                "warnings": [],
            }
    
    def _call_openai(self, prompt: str) -> str:
        """调用 OpenAI API"""
        if openai is None:
            raise ImportError("需要安装 openai 库: pip install openai")
        
        if not self.api_key:
            raise ValueError("未设置 OPENAI_API_KEY")
        
        client = openai.OpenAI(api_key=self.api_key)
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # 使用较便宜的模型
            messages=[
                {
                    "role": "system",
                    "content": "你是一个专业的 Python 数据可视化工程师。只输出可执行的 Python 代码，不要包含任何解释。",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
            max_tokens=2000,
        )
        
        return response.choices[0].message.content.strip()
    
    def _call_qwen(self, prompt: str) -> str:
        """调用 Qwen API（示例，需要根据实际 API 调整）"""
        if not self.api_key:
            raise ValueError("未设置 QWEN_API_KEY")
        
        # TODO: 实现 Qwen API 调用
        # 这里需要根据 Qwen 的实际 API 格式来实现
        raise NotImplementedError("Qwen API 暂未实现，请使用 OpenAI 或 Ollama")
    
    @staticmethod
    def get_ollama_models(ollama_base_url: Optional[str] = None) -> List[str]:
        """
        从 Ollama 服务获取可用模型列表
        
        Args:
            ollama_base_url: Ollama API 基础 URL（例如 http://localhost:11434）
        
        Returns:
            模型名称列表
        """
        try:
            import requests
        except ImportError:
            return []
        
        base_url = ollama_base_url or os.getenv("OLLAMA_API_BASE_URL", "http://localhost:11434")
        # 清理 URL，确保格式正确
        if base_url.endswith("/api/generate"):
            base_url = base_url.replace("/api/generate", "")
        if not base_url.startswith("http"):
            base_url = f"http://{base_url}"
        
        tags_url = f"{base_url}/api/tags"
        
        try:
            response = requests.get(tags_url, timeout=5)
            response.raise_for_status()
            models_data = response.json()
            models = [model['name'] for model in models_data.get('models', [])]
            return models
        except requests.exceptions.ConnectionError:
            return []
        except requests.exceptions.RequestException:
            return []
        except Exception:
            return []
    
    def _call_ollama(self, prompt: str) -> str:
        """调用本地 Ollama"""
        try:
            import requests
        except ImportError:
            raise ImportError("需要安装 requests 库来使用 Ollama")
        
        ollama_base_url = os.getenv("OLLAMA_API_BASE_URL", "http://localhost:11434")
        # 清理 URL
        if ollama_base_url.endswith("/api/generate"):
            ollama_base_url = ollama_base_url.replace("/api/generate", "")
        if not ollama_base_url.startswith("http"):
            ollama_base_url = f"http://{ollama_base_url}"
        
        url = f"{ollama_base_url}/api/generate"
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False,
        }
        
        response = requests.post(url, json=payload, timeout=60)
        response.raise_for_status()
        result = response.json()
        
        return result.get("response", "").strip()
    
    def _clean_code(self, code: str) -> str:
        """清理生成的代码，移除 markdown 标记、思考部分等"""
        import re
        
        # 移除 markdown 代码块标记
        if code.startswith("```python"):
            code = code[9:]
        elif code.startswith("```"):
            code = code[3:]
        
        if code.endswith("```"):
            code = code[:-3]
        
        code = code.strip()
        
        # 移除思考/推理部分（常见格式）
        # 移除 <think>...</think>（不区分大小写）
        code = re.sub(r'<think>.*?</think>', '', code, flags=re.DOTALL | re.IGNORECASE)
        # 移除 <reasoning>...</reasoning>
        code = re.sub(r'<reasoning>.*?</reasoning>', '', code, flags=re.DOTALL | re.IGNORECASE)
        # 移除 <think>...</think>
        code = re.sub(r'<think>.*?</think>', '', code, flags=re.DOTALL | re.IGNORECASE)
        # 移除 <!-- ... --> 格式的思考
        code = re.sub(r'<!--.*?-->', '', code, flags=re.DOTALL)
        # 移除 [思考] 或 [reasoning] 等标记
        code = re.sub(r'\[思考\].*?\[/思考\]', '', code, flags=re.DOTALL)
        code = re.sub(r'\[reasoning\].*?\[/reasoning\]', '', code, flags=re.DOTALL)
        # 移除单行的思考标记（没有闭合标签的情况）
        code = re.sub(r'<think>.*', '', code, flags=re.IGNORECASE)
        code = re.sub(r'<reasoning>.*', '', code, flags=re.IGNORECASE)
        
        # 移除包含思考内容的长注释行（通常包含中文思考过程）
        # 匹配类似 "好的，我需要..." 这样的中文思考注释
        lines = code.split('\n')
        cleaned_lines = []
        in_thinking_block = False
        
        for line in lines:
            line_stripped = line.strip()
            
            # 跳过空行
            if not line_stripped:
                if not in_thinking_block:
                    cleaned_lines.append(line)
                continue
            
            # 检测思考标记的开始（不区分大小写）
            thinking_start_markers = ['<think>', '<reasoning>', '<think>', '[思考]', '[reasoning]']
            if any(marker.lower() in line.lower() for marker in thinking_start_markers):
                in_thinking_block = True
                continue
            
            # 检测思考标记的结束（不区分大小写）
            thinking_end_markers = ['</think>', '</reasoning>', '</think>', '[/思考]', '[/reasoning]']
            if any(marker.lower() in line.lower() for marker in thinking_end_markers):
                in_thinking_block = False
                continue
            
            # 如果在思考块中，跳过
            if in_thinking_block:
                continue
            
            # 移除包含思考内容的注释行
            # 检测包含中文思考关键词的注释
            if line_stripped.startswith('#'):
                thinking_keywords = [
                    '好的，我需要', '首先，', '接下来，', '然后，', '最后，',
                    '我需要', '我应该', '让我', '首先我得', '首先，我得',
                    'redacted', 'reasoning', 'thinking'
                ]
                if any(keyword in line for keyword in thinking_keywords):
                    continue
            
            # 跳过文件加载相关的行
            file_loading_keywords = [
                'pd.read_csv', 'pd.read_excel', 'pd.read_table',
                'read_csv', 'read_excel', 'read_table',
                'pandas.read_csv', 'pandas.read_excel',
            ]
            
            has_file_loading = any(keyword in line for keyword in file_loading_keywords)
            if has_file_loading:
                continue
            
            cleaned_lines.append(line)
        
        code = '\n'.join(cleaned_lines)
        
        # 再次清理：移除多余的空行（连续3个以上空行变成2个）
        code = re.sub(r'\n{3,}', '\n\n', code)
        
        return code.strip()
    
    def guardrails_check(self, code: str) -> List[str]:
        """
        代码安全检查
        
        Returns:
            警告列表
        """
        warnings = []
        
        # 禁止的函数/方法
        banned_patterns = [
            ("plt.show()", "禁止使用 plt.show()，会弹出窗口"),
            ("os.remove(", "禁止删除文件"),
            ("os.system(", "禁止执行系统命令"),
            ("subprocess.", "禁止使用 subprocess"),
            ("__import__", "禁止动态导入"),
            ("eval(", "禁止使用 eval"),
            ("exec(", "禁止使用 exec（除了我们的安全执行环境）"),
            ("open(", "禁止直接打开文件（应使用 output_path 变量）"),
        ]
        
        # 检查是否尝试加载文件
        file_loading_patterns = [
            ("pd.read_csv", "检测到文件加载语句，数据已在 df 变量中，请移除"),
            ("pd.read_excel", "检测到文件加载语句，数据已在 df 变量中，请移除"),
            ("read_csv", "检测到文件加载语句，数据已在 df 变量中，请移除"),
            ("read_excel", "检测到文件加载语句，数据已在 df 变量中，请移除"),
        ]
        
        for pattern, message in file_loading_patterns:
            if pattern in code:
                warnings.append(f"⚠️ {message}")
        
        for pattern, message in banned_patterns:
            if pattern in code:
                warnings.append(f"⚠️ {message}")
        
        # 检查是否生成了 fig 和 ax
        if "fig, ax" not in code and "fig = plt.figure()" not in code:
            warnings.append("⚠️ 代码中可能缺少 fig 和 ax 变量的定义")
        
        # 检查是否使用了 df
        if "df" not in code:
            warnings.append("⚠️ 代码中未使用 df 变量，可能无法正确访问数据")
        
        return warnings
    
    def generate_chart_suggestions(
        self,
        schema: List[Dict[str, Any]],
        sample_data: List[Dict[str, Any]],
        max_suggestions: int = 5,
    ) -> Dict[str, Any]:
        """
        使用 AI 生成图表推荐建议
        
        Args:
            schema: 数据模式
            sample_data: 样例数据（实际数据行）
            max_suggestions: 最大推荐数量
        
        Returns:
            {
                'suggestions': List[Dict],  # 推荐列表，每个包含 description, intent, reason
                'error': Optional[str]
            }
        """
        # 格式化列信息
        columns_info = []
        for col in schema:
            col_str = f"- {col['name']} ({col['dtype']})"
            if col.get("n_missing", 0) > 0:
                col_str += f", 缺失值: {col['n_missing']} ({col.get('missing_pct', 0):.1f}%)"
            # 添加统计信息
            if col['dtype'] == 'numeric' and 'stats' in col:
                stats = col['stats']
                if stats.get('mean') is not None:
                    col_str += f", 平均值: {stats['mean']:.2f}"
            elif col['dtype'] == 'categorical' and 'n_unique' in col:
                col_str += f", 唯一值数量: {col['n_unique']}"
            columns_info.append(col_str)
        
        columns_text = "\n".join(columns_info)
        
        # 格式化实际数据样本（显示更多行，让 AI 能看到数据模式）
        sample_text = ""
        if sample_data:
            # 显示前 10 行数据，让 AI 能够理解数据的实际内容和模式
            sample_rows = sample_data[:10]
            
            # 创建表格格式的数据展示
            sample_lines = []
            sample_lines.append("实际数据样本（前 10 行）：")
            sample_lines.append("")
            
            # 表头
            if sample_rows:
                headers = list(sample_rows[0].keys())
                header_line = " | ".join([f"{h:15}" for h in headers])
                sample_lines.append(header_line)
                sample_lines.append("-" * len(header_line))
                
                # 数据行
                for row in sample_rows:
                    row_values = []
                    for h in headers:
                        value = row.get(h, '')
                        # 限制值长度，避免过长
                        str_value = str(value)
                        if len(str_value) > 20:
                            str_value = str_value[:17] + "..."
                        row_values.append(f"{str_value:15}")
                    sample_lines.append(" | ".join(row_values))
            
            sample_text = "\n".join(sample_lines)
        
        prompt = f"""你是一个数据可视化专家。请仔细分析以下实际数据，根据数据的真实内容和模式，推荐 {max_suggestions} 个最适合的图表类型。

## 数据字段信息：
{columns_text}

## {sample_text}

## 重要要求：
1. **必须根据实际数据值进行分析**，不要只看字段类型
2. 观察数据中的实际值、范围、分布模式
3. 识别数据中的关系、趋势、类别等特征
4. 每个推荐必须基于实际数据内容，包含具体的列名和数据特征
5. 推荐应该具体且可执行，包含：
   - 图表类型描述（如：时间序列折线图、分组条形图等）
   - 具体的自然语言绘图指令（用户可以直接使用，必须包含实际的列名）
   - 推荐理由（说明为什么这个图表适合这些实际数据）

## 输出格式：
输出 JSON 数组，每个元素包含：
- "description": 图表类型描述
- "intent": 具体的自然语言绘图指令（必须使用实际的列名，可以直接用于生成图表）
- "reason": 推荐理由（说明基于实际数据的哪些特征做出推荐）

## 输出示例：
```json
[
  {{
    "description": "时间序列折线图",
    "intent": "画一个按date列展示sales列的折线图，添加网格线和标题'销售额趋势'",
    "reason": "数据包含date列（日期）和sales列（数值），前10行数据显示销售额随时间变化，适合展示时间趋势"
  }},
  {{
    "description": "分组条形图",
    "intent": "画一个按category列分组的sales列条形图，横向显示，添加图例",
    "reason": "数据包含category分类列和sales数值列，可以对比不同类别的销售额分布"
  }}
]
```

**注意**：intent 中的列名必须使用数据中实际存在的列名，不要使用占位符。

只输出 JSON 数组，不要包含其他文字或 markdown 标记。"""
        
        try:
            if self.model_type == "openai":
                response = self._call_openai(prompt)
            elif self.model_type == "ollama":
                response = self._call_ollama(prompt)
            else:
                return {
                    "suggestions": [],
                    "error": f"不支持的模型类型: {self.model_type}",
                }
            
            # 清理响应，提取 JSON
            response = response.strip()
            # 移除 markdown 代码块标记
            if response.startswith("```json"):
                response = response[7:]
            elif response.startswith("```"):
                response = response[3:]
            if response.endswith("```"):
                response = response[:-3]
            response = response.strip()
            
            # 解析 JSON
            import json
            suggestions = json.loads(response)
            
            # 确保是列表格式
            if not isinstance(suggestions, list):
                suggestions = [suggestions]
            
            # 限制数量
            suggestions = suggestions[:max_suggestions]
            
            return {
                "suggestions": suggestions,
                "error": None,
            }
        except json.JSONDecodeError as e:
            return {
                "suggestions": [],
                "error": f"解析 AI 推荐失败: {str(e)}",
            }
        except Exception as e:
            return {
                "suggestions": [],
                "error": f"生成推荐失败: {str(e)}",
            }
    
    def enhance_query(
        self,
        query: str,
        schema: List[Dict[str, Any]],
        sample_data: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        增强用户查询，提供建议补充和意图分析
        
        Args:
            query: 用户原始查询
            schema: 数据模式
            sample_data: 样例数据
        
        Returns:
            {
                'enhanced_query': str,  # 增强后的查询
                'suggestions': List[str],  # 建议补充列表
                'intent_analysis': str,  # 意图分析
                'key_concepts': List[str],  # 关键概念
                'confidence': float,  # 置信度
                'error': Optional[str]
            }
        """
        # 格式化列信息
        columns_info = []
        for col in schema:
            col_str = f"- {col['name']} ({col['dtype']})"
            columns_info.append(col_str)
        columns_text = "\n".join(columns_info)
        
        # 格式化样例数据（前 5 行）
        sample_text = ""
        if sample_data:
            sample_rows = sample_data[:5]
            sample_lines = []
            if sample_rows:
                headers = list(sample_rows[0].keys())
                for row in sample_rows:
                    row_str = " | ".join([f"{h}: {row.get(h, '')}" for h in headers[:5]])  # 限制列数
                    sample_lines.append(row_str)
            sample_text = "\n".join(sample_lines[:3])  # 只显示前3行
        
        prompt = f"""你是一个数据可视化查询增强专家。分析用户的查询意图，并提供增强建议。

## 用户原始查询：
{query}

## 数据字段信息：
{columns_text}

## 数据样例：
{sample_text}

## 任务：
1. 分析用户的查询意图
2. 生成增强后的查询（更具体、更完整）
3. 提供 3-5 个建议补充（可以添加到查询中的内容）
4. 识别关键概念
5. 评估查询的清晰度（置信度）

## 输出格式（JSON）：
{{
    "enhanced_query": "增强后的完整查询，包含具体列名和详细要求",
    "suggestions": [
        "可以补充的具体内容1",
        "可以补充的具体内容2",
        "可以补充的具体内容3"
    ],
    "intent_analysis": "分析用户的查询意图，说明用户想要什么类型的图表",
    "key_concepts": ["概念1", "概念2", "概念3"],
    "confidence": 0.85
}}

## 要求：
- enhanced_query 必须使用数据中实际存在的列名
- suggestions 应该是具体的、可操作的补充建议
- intent_analysis 要清晰说明用户意图
- key_concepts 提取查询中的关键概念（3-5个）
- confidence 是 0-1 之间的浮点数，表示查询的清晰度

只输出 JSON，不要包含其他文字或 markdown 标记。"""
        
        try:
            if self.model_type == "openai":
                response = self._call_openai(prompt)
            elif self.model_type == "ollama":
                response = self._call_ollama(prompt)
            else:
                return {
                    "enhanced_query": query,
                    "suggestions": [],
                    "intent_analysis": "",
                    "key_concepts": [],
                    "confidence": 0.5,
                    "error": f"不支持的模型类型: {self.model_type}",
                }
            
            # 清理响应，提取 JSON
            response = response.strip()
            if response.startswith("```json"):
                response = response[7:]
            elif response.startswith("```"):
                response = response[3:]
            if response.endswith("```"):
                response = response[:-3]
            response = response.strip()
            
            # 解析 JSON
            import json
            result = json.loads(response)
            
            return {
                "enhanced_query": result.get("enhanced_query", query),
                "suggestions": result.get("suggestions", []),
                "intent_analysis": result.get("intent_analysis", ""),
                "key_concepts": result.get("key_concepts", []),
                "confidence": result.get("confidence", 0.5),
                "error": None,
            }
        except json.JSONDecodeError as e:
            return {
                "enhanced_query": query,
                "suggestions": [],
                "intent_analysis": "",
                "key_concepts": [],
                "confidence": 0.5,
                "error": f"解析增强结果失败: {str(e)}",
            }
        except Exception as e:
            return {
                "enhanced_query": query,
                "suggestions": [],
                "intent_analysis": "",
                "key_concepts": [],
                "confidence": 0.5,
                "error": f"查询增强失败: {str(e)}",
            }

