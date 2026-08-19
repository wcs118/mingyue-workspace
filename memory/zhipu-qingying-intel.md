# 智谱清影 (Zhipu Qingying) 视频生成情报

## 接入信息 (2026-08-13)
- API Key: 存于 /home/admin/.openclaw/zhipu.key (chmod 600, 格式 {id}.{secret} 共49字符)
- Base URL: https://open.bigmodel.cn
- 鉴权: Authorization: Bearer {完整key}

## 关键端点
- 模型列表: GET /api/paas/v4/models
- 提交视频任务: POST /api/paas/v4/videos/generations
  - body: {"model":"cogvideox-flash","prompt":"...","image_size":"1920x1080","duration":10}
- **查询任务: GET /api/paas/v4/async-result/{task_id}** ⚠️ 注意: /v4/videos/generations/{id} 返回404!
- 任务字段: task_status (PROCESSING/SUCCESS/FAIL), video_result[].url + cover_image_url

## 模型
- cogvideox-flash: 免费档, 生成约10分钟(01:08提交→01:18完成), 1080p
- 视频模型不显示在 /models 列表(该接口只有 glm 系列)

## 踩坑
- 智谱控制台显示的 key 是脱敏的(b32b...87cb), 必须点"复制"按钮拿完整key
- key 被系统消息脱敏时, 用户需重发完整格式 {id}.{secret}
