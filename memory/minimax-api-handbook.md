# MiniMax API 接入实战手册(2026-08-13 实测打通)

> 状态:✅ 全链路验证通过(文本 + H3 视频生成 + 查询 + 下载)
> 环境:阿里云 Ubuntu 24.04,curl 直连,无需 SDK

## 一、凭据(已存 config/minimax.env,权限600)

| 项 | 值 | 说明 |
|---|---|---|
| API Key | sk-api-...(126字符) | 2026-08-13 用户提供,可用✅ |
| 端点 | https://api.minimaxi.com | **国内端点**(国际 api.minimax.io 报 invalid api key 2049) |
| GroupId | 不需要 | v2 接口不传;旧版 v1 chat 接口才需要(query 参数) |

⚠️ Key 注意:
- 微信传输易截断(出现过 sk-api…GxOA 带省略号),保存时检查长度(应>100字符)
- 旧 key(sk-cp- 前缀)报"TokenPlan 或 Credit 暂不支持 MiniMax-H3"→ 不同账号/额度,别混用

## 二、接口清单(实测有效)

### 1. 文本对话(OpenAI 兼容)
```
POST https://api.minimaxi.com/v1/text/chatcompletion_v2
Header: Authorization: Bearer <key>
Body: {"model":"MiniMax-Text-01","messages":[{"role":"user","content":"hi"}],"max_tokens":20}
```
✅ 实测返回正常回复

### 2. H3 视频生成(核心!)
```
POST https://api.minimaxi.com/v2/video_generation
Header: Authorization: Bearer <key>
Body: {
  "model": "MiniMax-H3",
  "content": [{"type":"text","text":"<prompt>"}],   # ⚠️ 必须是数组,不能是字符串
  "duration": 6,          # 秒
  "resolution": "768p",   # 或 2K
  "ratio": "16:9"         # ⚠️ t2va纯文本场景必须显式指定: 16:9/4:3/1:1/3:4/9:16/21:9
}
```
✅ 实测:6.6s / 768p / 1344x768 / h264+aac 原生音频
返回:`{"task_id":"430235509489929"}`

### 3. 查询任务状态
```
GET https://api.minimaxi.com/v1/query/video_generation?task_id=<task_id>
Header: Authorization: Bearer <key>
```
⚠️ 是 **/v1/query**,不是 /v2!v2 的 query 全是 404
状态:Processing → Success;成功时带 `file_id`

### 4. 获取文件下载地址
```
GET https://api.minimaxi.com/v1/files/retrieve?file_id=<file_id>
Header: Authorization: Bearer <key>
```
返回 `download_url`(OSS 临时链接,带 Expires,约24小时有效)

## 三、错误码速查(实测)

| 现象 | 含义 |
|---|---|
| 401 invalid api key (2049) | Key 无效/端点不对(国际端点) |
| 1004 login fail / token not match group | Key 残缺 或 传了错误 GroupId(v2 不该传) |
| 400 "Mismatch type []*VideoGenContentItem" | content 必须是数组 |
| 400 "t2va 必须显式指定 ratio" | 缺 ratio 参数 |
| 400 "TokenPlan 或 Credit 暂不支持" | 账号额度/套餐不含该模型,需另购视频 Credit |

## 四、踩坑记录(血泪史)
1. **微信发 Key 会截断**:第一次收到 "sk-api…GxOA" 只有13字符,白测两轮。收到先检查长度。
2. **v2 接口不要传 GroupId**:传了错的反而 401/1004,误导以为 Key 配错。
3. **content 数组坑**:官方示例若是字符串会报类型错,必须是 `[{"type":"text","text":"..."}]`。
4. **查询端点是 v1**:任务创建在 v2,查询在 v1/query,文件在 v1/files,三处不统一。
5. **文本套餐 ≠ 视频额度**:文本 TokenPlan 生效不代表 H3 视频能用,视频是独立 Credit。

## 五、可复用脚本
- `scripts/minimax-h3.sh` — 一键文生视频(生成→轮询→下载)
- Key 存放:`config/minimax.env`(chmod 600)
