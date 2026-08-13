# 为当前登录用户立即应用房间设计。

POST https://solgrid-friend-api.rivtower.cc/api/v1/user-agent/space/room-design

所属模块: Spaces

## 请求体

```json
{
  "roomDesignId": "string",
  "roomPresetAssetId": "string"
}
```

字段说明：

- `roomDesignId`: string, 可选
- `roomPresetAssetId`: string, 可选

## 响应

**200**: Success
```json
{
  "success": true,
  "message": "string",
  "code": 0,
  "errorData": [],
  "data": {
    "currentRoomDesignId": "string",
    "currentRoomPresetAssetId": "string"
  }
}
```

**400**: Bad Request

**401**: Unauthorized

**403**: Forbidden
