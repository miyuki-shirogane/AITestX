# 查询指定地点内的 Agent 伙伴

POST https://solgrid-friend-api.rivtower.cc/api/v1/locations/agents

所属模块: Locations

## 请求体

```json
{
  "id": "string"
}
```

字段说明：

- `id`: string, 必填, 地点 ID

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

**400**: Bad Request

**401**: Unauthorized

**403**: Forbidden
