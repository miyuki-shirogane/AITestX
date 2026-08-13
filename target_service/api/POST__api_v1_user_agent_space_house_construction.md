# 为当前登录用户开始一次房屋施工。

POST https://solgrid-friend-api.rivtower.cc/api/v1/user-agent/space/house-construction

所属模块: Spaces

## 请求体

```json
{
  "designId": "string",
  "presetAssetId": "string",
  "layoutJson": "string"
}
```

字段说明：

- `designId`: string, 可选, 自定义房屋设计 ID；使用预设房屋素材时为空。
- `presetAssetId`: string, 可选, 预设房屋素材 ID；使用自定义房屋设计时为空。
- `layoutJson`: string, 必填, 完整房屋布局 JSON，包含目标设计、地块位置和镜像等信息。

## 响应

**200**: Success
```json
{
  "success": true,
  "message": "string",
  "code": 0,
  "errorData": [],
  "data": {
    "constructionId": "string",
    "status": 1,
    "expectedCompletedAt": "string",
    "constructionCost": 0,
    "economyBalance": 0
  }
}
```

**400**: Bad Request

**401**: Unauthorized

**403**: Forbidden
