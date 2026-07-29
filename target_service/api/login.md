# 用户登录接口

POST /api/user/login

请求体：
- username: string, 必填, 3-50字符
- password: string, 必填, 6-20字符

响应：
成功: {"code": 0, "data": {"token": "xxx", "user_id": 123}}
失败: {"code": 1001, "msg": "用户名或密码错误"}

API调用方式：
from apis.user.auths_api import AuthsApi
auth = AuthsApi()
resp = auth.login(req_data=req_data, jmes_expression="@")