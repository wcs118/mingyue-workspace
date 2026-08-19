---
name: word-doc
description: 生成格式规范的 Word .docx 文件，含封面、目录、正文章节、页脚
---

使用 python-docx 生成 Word 文档，严格遵循以下规范：

**环境**
- 使用系统 Python（`python` 或 `python3`），不创建 venv
- 依赖：`pip install python-docx`（如未安装则先安装）
- 所有脚本文件显式设置 UTF-8 编码：`# -*- coding: utf-8 -*-`
- PowerShell 中执行前设置：`$OutputEncoding = [System.Text.Encoding]::UTF8`

**文档结构（默认包含）**
1. 封面页：标题（大号加粗）、副标题、日期、制作方
2. 分页符
3. 目录（手动列出章节，标注"目录"标题）
4. 分页符
5. 正文章节：H1 对应一级标题，H2 对应二级标题
6. 页脚：居中显示文档名称和页码

**YAML frontmatter 注意**
- 含冒号的值必须加引号，例如：`title: "项目方案：第一期"`

**输出路径**
- 默认保存到 `./output/<文件名>.docx`
- 若 output 目录不存在则自动创建

**执行后验证**
- 确认文件已生成且大小 > 0
- 输出文件的绝对路径供用户直接打开
