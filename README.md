# [https://github.com/Yonsm/ZhiBot](https://github.com/Yonsm/ZhiBot)

Uniform Bot Platform for HomeAssistant

通用交互式机器人平台，目前支持天猫精灵、小爱同学、钉钉群机器人。

**安装**：把 `zhibot` 放入 `custom_components`；也支持在 [HACS](https://hacs.xyz/) 中添加自定义库的方式安装。

_提示：如果只用了单个平台，可以把未使用的平台文件删除，如只用了天猫精灵，可以删除掉 `ding.py` 和 `miai.py`。_

**配置**：参见下文。也可以参考 [我的 Home Assistant 配置](https://github.com/Yonsm/.homeassistant) 中 [configuration.yaml](https://github.com/Yonsm/.homeassistant/blob/main/configuration.yaml)

## 零、天猫精灵个人技能机器人（强烈推荐） [genie2bot](https://github.com/Yonsm/ZhiBot/blob/main/custom_components/zhibot/genie2.py)

### 1. Home Assistant 配置

```yaml
zhibot:
  - platform: genie2
    token: XXXXXXXX
    file: !secret zhibot_file（天猫精灵-个人技能-后端服务-编辑-下载认证文件，文件名，不包含.txt）
    text: !secret zhibot_text（认证文件文件内容）
```

配置后，可以进行对话测试：`https://xxx.xxx.xxx:8123/genie2bot?q=打开客厅灯&token=XXXXXXXX`；也可以在浏览器通过以下链接获取相应的预料库和词汇表：

- 对话表达语料库：`https://xxx.xxx.xxx:8123/genie2bot?q=corpus`
- 动作实体词汇表：`https://xxx.xxx.xxx:8123/genie2bot?q=action`
- 位置实体词汇表：`https://xxx.xxx.xxx:8123/genie2bot?q=place`
- 设备实体词汇表：`https://xxx.xxx.xxx:8123/genie2bot?q=device`
- 名称实体词汇表（不用）：`https://xxx.xxx.xxx:8123/genie2bot`

语料库和实体词汇表，在后续的配置后批量导入。

### 2. 天猫精灵技能应用平台配置

登录 [天猫精灵技能应用平台](https://iap.aligenie.com/home)， `创建新技能`  → [个人技能（私域分享）](https://iap.aligenie.com/console/hybird/create?path=newskill&type=personalskill) ，然后按照下面的示意图配置。

![HASS-GENIE1](https://github.com/Yonsm/ZhiBot/blob/main/images/1.jpg)
![HASS-GENIE2](https://github.com/Yonsm/ZhiBot/blob/main/images/2.jpg)
![HASS-GENIE3](https://github.com/Yonsm/ZhiBot/blob/main/images/3.jpg)
![HASS-GENIE4](https://github.com/Yonsm/ZhiBot/blob/main/images/4.jpg)
![HASS-GENIE5](https://github.com/Yonsm/ZhiBot/blob/main/images/5.jpg)
![HASS-GENIE6](https://github.com/Yonsm/ZhiBot/blob/main/images/6.jpg)
![HASS-GENIE7](https://github.com/Yonsm/ZhiBot/blob/main/images/7.jpg)
![HASS-GENIE8](https://github.com/Yonsm/ZhiBot/blob/main/images/8.jpg)


## 一、天猫精灵机器人 [geniebot](https://github.com/Yonsm/ZhiBot/blob/main/custom_components/zhibot/genie.py)

一次性接入 Home Assistant 的大部分设备到天猫精灵，通过天猫精灵语音控制开关设备、查询传感器。无需第三方服务器，直接使用 Home Assistant 作为服务器和 OAuth，链路高效。

### 1. Home Assistant 配置

```yaml
zhibot:
  - platform: genie
```

无需配置 `token`，会修正 HA 的 OAuth 认证方式延长认证有效期（借鉴来的套路，参见 [oauthbot](https://github.com/Yonsm/ZhiBot/blob/main/custom_components/zhibot/__init__.py)，我也没搞明白）。建议配置 `token`，这样不用重写 HA 的 OAuth 认证有效期，此时下文中的 `网关 URL` 将变成 `https://xxx.xxx.xxx:8123//geniebot?token=******`。

### 2. 天猫精灵开放平台设置

#### 1). 添加技能

登录 [天猫精灵开放平台](https://www.aligenie.com)，进入 `设备开发与接入` → `生活物联网平台` → `云云接入` → [技能开发](https://iot.aligenie.com/skill/home) → `添加新技能`。

#### 2). 服务设置

- 网关 URL：`https://xxx.xxx.xxx:8123/geniebot`
- Client ID：`https://open.bot.tmall.com`
- Client Secret：`NA`
- Authorization URL：`https://xxx.xxx.xxx:8123/auth/authorize`
- Access Token URL：`https://xxx.xxx.xxx:8123/auth/token`

#### 3). 授权调试

`内容设置` → `技能发布` → `发布前验证` → `授权调试` → `账户配置`→ 输入 HA 账户密码 → 可看到你的设备列表。

#### 4). 设备解绑

天猫精灵开放平台已升级为 2.0，但新版竟然没有 `设备解绑` 的功能。虽然旧版已无法新增 `智能家居` 技能，但可以解绑设备：`控制台` → `技能应用平台` → [内容&IOT 技能](https://iap.aligenie.com/console/skill/list) → `服务设置` → `测试验证` → `测试已开启` → `设备解绑`。

另外，这里有 [旧版本配置图示](https://github.com/Yonsm/ZhiBot/blob/main/images/HASS-GENIE.png?raw=true)，仅供参考。

### 3. 使用方式

直接通过天猫精灵语音控制 HA 设备，如“天猫精灵，打开客厅灯”，也可以查询传感器，如“天猫精灵，阳台传感器 PM2.5”。

### 4. 名称规范

天猫精灵查询 HA 时，重要的三个参数需符合规范，否则天猫精灵理解不了：

- `zone`：区域名称，如客厅、餐厅等，须符合 [placelist](https://open.bot.tmall.com/oauth/api/placelist) 规范：

```
门口,客厅,卧室,客房,主卧,次卧,书房,餐厅,厨房,洗手间,浴室,阳台,宠物房,老人房,儿童房,婴儿房,保姆房,玄关,一楼,二楼,三楼,四楼,楼梯,走廊,过道,楼上,楼下,影音室,娱乐室,工作间,杂物间,衣帽间,吧台,花园,温室,车库,休息室,办公室,起居室
```

- `deviceName`：设备名称，须符合 [支持品类](https://www.aligenie.com/doc/357554/gxhx67) 或 [aliaslist](https://open.bot.tmall.com/oauth/api/aliaslist) 规范：

```
灯,房灯,吸顶灯,床头灯,床灯,电灯,吊灯,台灯,落地灯,壁灯,挂灯,射灯,筒灯,灯带,灯条,暗藏灯,背景灯,阅读灯,柜灯,衣柜灯,天花灯,路灯,彩灯;空调,空气调节器,挂式空调;风扇,电风扇,落地扇,电扇,台扇,壁扇,顶扇,驱蚊风扇,暖风扇,净化暖风扇,冷风扇,塔扇;空气净化器,空净,空气清洁器;扫地机器人,扫地机,打扫机,自动打扫机;窗帘,窗纱,布帘,纱帘,百叶帘,卷帘;加湿器,空气加湿器,加湿机,空气加湿机;插座,插头,排插单孔单控;暖奶器,热奶器,牛奶,调奶器,温奶器,冲奶机;电热水壶,养生水壶,水壶,养生壶,热水壶,电水壶;豆浆机;烤箱,嵌入式烤箱;电视;净水器,净水器箱型;冰箱,双开门冰箱,冰柜;开关;机顶盒;传感器;热水器,电热水器,燃气热水器;饮水机;摄像头,摄像,摄像机;路由器,路由,智能路由器;电饭煲,电饭锅,饭煲,饭锅;水族箱控制器,智能鱼缸,鱼缸;蒸脸器;取暖器,加热器;料理机;洗衣机,顶开式洗衣机,滚筒洗衣机;微波炉;空气检测仪;除湿机,除湿器;智能床;万能遥控器;香薰机;窗;抽油烟机,抽烟机,烟机;指纹锁;洗碗机,洗碗器;车;浴霸;晾衣机;新风机;壁挂炉;干衣机,干衣器;驱蚊器;跑步机;智能门控,智能门锁,门锁,电子锁;破壁机,超跑;网关;秤;智能手环;电压力锅,压力锅,高压锅;晾衣架,衣架,晒衣架;电热毯;按摩仪;按摩椅;无线按钮;电视盒子,盒子,小米盒子,荣耀盒子,乐视盒子,智能盒子;投影仪,投影机,投影,背投;风扇灯;门磁传感器;人体传感器;灯带;智能猫眼;燃气热水器;面包机;消毒柜;磁炉,电磁炉;补水仪;电动牙刷;灭蚊器;双键开关;三键开关;单火开关;单火双键开关;单火三键开关;榨汁机;调奶器;酒柜;吸奶器;消毒锅;擦窗机;动感单车;走步机;多功能料理锅;吸尘器;电脑;温湿度传感器;四键开关;垃圾处理器;血糖仪;血压仪;智能垃圾桶;取暖桌;划船机;点读笔;猫砂盆;制冰机;电炸锅;按摩贴;烟雾传感器;燃气传感器;水浸传感器;光线传感器;暖菜板;艾灸仪;辅食机;足浴盆;暖宫带
```

- `deviceType`：设备类型，须符合 [支持品类](https://www.aligenie.com/doc/357554/gxhx67) 规范。

会尝试从 HA 配置信息中，根据规则尝试自动转换成天猫精灵匹配的名称和类型。但有些可能匹配不成功，此时可以在 [customize.yaml](https://github.com/Yonsm/.homeassistant/blob/main/customize.yaml) 中，定制天猫精灵能识别的区域、名称和类型，如：

```yaml
genie_zone: 客厅
genie_name: 吸顶灯
genie_type: outlet
```

其中 `genie_zone` 可以配置给单个设备，也可以配置给分组（将应用到分组下的所有设备）。

_**建议**：把设备按上述区域名称分组（如“客厅”），或以上述区域前导设备名称（如“客厅灯”）；设备名符合上述名称规范。这样会自动推测搞定，不用手动配置。_

## 二、小爱同学机器人 [miaibot](https://github.com/Yonsm/ZhiBot/blob/main/custom_components/zhibot/miai.py)

类似天猫精灵，但小爱同学的智能设备使用控制方式需要唤醒词语，实际体验远远没有天猫精灵好。_且需进入测试模式，有效时间短，要频繁重新进入测试模式，不建议使用。_

## 三、钉钉群机器人 [dingbot](https://github.com/Yonsm/ZhiBot/blob/main/custom_components/zhibot/ding.py) 之 `Home Assistant` ⇋ `钉钉群机器人` 双向互动

**钉钉群设置**：在钉钉群里添加自定义机器人，**勾选“是否开启 Outgoing 机制”**。据称此功能在内测，部分用户可能没有没有此选项，佛系或自行解决。

### 1. Home Assistant 配置

```yaml
zhimsg:
  - platform: ding
    name: 钉钉信使
    token: !secret dingbot_token
    secret: !secret dingbot_secret

zhibot:
  - platform: ding
    token: !secret zhibot_token
```

_**依赖**：需依赖 [ZhiMsg](https://github.com/Yonsm/ZhiMsg)，请一并安装好。_
_**注意**：`zhibot` 的 `- platform: ding` 没有配置 `name `。_

### 2. 钉钉群机器人设置

![HASS-DING](https://github.com/Yonsm/ZhiBot/blob/main/images/HASS-DING.png)

### 3. 使用方式

Home Assistant 可以给钉钉群机器人发送消息。也可以在钉钉群里面 @机器人 控制 Home Assistant，输入 `?` 查询使用样例，如下：

```
打开/关闭（设备或群组名）；查询（设备或群组名，可省略“查询”）；触发（自动化，可省略“触发”）
```

## 四、钉钉群机器人 [dingbot](https://github.com/Yonsm/ZhiBot/blob/main/custom_components/zhibot/ding.py) 之 `钉钉群机器人` → `Home Assistant` → `小爱音箱` 单向控制

**钉钉群设置**：在钉钉群里添加自定义机器人，**勾选“是否开启 Outgoing 机制”**。据称此功能在内测，部分用户可能没有没有此选项，佛系或自行解决。

### 1. Home Assistant 配置

```yaml
zhimi:
  username: !secret zhimi_username
  password: !secret zhimi_password

zhimsg:
  - platform: miai
    name: 客厅音箱
    did: 380205692
    model: x08c
  - platform: miai
    name: 过道音箱
    did: 89463074
    model: lx01

zhibot:
  - platform: ding
    name: 客厅音箱
    token: !secret zhibot_token
  - platform: ding
    name: 过道音箱
    token: !secret zhibot_token
```

_**依赖**：需依赖 [ZhiMi](https://github.com/Yonsm/ZhiMi) 和 [ZhiMsg](https://github.com/Yonsm/ZhiMsg)，请一并安装好。_
_**注意**：必须配置 `name`，并和 `ZhiMsg` 的小爱音箱同名。_

### 2. 钉钉群机器人设置

![HASS-MIAI](https://github.com/Yonsm/ZhiBot/blob/main/images/HASS-MIAI.png)

### 3. 使用方式

在钉钉群里面 @小爱音箱 来播报或执行文本。输入 `?` 查询使用样例，如下：

```
您好，我是小爱同学
查询天气
执行关灯
静默关灯
音量40
音量70%大声说您好
```

还可以 `??` 查询更多 MIoT 命令，如下：

```
Get Props: ?<siid[-piid]>[,...]
           ?1,1-2,1-3,1-4,2-1,2-2,3
Set Props: ?<siid[-piid]=[#]value>[,...]
           ?2=#60,2-2=#false,3=test
Do Action: ?<siid[-piid]> <arg1> [...]
           ?5 Hello
           ?5-4 Hello #1

Call MIoT: ?<cmd=prop/get|/prop/set|action> <params>
           ?action {"did":"380205692","siid":5,"aiid":1,"in":["Hello"]}

Call MiIO: ?/<uri> <data>
           ?/home/device_list {"getVirtualModel":false,"getHuamiDevices":1}

Devs List: ?list [name=full|name_keyword] [getVirtualModel=false|true] [getHuamiDevices=0|1]
           ?list Light true 0

MiIO Spec: ?spec [model_keyword|type_urn]
           ?spec
           ?spec speaker
           ?spec xiaomi.wifispeaker.lx04
           ?spec urn:miot-spec-v2:device:speaker:0000A015:xiaomi-lx04:1
```

## 五、参考

- [ZhiMsg](https://github.com/Yonsm/ZhiMsg)
- [Yonsm.NET](https://yonsm.github.io)
- [Hassbian geniebot](https://bbs.hassbian.com/thread-2700-1-1.html)
- [Hassbian miaibot](https://bbs.hassbian.com/thread-4680-1-1.html)
- [Hassbian dingbot](https://bbs.hassbian.com/thread-12348-1-1.html)
- [Hassbian ding2msgbot](https://bbs.hassbian.com/thread-12349-1-1.html)
- [Yonsm's .homeassistant](https://github.com/Yonsm/.homeassistant)
