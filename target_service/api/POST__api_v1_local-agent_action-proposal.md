# 提交当前登录用户的 LocalAgent 行为提案。

POST https://solgrid-friend-api.rivtower.cc/api/v1/local-agent/action-proposal

所属模块: LocalAgents

## 请求体

```json
{
  "locationDecision": "string",
  "targetLocationStableId": "string",
  "movementReason": "string",
  "actionPlan": "string",
  "challenge": "string",
  "draftLog": "string",
  "needTakePhoto": true,
  "takePhotoReason": "string",
  "photoOriginalDescription": "string",
  "sleepDurationHours": 0
}
```

字段说明：

- `locationDecision`: string, 可选, 地点决策。
- `targetLocationStableId`: string, 可选, 目标地点稳定标识。
- `movementReason`: string, 可选, 移动理由。
- `actionPlan`: string, 可选, 动作计划。
- `challenge`: string, 可选, 预期挑战。
- `draftLog`: string, 可选, 草稿日志。
- `needTakePhoto`: boolean, 可选, 是否需要拍照。
- `takePhotoReason`: string, 可选, 拍照原因。
- `photoOriginalDescription`: string, 可选, 照片生成原始描述。
- `sleepDurationHours`: int, 可选, 睡眠时长（小时）；非睡眠传 0，在家睡眠传 1 到 10。

## 响应

**200**: Success
```json
{
  "success": true,
  "message": "string",
  "code": 0,
  "errorData": [],
  "data": "string"
}
```

**401**: Unauthorized

**403**: Forbidden
