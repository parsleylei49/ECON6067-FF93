# 提交指南

最终整理日期：**2026年10月9日**。

当前状态：已创建并上传至私有仓库 [parsleylei49/ECON6067-FF93](https://github.com/parsleylei49/ECON6067-FF93)，保留真实Git历史。下方第2、3步已完成，无需重复创建远程仓库。教学团队访问权限及正式课程提交尚待完成。

## 在哪里交？

已于10月9日重新核对[课程期末项目页面](https://yan-xiong-courses.protected-courses.workers.dev/quantitative-tools/project/)：向教学团队提供**可访问的GitHub仓库链接**。仓库须包含报告、复现代码、分析数据、README、可复用工作流及有意义的Git提交历史。

截止时间：**2026年10月18日23:59，香港时间**。

项目网页目前没有明确指定链接应交到哪个Moodle栏目、表单或邮箱；GitHub分享详细指南仍显示“link to be added”。[课程主页](https://yan-xiong-courses.protected-courses.workers.dev/quantitative-tools/portal)列出的教师联系邮箱是 **yanxiong@hku.hk**。这是确认提交渠道的联系地址，不能把它误称为已经明确指定的收作业邮箱。如果Moodle或后续通知另有安排，以教学团队通知为准。

## 怎么交？

1. 阅读 `REPORT.md`，核对姓名、学号、样本限制和附录声明。报告最终整理日期已设为9 October 2026；数据期间、基准版本及真实Git历史没有伪造或改写。
2. 登录你自己的GitHub，创建空仓库，例如 `ECON6067-FF93-3036762812`。建议先设为private；不要让GitHub自动生成README或初始化文件，以免与本地已有历史冲突。
3. 使用本地项目现有Git仓库推送，保留真实提交历史。不要只通过网页拖拽上传最终文件。下方命令中的账号与仓库名需要替换成你实际创建的值。
4. 如果仓库是private，邀请教学团队指定的GitHub账号访问，并确认他们已能打开。不要自行猜测老师的GitHub账号。
5. 按课程平台最新通知提交仓库首页链接；若仍没有通知，联系教师确认具体渠道。提交时写明姓名、学号、论文题目和仓库URL。
6. 保留提交回执或确认邮件。仅创建仓库、上传文件或保存ZIP，不等于已向课程提交。

从当前本地项目目录执行：

```bash
git status
git log --oneline
git remote -v
```

确认没有既存的同名远程仓库后，再执行：

```bash
git remote add origin https://github.com/YOUR_ACCOUNT/YOUR_REPOSITORY.git
git push -u origin main
```

若已有 `origin`，先检查它是否就是你的课程仓库，不要直接覆盖。如果是从ZIP迁移到另一台电脑，可以先从包内 `.bundle` 恢复完整仓库：

```bash
git clone ECON6067-FF93-history.bundle ECON6067-FF93-repository
cd ECON6067-FF93-repository
```

该方式会将bundle路径设置为origin。确认后，将其改成你自己的GitHub地址，再推送：

```bash
git remote set-url origin https://github.com/YOUR_ACCOUNT/YOUR_REPOSITORY.git
git push -u origin main
```

## 可以直接复制的渠道确认邮件

To: yanxiong@hku.hk  
Subject: ECON6067 Final Project — Submission Channel Confirmation — LEI Jinqiu (3036762812)

Dear Professor Xiong,

I have prepared my ECON6067 final project on Fama and French (1993). The project page asks us to share an accessible GitHub repository URL with the teaching team. Could you please confirm whether the link should be submitted by email or through a specific course-platform page? If the repository is private, which GitHub account(s) should I invite?

Thank you.

Best regards,  
Jinqiu Lei  
Student ID: 3036762812  
MEcon

## 交付文件与注意事项

- `REPORT.md`：正式英文报告；附录A包含课程必需的AI使用披露。
- `src/`、`results/`、`figures/`：代码、聚合分析数据和图表。
- `README.md`、`DATA_ACCESS.md`、`WORKFLOW.md`、`requirements.txt`：复现入口、数据访问、工作流和环境。
- `REPORT.html` 与 `report-app/`：可选浏览版本，不替代报告及复现代码；浏览器视觉验收限制见README。
- `.bundle`：保留真实Git历史的备份，不是需要上传到GitHub仓库中的原始数据。

不要上传受限原始CSV、课程密码、受限下载链接、论文PDF或虚拟环境。SMB/HML从2002年7月开始的限制必须保留。课程明确允许AI协助，同时要求披露使用方式、检查和纠错，因此不能删去该必交声明。

已创建私有远程仓库并推送项目；尚未邀请教学团队、代发邮件或正式提交作业。
