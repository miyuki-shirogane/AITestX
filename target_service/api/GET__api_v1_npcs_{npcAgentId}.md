# 查询指定 NPC 的公开身份、人设、职责和当前运行信息。

GET https://solgrid-friend-api.rivtower.cc/api/v1/npcs/{npcAgentId}

所属模块: Npcs

## 请求参数

| 参数名 | 位置 | 类型 | 必填 | 说明 |
|--------|------|------|------|------|
| npcAgentId | path | string | 是 | 需要查询资料的 NPC ID。 |

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
