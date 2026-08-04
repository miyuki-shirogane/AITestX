# 查询地点整场景规则。

POST https://solgrid-friend-api.rivtower.cc/api/v1/locations/scene-rule

所属模块: Locations

## 请求体

```json
{
  "locationId": "string"
}
```

字段说明：

- `locationId`: string, 必填, 地点ID。

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
