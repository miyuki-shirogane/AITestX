# 查询当前用户的 Agent 是否在指定地点

POST https://solgrid-friend-api.rivtower.cc/api/v1/locations/user-agent/in-location

所属模块: Locations

## 请求体

```json
{
  "locationId": "string"
}
```

字段说明：

- `locationId`: string, 必填, 地点 ID

## 响应

**200**: Success
```json
{
  "success": true,
  "message": "string",
  "code": 0,
  "errorData": [],
  "data": true
}
```

**400**: Bad Request

**401**: Unauthorized

**403**: Forbidden
