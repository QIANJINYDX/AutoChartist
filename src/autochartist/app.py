"""Streamlit 主应用：AutoChartist UI"""

import streamlit as st
import pandas as pd
import os
from pathlib import Path
from typing import Optional, Dict, Any
import json
import tempfile
import sys

# 添加当前目录到路径（用于直接运行）
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))

try:
    from autochartist.platform import get_platform, get_shortcuts, get_config_dir
    from autochartist.profiling import profile_df, suggest_chart_types
    from autochartist.codegen import CodeGenerator
    from autochartist.render import CodeRenderer
    from autochartist.exporters import Exporter
except ImportError:
    # 如果作为包导入失败，尝试相对导入
    from .platform import get_platform, get_shortcuts, get_config_dir
    from .profiling import profile_df, suggest_chart_types
    from .codegen import CodeGenerator
    from .render import CodeRenderer
    from .exporters import Exporter


# 页面配置
st.set_page_config(
    page_title="AutoChartist",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 初始化 session state
if "df" not in st.session_state:
    st.session_state.df = None
if "profile" not in st.session_state:
    st.session_state.profile = None
if "generated_code" not in st.session_state:
    st.session_state.generated_code = None
if "chart_image" not in st.session_state:
    st.session_state.chart_image = None
if "data_file_path" not in st.session_state:
    st.session_state.data_file_path = None
if "render_result" not in st.session_state:
    st.session_state.render_result = None
if "ai_suggestions" not in st.session_state:
    st.session_state.ai_suggestions = None
if "ai_suggestions_loading" not in st.session_state:
    st.session_state.ai_suggestions_loading = False
if "show_query_enhancement" not in st.session_state:
    st.session_state.show_query_enhancement = False
if "enhanced_query" not in st.session_state:
    st.session_state.enhanced_query = ""
if "query_suggestions" not in st.session_state:
    st.session_state.query_suggestions = []
if "selected_suggestions" not in st.session_state:
    st.session_state.selected_suggestions = []


def load_data_file(uploaded_file) -> Optional[pd.DataFrame]:
    """加载上传的数据文件"""
    try:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        elif uploaded_file.name.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(uploaded_file)
        else:
            st.error(f"不支持的文件格式: {uploaded_file.name}")
            return None
        
        return df
    except Exception as e:
        st.error(f"加载文件失败: {str(e)}")
        return None


def main():
    """主函数"""
    # 显示 Logo
    logo_path = Path(__file__).parent.parent.parent / "logo.png"
    if logo_path.exists():
        col_logo, col_title, col_shortcut = st.columns([1, 3, 1])
        with col_logo:
            st.image(str(logo_path), width=80)
        with col_title:
            st.title("AutoChartist")
            st.caption("自然语言生成 Matplotlib 图表")
        with col_shortcut:
            shortcuts = get_shortcuts()
            st.caption(f"快捷键: {shortcuts['open']} 打开文件")
    else:
        # 标题栏
        col1, col2 = st.columns([3, 1])
        with col1:
            st.title("📊 AutoChartist")
            st.caption("自然语言生成 Matplotlib 图表")
        
        with col2:
            shortcuts = get_shortcuts()
            st.caption(f"快捷键: {shortcuts['open']} 打开文件")
    
    # 侧边栏
    with st.sidebar:
        st.header("⚙️ 设置")
        
        # Ollama 配置
        st.info("Ollama 需要在本地运行，默认地址: http://localhost:11434")
        
        ollama_base_url = st.text_input(
            "Ollama API 地址",
            value=os.getenv("OLLAMA_API_BASE_URL", "http://localhost:11434"),
            help="Ollama 服务的 API 地址",
        )
        
        # 获取可用模型列表
        if st.button("🔄 刷新模型列表", use_container_width=True):
            st.rerun()
        
        ollama_models = CodeGenerator.get_ollama_models(ollama_base_url)
        
        ollama_model_name = None  # 初始化变量
        if ollama_models:
            # 从 session state 或环境变量获取默认模型
            default_model = st.session_state.get("selected_ollama_model") or os.getenv("OLLAMA_MODEL", ollama_models[0])
            if default_model not in ollama_models:
                default_model = ollama_models[0]
            
            selected_index = ollama_models.index(default_model) if default_model in ollama_models else 0
            
            ollama_model_name = st.selectbox(
                "选择 Ollama 模型",
                options=ollama_models,
                index=selected_index,
                help="选择要使用的 Ollama 模型",
            )
            st.session_state.selected_ollama_model = ollama_model_name
            os.environ["OLLAMA_MODEL"] = ollama_model_name
        else:
            st.warning("⚠️ 无法连接到 Ollama 服务或获取模型列表")
            st.info("请确保：\n1. Ollama 服务正在运行\n2. API 地址正确\n3. 已安装模型（使用 `ollama pull <model>`）")
            
            # 提供手动输入选项
            ollama_model_name = st.text_input(
                "手动输入模型名称",
                value=os.getenv("OLLAMA_MODEL", "llama3.2"),
                help="如果无法自动获取，请手动输入模型名称",
            )
            if ollama_model_name:
                st.session_state.selected_ollama_model = ollama_model_name
                os.environ["OLLAMA_MODEL"] = ollama_model_name
        
        st.divider()
        
        # 文件上传
        st.header("📁 数据文件")
        uploaded_file = st.file_uploader(
            "上传 CSV 或 Excel 文件",
            type=["csv", "xlsx", "xls"],
            help="支持拖拽文件到此处",
        )
        
        if uploaded_file is not None:
            if st.session_state.data_file_path != uploaded_file.name:
                # 新文件，重新加载
                df = load_data_file(uploaded_file)
                if df is not None:
                    st.session_state.df = df
                    st.session_state.data_file_path = uploaded_file.name
                    # 重新分析数据
                    st.session_state.profile = None
                    st.session_state.generated_code = None
                    st.session_state.chart_image = None
                    st.rerun()
    
    # 主内容区
    if st.session_state.df is None:
        # 欢迎页面
        st.info("👈 请在左侧上传数据文件开始使用")
        
        # 显示示例
        st.subheader("📖 使用示例")
        st.code("""
# 示例 1: 时间序列图
"画一个每月销售额的折线图，加上 95% 置信区间"

# 示例 2: 分布图
"展示年龄的直方图，分成 20 个区间"

# 示例 3: 对比图
"画一个按类别分组的销售额条形图，横向显示"

# 示例 4: 散点图
"绘制身高和体重的散点图，用颜色区分性别"
        """)
        return
    
    df = st.session_state.df
    
    # 数据体检
    if st.session_state.profile is None:
        with st.spinner("正在分析数据..."):
            st.session_state.profile = profile_df(df)
    
    profile = st.session_state.profile
    
    # 布局：左侧信息，右侧操作
    col_left, col_right = st.columns([1, 2])
    
    with col_left:
        st.subheader("📋 数据概览")
        
        # 基本信息
        st.metric("行数", f"{profile['rows']:,}")
        st.metric("列数", profile['cols'])
        
        # 字段信息
        st.subheader("字段列表")
        for idx, col_info in enumerate(profile['schema']):
            # 注意：某些 Streamlit 版本不支持 expander 的 key 参数
            with st.expander(f"📌 {col_info['name']} ({col_info['dtype']})"):
                st.write(f"**类型**: {col_info['dtype']}")
                st.write(f"**缺失值**: {col_info['n_missing']} ({col_info['missing_pct']:.1f}%)")
                
                if col_info['dtype'] == 'numeric' and 'stats' in col_info:
                    stats = col_info['stats']
                    st.write("**统计**:")
                    st.write(f"- 最小值: {stats.get('min', 'N/A')}")
                    st.write(f"- 最大值: {stats.get('max', 'N/A')}")
                    st.write(f"- 平均值: {stats.get('mean', 'N/A'):.2f}" if stats.get('mean') else "- 平均值: N/A")
                    st.write(f"- 中位数: {stats.get('median', 'N/A'):.2f}" if stats.get('median') else "- 中位数: N/A")
                
                if col_info['sample']:
                    st.write("**样例值**:")
                    st.write(col_info['sample'][:5])
        
        # 警告信息
        if profile.get('warnings'):
            st.warning("⚠️ 数据警告")
            for idx, warning in enumerate(profile['warnings']):
                st.write(f"- {warning}")
        
        # AI 推荐图表
        st.subheader("🤖 AI 推荐")
        
        # Ollama 始终可用（不需要密钥）
        if ollama_model_name:
            # 显示获取推荐按钮
            if st.button("✨ 获取 AI 智能推荐", use_container_width=True, type="primary"):
                st.session_state.ai_suggestions_loading = True
                st.session_state.ai_suggestions = None
                st.rerun()
            
            # 如果正在加载
            if st.session_state.ai_suggestions_loading:
                with st.spinner("AI 正在分析数据并生成推荐..."):
                    try:
                        generator = CodeGenerator(
                            model_type="ollama",
                            api_key=None,
                            model_name=ollama_model_name
                        )
                        
                        result = generator.generate_chart_suggestions(
                            schema=profile['schema'],
                            sample_data=profile['sample_data'],
                            max_suggestions=5,
                        )
                        
                        if result['error']:
                            st.error(f"❌ {result['error']}")
                            st.session_state.ai_suggestions = None
                        else:
                            st.session_state.ai_suggestions = result['suggestions']
                        
                        st.session_state.ai_suggestions_loading = False
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ 生成推荐失败: {str(e)}")
                        st.session_state.ai_suggestions_loading = False
                        st.session_state.ai_suggestions = None
            
            # 显示 AI 推荐结果
            if st.session_state.ai_suggestions:
                st.success(f"✅ 找到 {len(st.session_state.ai_suggestions)} 个推荐")
                for i, suggestion in enumerate(st.session_state.ai_suggestions):
                    suggestion_desc = suggestion.get('description', f'推荐 {i+1}')
                    # 注意：某些 Streamlit 版本不支持 expander 的 key 参数
                    with st.expander(f"📊 {suggestion_desc}", expanded=False):
                        st.write(f"**推荐理由**: {suggestion.get('reason', '')}")
                        st.write(f"**绘图指令**: {suggestion.get('intent', '')}")
                        
                        # 添加"使用此推荐"按钮
                        if st.button(f"🎯 使用此推荐", key=f"use_suggestion_{i}", use_container_width=True):
                            # 将推荐指令填入输入框
                            st.session_state.suggested_intent = suggestion.get('intent', '')
                            st.rerun()
        else:
            st.info("💡 请先选择 Ollama 模型以获取智能推荐")
            # 显示基础推荐（不使用 AI）
            st.caption("基础推荐（基于字段类型）")
            basic_suggestions = suggest_chart_types(profile['schema'])
            if basic_suggestions:
                for i, suggestion in enumerate(basic_suggestions[:3]):
                    st.info(f"**{suggestion['description']}**\n\n{suggestion['reason']}")
    
    with col_right:
        st.subheader("🎨 生成图表")
        
        # 意图输入（如果从推荐中选择，自动填充）
        default_intent = ""
        if 'suggested_intent' in st.session_state:
            default_intent = st.session_state.suggested_intent
            # 使用后清除，避免下次自动填充
            del st.session_state.suggested_intent
        
        # 查询输入和增强按钮
        col_query, col_enhance = st.columns([4, 1])
        with col_query:
            intent = st.text_area(
                "描述你想要的图表",
                height=100,
                value=default_intent,
                placeholder="例如：画一个每月销售额的折线图，加上 95% 置信区间",
                help="用自然语言描述你想要生成的图表",
                key="intent_input",
            )
        with col_enhance:
            st.write("")  # 占位，对齐
            st.write("")  # 占位，对齐
            if st.button("✨ 查询增强", use_container_width=True, help="使用 AI 增强您的查询"):
                if intent.strip():
                    st.session_state.show_query_enhancement = True
                    st.session_state.enhanced_query = intent
                    st.session_state.query_suggestions = []
                    st.session_state.selected_suggestions = []
                else:
                    st.warning("请先输入查询内容")
        
        col_gen, col_clear = st.columns([3, 1])
        with col_gen:
            generate_button = st.button("🚀 生成图表", type="primary", use_container_width=True)
        with col_clear:
            if st.button("🗑️ 清除", use_container_width=True):
                st.session_state.generated_code = None
                st.session_state.chart_image = None
                st.session_state.render_result = None
                # 清除 SVG 和 PDF 缓存
                keys_to_remove = [k for k in st.session_state.keys() if k.startswith('svg_') or k.startswith('pdf_')]
                for k in keys_to_remove:
                    del st.session_state[k]
                st.rerun()
        
        # 查询增强弹窗（使用容器确保只渲染一次）
        if st.session_state.show_query_enhancement:
            st.markdown("---")
            enhancement_container = st.container()
            with enhancement_container:
                st.subheader("✨ 查询增强")
                
                # 检查是否已选择模型
                if not ollama_model_name:
                    st.error("请先选择 Ollama 模型以使用查询增强功能")
                    if st.button("关闭", key="close_enhancement_no_key"):
                        st.session_state.show_query_enhancement = False
                        st.rerun()
                else:
                    # 如果还没有生成增强结果，则生成
                    if not st.session_state.query_suggestions and intent.strip():
                        with st.spinner("正在分析查询并生成增强建议..."):
                            try:
                                generator = CodeGenerator(
                                    model_type="ollama",
                                    api_key=None,
                                    model_name=ollama_model_name
                                )
                                
                                result = generator.enhance_query(
                                    query=intent,
                                    schema=profile['schema'],
                                    sample_data=profile['sample_data'],
                                )
                                
                                if result['error']:
                                    st.error(f"❌ {result['error']}")
                                else:
                                    st.session_state.enhanced_query = result['enhanced_query']
                                    st.session_state.query_suggestions = result['suggestions']
                                    st.session_state.intent_analysis = result.get('intent_analysis', '')
                                    st.session_state.key_concepts = result.get('key_concepts', [])
                                    st.session_state.confidence = result.get('confidence', 0.5)
                                
                                st.rerun()
                            except Exception as e:
                                st.error(f"❌ 查询增强失败: {str(e)}")
                    
                    # 显示增强界面（使用容器包装，避免重复渲染）
                    enhancement_cols = st.columns([1, 1])
                    
                    with enhancement_cols[0]:
                        st.markdown("#### 增强后的查询")
                        enhanced_query_edit = st.text_area(
                            "编辑增强后的查询",
                            value=st.session_state.enhanced_query,
                            height=100,
                            key="enhanced_query_edit",
                            label_visibility="collapsed",
                        )
                        # 只在值改变时更新
                        if enhanced_query_edit != st.session_state.enhanced_query:
                            st.session_state.enhanced_query = enhanced_query_edit
                        
                        # 意图分析
                        if hasattr(st.session_state, 'intent_analysis') and st.session_state.intent_analysis:
                            st.markdown("#### 意图分析")
                            st.info(st.session_state.intent_analysis)
                        
                        # 关键概念
                        if hasattr(st.session_state, 'key_concepts') and st.session_state.key_concepts:
                            st.markdown("#### 关键概念")
                            concepts_text = " ".join([f"`{c}`" for c in st.session_state.key_concepts])
                            st.markdown(concepts_text)
                        
                        # 置信度
                        if hasattr(st.session_state, 'confidence'):
                            st.markdown("#### 置信度")
                            confidence = st.session_state.confidence
                            st.progress(confidence, text=f"{int(confidence * 100)}%")
                    
                    with enhancement_cols[1]:
                        st.markdown("#### 最终查询预览")
                        final_query = st.text_area(
                            "最终查询",
                            value=st.session_state.enhanced_query,
                            height=150,
                            key="final_query_preview",
                            label_visibility="collapsed",
                        )
                        # 只在值改变时更新
                        if final_query != st.session_state.enhanced_query:
                            st.session_state.enhanced_query = final_query
                    
                    # 底部按钮
                    button_cols = st.columns([1, 1])
                    with button_cols[0]:
                        if st.button("取消", use_container_width=True, key="cancel_enhancement"):
                            st.session_state.show_query_enhancement = False
                            st.rerun()
                    with button_cols[1]:
                        if st.button("应用增强结果", type="primary", use_container_width=True, key="apply_enhancement"):
                            # 将增强后的查询应用到输入框
                            st.session_state.suggested_intent = st.session_state.enhanced_query
                            st.session_state.show_query_enhancement = False
                            st.rerun()
        
        # 生成代码和图表
        if generate_button and intent:
            if not ollama_model_name:
                st.error("请先选择或输入 Ollama 模型名称")
            else:
                with st.spinner("正在生成代码..."):
                    # 初始化代码生成器
                    generator = CodeGenerator(
                        model_type="ollama",
                        api_key=None,
                        model_name=ollama_model_name
                    )
                    
                    # 生成代码
                    result = generator.generate_code(
                        schema=profile['schema'],
                        sample_data=profile['sample_data'],
                        intent=intent,
                    )
                    
                    if result['error']:
                        st.error(f"❌ 生成失败: {result['error']}")
                    else:
                        st.session_state.generated_code = result['code']
                        
                        # 显示警告
                        if result['warnings']:
                            for warning in result['warnings']:
                                st.warning(warning)
                        
                        # 渲染图表
                        with st.spinner("正在渲染图表..."):
                            renderer = CodeRenderer()
                            render_result = renderer.render_code(
                                code=result['code'],
                                df=df,
                                output_format="png",
                                dpi=200,
                            )
                            
                            st.session_state.render_result = render_result
                            
                            if render_result['success']:
                                st.session_state.chart_image = render_result['output_path']
                                
                                # 显示警告
                                if render_result['warnings']:
                                    for warning in render_result['warnings']:
                                        st.warning(warning)
                            else:
                                st.error(f"❌ 渲染失败: {render_result['error']}")
                                if 'error_traceback' in render_result:
                                    with st.expander("查看错误详情"):
                                        st.code(render_result['error_traceback'])
        
        # 显示结果
        if st.session_state.chart_image and Path(st.session_state.chart_image).exists():
            st.subheader("📊 图表预览")
            st.image(st.session_state.chart_image, use_container_width=True)
        
        # 代码和导出
        if st.session_state.generated_code:
            st.subheader("💻 生成的代码")
            
            tab_preview, tab_code = st.tabs(["预览", "代码"])
            
            with tab_preview:
                if st.session_state.chart_image and Path(st.session_state.chart_image).exists():
                    st.image(st.session_state.chart_image, use_container_width=True)
            
            with tab_code:
                st.code(st.session_state.generated_code, language="python")
                
                # 代码编辑（可选）
                edited_code = st.text_area(
                    "编辑代码（可选）",
                    value=st.session_state.generated_code,
                    height=300,
                    key="code_editor",
                )
                
                if st.button("🔄 重新渲染", key="rerender"):
                    renderer = CodeRenderer()
                    render_result = renderer.render_code(
                        code=edited_code,
                        df=df,
                        output_format="png",
                        dpi=200,
                    )
                    
                    if render_result['success']:
                        st.session_state.chart_image = render_result['output_path']
                        st.session_state.generated_code = edited_code
                        st.success("✅ 重新渲染成功！")
                        st.rerun()
                    else:
                        st.error(f"❌ 渲染失败: {render_result['error']}")
            
            # 导出选项
            st.subheader("💾 导出")
            
            col_png, col_svg, col_pdf, col_py, col_nb = st.columns(5)
            
            exporter = Exporter()
            
            # PNG 导出
            with col_png:
                if st.session_state.chart_image and Path(st.session_state.chart_image).exists():
                    with open(st.session_state.chart_image, "rb") as f:
                        st.download_button(
                            "📷 下载 PNG",
                            f.read(),
                            file_name="chart.png",
                            mime="image/png",
                            use_container_width=True,
                        )
            
            # SVG 导出
            with col_svg:
                if st.session_state.chart_image and Path(st.session_state.chart_image).exists() and st.session_state.generated_code:
                    # 检查是否已有 SVG 缓存
                    svg_key = f"svg_{hash(st.session_state.generated_code)}"
                    if svg_key not in st.session_state:
                        st.session_state[svg_key] = None
                    
                    # 如果还没有生成 SVG，则生成
                    if st.session_state[svg_key] is None:
                        if st.button("📐 生成 SVG", use_container_width=True, key="generate_svg"):
                            with st.spinner("正在生成 SVG..."):
                                renderer = CodeRenderer()
                                svg_result = renderer.render_code(
                                    code=st.session_state.generated_code,
                                    df=df,
                                    output_format="svg",
                                    dpi=200,
                                )
                                
                                if svg_result['success']:
                                    st.session_state[svg_key] = svg_result['output_path']
                                    st.rerun()
                                else:
                                    st.error(f"❌ SVG 生成失败: {svg_result['error']}")
                    else:
                        # 直接提供下载
                        svg_path = st.session_state[svg_key]
                        if Path(svg_path).exists():
                            with open(svg_path, "rb") as f:
                                st.download_button(
                                    "📐 下载 SVG",
                                    f.read(),
                                    file_name="chart.svg",
                                    mime="image/svg+xml",
                                    use_container_width=True,
                                )
                        else:
                            # 文件不存在，清除缓存
                            st.session_state[svg_key] = None
                            st.rerun()
            
            # PDF 导出
            with col_pdf:
                if st.session_state.chart_image and Path(st.session_state.chart_image).exists() and st.session_state.generated_code:
                    # 检查是否已有 PDF 缓存
                    pdf_key = f"pdf_{hash(st.session_state.generated_code)}"
                    if pdf_key not in st.session_state:
                        st.session_state[pdf_key] = None
                    
                    # 如果还没有生成 PDF，则生成
                    if st.session_state[pdf_key] is None:
                        if st.button("📄 生成 PDF", use_container_width=True, key="generate_pdf"):
                            with st.spinner("正在生成 PDF..."):
                                renderer = CodeRenderer()
                                pdf_result = renderer.render_code(
                                    code=st.session_state.generated_code,
                                    df=df,
                                    output_format="pdf",
                                    dpi=300,
                                )
                                
                                if pdf_result['success']:
                                    st.session_state[pdf_key] = pdf_result['output_path']
                                    st.rerun()
                                else:
                                    st.error(f"❌ PDF 生成失败: {pdf_result['error']}")
                    else:
                        # 直接提供下载
                        pdf_path = st.session_state[pdf_key]
                        if Path(pdf_path).exists():
                            with open(pdf_path, "rb") as f:
                                st.download_button(
                                    "📄 下载 PDF",
                                    f.read(),
                                    file_name="chart.pdf",
                                    mime="application/pdf",
                                    use_container_width=True,
                                )
                        else:
                            # 文件不存在，清除缓存
                            st.session_state[pdf_key] = None
                            st.rerun()
            
            with col_py:
                # 导出脚本
                script_path = tempfile.NamedTemporaryFile(
                    delete=False,
                    suffix=".py",
                ).name
                
                result = exporter.export_script(
                    code=st.session_state.generated_code,
                    data_path=st.session_state.data_file_path,
                    target_path=script_path,
                )
                
                if result['success']:
                    with open(script_path, "rb") as f:
                        st.download_button(
                            "🐍 下载 Python 脚本",
                            f.read(),
                            file_name="chart.py",
                            mime="text/x-python",
                            use_container_width=True,
                        )
                else:
                    st.error(result['error'])
            
            with col_nb:
                # 导出 Notebook
                nb_path = tempfile.NamedTemporaryFile(
                    delete=False,
                    suffix=".ipynb",
                ).name
                
                result = exporter.export_notebook(
                    code=st.session_state.generated_code,
                    data_path=st.session_state.data_file_path,
                    target_path=nb_path,
                )
                
                if result['success']:
                    with open(nb_path, "rb") as f:
                        st.download_button(
                            "📓 下载 Notebook",
                            f.read(),
                            file_name="chart.ipynb",
                            mime="application/json",
                            use_container_width=True,
                        )
                else:
                    st.error(result['error'])


if __name__ == "__main__":
    main()

