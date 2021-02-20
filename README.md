# ZhiBot
HomeAssistant Component for Bot Platform

通用交互式机器人平台，里面有天猫精灵、小爱同学、钉钉群机器人等。

# [dingbot](custom_components/zhibot/dingbot.py)

交互应答式钉钉群机器人。依赖 [ZhiMsg](https://github.com/Yonsm/ZhiMsg)。

# [geniebot](custom_components/zhibot/geniebot.py)

几乎零配置，一键接入 Home Assistant 的大部分设备到天猫精灵，可以语音控制相关设备开关。详情请参考 [https://bbs.hassbian.com/thread-2700-1-1.html](https://bbs.hassbian.com/thread-2700-1-1.html)

但上述文章是老的实现方式，不适用于此插件。此插件使用姿势更妙，无需第三方服务器，直接使用 Home Assistant 作为服务器和 OAuth，链路更高效。具体可参考网友的帖子 [https://bbs.hassbian.com/thread-4758-1-1.html](https://bbs.hassbian.com/thread-4758-1-1.html)

# [miaibot](custom_components/zhibot/miaibot.py)

`官方测试模式一小时失效，已废弃`。小爱同学的智能设备使用控制方式没有天猫精灵好，需要唤醒词语。详情请参考 [https://bbs.hassbian.com/thread-4680-1-1.html](https://bbs.hassbian.com/thread-4680-1-1.html)
