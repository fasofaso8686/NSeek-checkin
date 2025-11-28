# NSeek-checkin
第1步：Fork 仓库

GitHub 右上角点击 Fork 按钮

第2步：配置 Secrets

进入 Settings → Secrets and variables → Actions

点击 New repository secret

添加以下内容：

必填：ACCOUNTS

json
[
  {"email": "123456@abc.com", "password": "abc123"}
]
可选：TELEGRAM_BOT_TOKEN 和 TELEGRAM_CHAT_ID（用于接收签到通知）

第3步：启用 Actions

进入 Actions 标签

点击 I understand my workflows, go ahead and enable them

点击 Run workflow 测试

第4步：设置为私有仓库

Settings → 下拉到 Danger Zone → Change to private

✨ 核心修复内容
✅ 6种元素定位方式 - 确保找到按钮

✅ 双重点击机制 - 普通+JavaScript备选

✅ 自动滚动定位 - scrollIntoView

✅ 40秒多重等待 - Page Load + WebDriverWait

✅ 分类详细日志 - [初始化][登录][签到][结果]

✅ 完整错误追踪 - traceback打印

⏰ 执行配置
执行时间：每天北京时间 00:05

账号间隔：5 分钟

签到方式：1:5 概率随机选择
