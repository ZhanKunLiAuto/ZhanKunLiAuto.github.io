# GitHub Pages 部署指南

本网站已经为 GitHub Pages 部署进行了优化配置。以下是部署步骤：

## 快速部署步骤

### 1. 创建 GitHub 仓库
- 在 GitHub 上创建一个名为 `[username].github.io` 的仓库（其中 `[username]` 是您的 GitHub 用户名）
- 如果您想使用其他仓库名，也可以，但需要在 `_config.yml` 中设置 `baseurl`

### 2. 上传代码
```bash
# 初始化 git（如果还没有的话）
git init

# 添加远程仓库
git remote add origin https://github.com/[username]/[username].github.io.git

# 添加所有文件
git add .

# 提交
git commit -m "Initial commit"

# 推送到 GitHub
git push -u origin main
```

### 3. 启用 GitHub Pages
1. 进入仓库的 Settings
2. 找到 "Pages" 部分
3. 在 "Source" 下选择 "Deploy from a branch"
4. 选择 "main" 分支和 "/ (root)" 文件夹
5. 点击 "Save"

### 4. 等待部署
- GitHub 会自动构建您的 Jekyll 网站
- 通常需要几分钟时间
- 您可以在 Actions 标签页查看构建进度

### 5. 访问网站
- 网站将在 `https://[username].github.io` 上线
- 如果使用了其他仓库名，地址为 `https://[username].github.io/[repository-name]`

## 自定义配置

### 更新个人信息
1. 编辑 `_config.yml` 文件中的基本信息
2. 更新 `_pages/about.md` 中的个人介绍
3. 在 `assets/img/` 中添加您的头像（命名为 `portrait.jpeg`）

### 添加论文
- 编辑 `_bibliography/papers.bib` 文件
- 使用标准的 BibTeX 格式
- 添加 `selected={true}` 标记重要论文

### 添加新闻
- 在 `_news/` 目录下创建新的 `.md` 文件
- 使用现有文件作为模板

## 常见问题

### 网站没有更新？
- 检查 GitHub Actions 是否有错误
- 确保 `_config.yml` 中的 `url` 和 `baseurl` 设置正确
- 清除浏览器缓存后重试

### 样式不正确？
- 确保所有文件都已提交
- 检查 `_sass/` 目录中的文件是否完整
- 确保 Jekyll 版本兼容

### 需要本地预览？
```bash
# 安装依赖
bundle install

# 本地运行
bundle exec jekyll serve

# 访问 http://localhost:4000
```

## 维护更新

定期更新您的：
- 论文列表（`_bibliography/papers.bib`）
- 新闻动态（`_news/`）
- 个人信息（`_pages/about.md`）

祝您使用愉快！如有问题，请参考 Jekyll 和 al-folio 主题的官方文档。