# GitHub 上传指南

本指南将帮助您将 AutoChartist 项目上传到 GitHub。

## 📋 前置准备

1. **安装 Git**
   - Windows: 下载 [Git for Windows](https://git-scm.com/download/win)
   - macOS: `brew install git` 或从官网下载
   - Linux: `sudo apt-get install git` 或使用包管理器

2. **创建 GitHub 账号**（如果还没有）
   - 访问 [github.com](https://github.com) 注册账号

3. **配置 Git**（首次使用需要）
   ```bash
   git config --global user.name "您的姓名"
   git config --global user.email "您的邮箱"
   ```

## 🚀 上传步骤

### 步骤 1: 在 GitHub 上创建仓库

1. 登录 GitHub
2. 点击右上角的 **"+"** → **"New repository"**
3. 填写仓库信息：
   - **Repository name**: `AutoChartist`（或您喜欢的名称）
   - **Description**: `自然语言生成 Matplotlib 图表工具`
   - **Visibility**: 选择 **Public**（公开）或 **Private**（私有）
   - ⚠️ **不要**勾选 "Initialize this repository with a README"（我们已经有了）
4. 点击 **"Create repository"**

### 步骤 2: 初始化本地 Git 仓库

在项目根目录（`E:\Program\AutoChartist`）打开终端，执行：

```bash
# 初始化 Git 仓库
git init

# 添加所有文件到暂存区
git add .

# 创建首次提交
git commit -m "Initial commit: AutoChartist - 自然语言生成图表工具"
```

### 步骤 3: 连接远程仓库

将本地仓库连接到 GitHub（替换 `YOUR_USERNAME` 为您的 GitHub 用户名）：

```bash
# 添加远程仓库（使用 HTTPS）
git remote add origin https://github.com/YOUR_USERNAME/AutoChartist.git

# 或者使用 SSH（如果您配置了 SSH 密钥）
# git remote add origin git@github.com:YOUR_USERNAME/AutoChartist.git
```

### 步骤 4: 推送代码到 GitHub

```bash
# 将代码推送到 GitHub（首次推送）
git branch -M main
git push -u origin main
```

如果使用 HTTPS，GitHub 会要求您输入用户名和密码（或 Personal Access Token）。

## 🔐 使用 Personal Access Token（推荐）

如果使用 HTTPS 方式，GitHub 现在要求使用 Personal Access Token 而不是密码：

1. **生成 Token**:
   - GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
   - 点击 "Generate new token (classic)"
   - 勾选 `repo` 权限
   - 生成并**复制** token（只显示一次）

2. **使用 Token**:
   - 推送时，用户名输入您的 GitHub 用户名
   - 密码输入刚才生成的 token

## 📝 后续更新代码

当您修改代码后，使用以下命令更新 GitHub：

```bash
# 查看修改的文件
git status

# 添加所有修改
git add .

# 提交修改（使用有意义的提交信息）
git commit -m "描述您的修改，例如：更新 README，添加新功能"

# 推送到 GitHub
git push
```

## 🎯 常用 Git 命令

```bash
# 查看当前状态
git status

# 查看提交历史
git log

# 查看远程仓库
git remote -v

# 拉取远程更新
git pull

# 创建新分支
git checkout -b feature/new-feature

# 切换分支
git checkout main
```

## ⚠️ 注意事项

1. **`.gitignore` 已配置**：以下内容不会被上传：
   - `outputs/` 目录（生成的图表）
   - `__pycache__/` 等 Python 缓存
   - 虚拟环境 `venv/`
   - 临时文件和日志

2. **敏感信息**：
   - 不要上传 API 密钥
   - 不要上传 `config.json`（已在 .gitignore 中）

3. **大文件**：
   - 如果 `logo.png` 或 `screenshot.png` 很大，考虑压缩后再上传

## 🐛 常见问题

### 问题 1: 推送被拒绝
```bash
# 如果远程仓库有 README，先拉取
git pull origin main --allow-unrelated-histories
# 解决冲突后再次推送
git push -u origin main
```

### 问题 2: 忘记添加某些文件
```bash
# 添加遗漏的文件
git add 文件名
git commit -m "添加遗漏的文件"
git push
```

### 问题 3: 想撤销最后一次提交
```bash
# 撤销提交但保留修改
git reset --soft HEAD~1

# 完全撤销提交和修改（谨慎使用）
git reset --hard HEAD~1
```

## 📚 更多资源

- [Git 官方文档](https://git-scm.com/doc)
- [GitHub 帮助文档](https://docs.github.com)
- [Git 教程](https://www.atlassian.com/git/tutorials)

---

**完成！** 您的项目现在应该已经在 GitHub 上了。访问 `https://github.com/YOUR_USERNAME/AutoChartist` 查看您的仓库。

