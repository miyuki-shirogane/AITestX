# 查询指定地点当前在场且已启用的 NPC 列表。

GET https://solgrid-friend-api.rivtower.cc/api/v1/locations/{locationId}/npcs

所属模块: Npcs

## 请求参数

| 参数名 | 位置 | 类型 | 必填 | 说明 |
|--------|------|------|------|------|
| locationId | path | string | 是 | 需要查询在场 NPC 的地点 ID。 |

## 响应

**200**: Success
```json
{
  "success": true,
  "message": "string",
  "code": 0,
  "errorData": [],
  "data": []
}
```

**401**: Unauthorized

**403**: Forbidden
