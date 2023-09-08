# 常用工具包
## version 1.3.0
### updates
1. 新增common_utils.pdf.create_pdf模块，用于创建并写入pdf文档
   + 支持header和footer设置
   + 支持页边距和页面行数设置
2. common_utils/pdf/fonts目录中增加华文字体， 用于支持中文字符写入pdf文档


## version 1.2.9 
### updates
1. 新增common_utils.convert.translation模块，用于处理翻译任务
  + 目前可支持google翻译和有道翻译

**注意**:
1. google翻译需要梯子才能使用
2. 有道翻译(v3)需要设置Cookie，或者使用AES解密方法(v4已实现)
3. 需要安装pycryptodome>=3.18.0用于AES解密


...


## version 1.2

1. 新增haier自动测试功能
  + nlu模块，用于自动化测试use cases
  + parse_log模块，用于日志信息解析，加速问题分析和定位
