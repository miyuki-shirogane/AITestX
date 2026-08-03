# 手动创建合影照片生成请求。

POST https://solgrid-friend-api.rivtower.cc/api/v1/user-agent/group-photo/request

所属模块: UserAgents

## 请求体

```json
{
  "ownerAgentId": "string",
  "locationId": "string",
  "participantUserAgentIds": [],
  "participantNpcAgentIds": [],
  "logId": "string",
  "sourceType": "string",
  "sourceId": "string",
  "title": "string",
  "originalDescription": "string"
}
```

字段说明：

- `ownerAgentId`: string, 必填, 发起拍照的AI搭档ID。
- `locationId`: string, 必填, 当前地点ID。
- `participantUserAgentIds`: array[string], 可选, 一起拍照的用户AI搭档ID列表。
- `participantNpcAgentIds`: array[string], 可选, 一起拍照的NPC ID列表。
- `logId`: string, 必填, 关联冒险日志ID。
- `sourceType`: string, 可选, 来源类型，可以为空；为空时命令会归一化为 unknown。
- `sourceId`: string, 可选, 来源记录ID，可以为空；为空时命令会自动生成。
- `title`: string, 可选, 照片展示标题。
- `originalDescription`: string, 必填, 原始描述，默认用于手动测试。

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

**400**: Bad Request

**401**: Unauthorized

**403**: Forbidden
