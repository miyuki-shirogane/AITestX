# 查询地图地点详情

POST https://solgrid-friend-api.rivtower.cc/api/v1/locations/detail

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
  "data": "string"
}
```

**400**: Bad Request

**401**: Unauthorized

**403**: Forbidden
