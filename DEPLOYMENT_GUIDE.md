# 🚀 个人主页部署指南

## 📋 部署前检查清单

在部署您的新个人主页之前，请确保：

### ✅ 必要文件已准备
- [ ] `_pages/about.md` - 主页内容 ✨
- [ ] `_bibliography/papers.bib` - 论文数据库 ✨
- [ ] `_data/cv.yml` - 个人简历 ✨
- [ ] `_data/socials.yml` - 社交媒体链接 ✨
- [ ] `_config.yml` - 网站配置 ✨
- [ ] `_news/` - 新闻动态文件夹 ✨
- [ ] `_projects/` - 项目展示文件夹 ✨

### 🖼️ 图片资源（待补充）
- [ ] `assets/img/portrait.jpeg` - 个人照片
- [ ] `assets/img/wechat-qr.png` - 微信二维码
- [ ] `assets/img/publication_preview/` - 论文预览图片

## 🌐 GitHub Pages 部署步骤

### 1️⃣ 创建GitHub仓库
```bash
# 确保仓库名为: [您的用户名].github.io
# 例如: ZhanKunLiAuto.github.io
```

### 2️⃣ 上传文件到仓库
```bash
git add .
git commit -m "Initial commit: New personal homepage design"
git push origin main
```

### 3️⃣ 启用GitHub Pages
1. 进入仓库设置页面
2. 滚动到 "Pages" 部分
3. 选择源为 "Deploy from a branch"
4. 选择分支为 "main" 或 "gh-pages"
5. 选择文件夹为 "/" (root)
6. 点击 "Save"

### 4️⃣ 等待构建完成
- 初次部署可能需要5-15分钟
- 后续更新通常在2-5分钟内完成
- 可以在 "Actions" 标签页查看构建状态

## 🔧 个性化定制

### 立即可做的改进
1. **替换个人照片**
   ```bash
   # 将您的照片重命名为 portrait.jpeg 并放入:
   assets/img/portrait.jpeg
   ```

2. **添加微信二维码**
   ```bash
   # 将微信二维码保存为:
   assets/img/wechat-qr.png
   ```

3. **更新社交媒体链接**
   ```yaml
   # 编辑 _data/socials.yml
   github_username: 您的GitHub用户名
   linkedin_username: 您的LinkedIn用户名
   ```

### 论文预览图片
在 `assets/img/publication_preview/` 文件夹中添加论文预览图片：
- `drivevlm2024.png`
- `street_gaussians.png`
- `planagent.png`
- `tod3cap.png`
- 等等...

## 📱 域名配置（可选）

### 使用自定义域名
1. 在仓库根目录创建 `CNAME` 文件
2. 在文件中输入您的域名（如：`kunzhan.ai`）
3. 在域名DNS设置中添加CNAME记录指向 `[用户名].github.io`

### GitHub提供的域名
您的网站将在以下地址可用：
```
https://[您的用户名].github.io
```

## 🔍 SEO优化检查

### 基本SEO已配置
- ✅ 网站标题和描述
- ✅ 元数据标签
- ✅ 结构化数据
- ✅ XML网站地图
- ✅ 响应式设计

### 进一步优化建议
1. **提交到搜索引擎**
   - Google Search Console
   - Bing Webmaster Tools

2. **社交媒体卡片**
   - 确保Open Graph标签正确
   - 测试Twitter卡片显示

## 📊 网站分析（可选）

### 启用Google Analytics
1. 获取Google Analytics ID
2. 在 `_config.yml` 中更新：
   ```yaml
   google_analytics: G-XXXXXXXXXX
   enable_google_analytics: true
   ```

## 🛠️ 维护建议

### 定期更新内容
- **论文**: 及时添加新发表的论文到 `_bibliography/papers.bib`
- **新闻**: 在 `_news/` 中添加最新动态
- **项目**: 更新 `_projects/` 中的研究项目
- **简历**: 定期更新 `_data/cv.yml`

### 监控网站性能
- 使用 Google PageSpeed Insights 检查性能
- 定期检查链接有效性
- 监控网站访问统计

## 🆘 常见问题解决

### 构建失败
1. 检查 Jekyll 语法错误
2. 确认所有必要的插件已安装
3. 查看 GitHub Actions 构建日志

### 图片不显示
1. 确认图片路径正确
2. 检查图片文件大小（建议<5MB）
3. 使用支持的格式（jpg, png, webp）

### 样式问题
1. 清除浏览器缓存
2. 检查CSS语法
3. 确认Bootstrap类名正确

## 📧 技术支持

如需帮助，可以：
1. 查看 [al-folio文档](https://github.com/alshedivat/al-folio)
2. 搜索相关 GitHub Issues
3. 联系技术支持邮箱

---

🎉 **恭喜！您的专业个人主页即将上线！**

这个重新设计的个人主页将有效展示您在自动驾驶领域的专业成就和研究贡献。