# ZhiBot

Uniform Bot Platform for HomeAssistant

通用交互式机器人平台，目前支持天猫精灵、小爱同学、钉钉群机器人。

## 1. 安装准备

-   **依赖**：如果需要在钉钉群中控制小爱同学，需要依赖 [ZhiMsg](https://github.com/Yonsm/ZhiMsg)，请一并准备好。

-   **安装**：把 `zhibot` 放入 `custom_components`；也支持在 [HACS](https://hacs.xyz/) 中添加自定义库的方式安装。

## 2. 配置方法

参见[我的 Home Assistant 配置](https://github.com/Yonsm/.homeassistant)中 [configuration.yaml](https://github.com/Yonsm/.homeassistant/blob/main/configuration.yaml)

```
zhibot:
  - platform: genie
  - platform: miai
    token: !secret zhibot_token
  - platform: ding
    token: !secret zhibot_token
  - platform: ding
    name: 客厅音箱
    token: !secret zhibot_token
  - platform: ding
    name: 过道音箱
    token: !secret zhibot_token
  - platform: ding
    name: 儿童房音箱
    token: !secret zhibot_token
```

将分别生成以下 HTTP 子服务：

```
Serving on /geniebot
Serving on /miaibot?token=*****
Serving on /dingbot?token=*****
Serving on /ke_ting_yin_xiang?token=*****
Serving on /guo_dao_yin_xiang?token=*****
Serving on /er_tong_fang_yin_xiang?token=*****
```

以上，使用诸如 `https://xxx.xxx.xxx:8123/geniebot` 的 URL 来配合使用。

特别地，对于 `geniebot`，如果不配置 `token` 则重写 HA 的 OAuth 认证方式（借鉴来的套路，参见 [oauthbot](https://github.com/Yonsm/ZhiBot/blob/main/custom_components/zhibot/__init__.py)，我也没搞明白）；建议配置 `token` 并使用带 `token` 的 URL 避免重写 HA 的 OAuth 认证。

## 3. 使用方式

_提示：如果只用了单个平台，可以把未使用的平台文件删除，如只用了天猫精灵，可以删除掉 `dingbot.py` 和 `miaibot.py`。_

### 钉钉群机器人 [dingbot](https://github.com/Yonsm/ZhiBot/blob/main/custom_components/zhibot/dingbot.py)

交互应答式钉钉群机器人。如果需要配置为控制小爱同学，则依赖 [ZhiMsg](https://github.com/Yonsm/ZhiMsg)；如果只是使用钉钉控制 HA，则不需要。

_更详细的配置步骤待补充_

### 天猫精灵机器人 [geniebot](https://github.com/Yonsm/ZhiBot/blob/main/custom_components/zhibot/geniebot.py)

几乎零配置，一键接入 Home Assistant 的大部分设备到天猫精灵，通过天猫精灵语音控制开关设备、查询传感器。无需第三方服务器，直接使用 Home Assistant 作为服务器和 OAuth，链路更高效。详情参考[瀚思彼岸论坛](https://bbs.hassbian.com/thread-2700-1-1.html)

_更详细的配置步骤待补充_

### 小爱同学机器人 [miaibot](https://github.com/Yonsm/ZhiBot/blob/main/custom_components/zhibot/miaibot.py)

**官方测试模式短时间内会失效，要频繁重新进入测试模式。不建议使用**

类似天猫精灵，但小爱同学的智能设备使用控制方式需要唤醒词语，实际体验远远没有天猫精灵好。详情参考[瀚思彼岸论坛](https://bbs.hassbian.com/thread-4680-1-1.html)

## 4. 参考

-   [ZhiMsg](https://github.com/Yonsm/ZhiMsg)
-   [Yonsm.NET](https://yonsm.github.io)
-   [Yonsm's .homeassistant](https://github.com/Yonsm/.homeassistant)