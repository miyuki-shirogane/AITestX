# 创建用户AI搭档

POST https://solgrid-friend-api.rivtower.cc/api/v1/user-agent/create

所属模块: UserAgents

## 请求体

```json
{
  "nickname": "string",
  "userCallName": "string",
  "species": "string",
  "personalityCode": "string",
  "personalityDescription": "string",
  "birthDate": "string"
}
```

字段说明：

- `nickname`: string, 必填, AI搭档昵称
- `userCallName`: string, 必填, AI搭档如何称呼用户
- `species`: object, 可选, 形象物种：0未知、1柴犬、2鳄鱼、3大象、4猩猩、5兔子、6大熊猫、7橘猫、8土拨鼠、9鸭子、10考拉
- `personalityCode`: string, 必填, 性格代码，例如 INFJ
- `personalityDescription`: string, 必填, 性格描述
- `birthDate`: string, 必填, 出生日期

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
