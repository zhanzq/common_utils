# 常用工具包
## version 1.4.0
### updates
1. 新增**common_utils.text_io.word**模块
   + 支持docx文档的读写操作
   + 支持插入图片
   + 支持读写表格数据, `insert_table(data_lst)`, `extract_table(table_idx)`
   + 支持格式化文本，如字体设置`set_font(run, **args)`等
   + 支持页面设置，`set_page(margin=(3.18, 3.18, 2.54, 2.54), column=1, column_space=0.5)`
   + 支持插入新页面，`add_new_page()`
   + 等等

2. 新增**common_utils.poetry.poetry**模块，用于古诗文处理
   + 继承`common_utils.text_io.word.Docx`
   + 支持添加古诗标题，`add_poetry_title(title)`
   + 支持添加古诗作者，`add_poetry_author(author)`
   + 支持添加古诗正文，`add_poetry_content(content)`
   + 支持添加古诗学习日期，`add_poetry_date(date)`
   + 支持添加整首古诗信息，`add_poetry(poetry_info: dict)`
   + 等等


## version 1.3.2
### updates
1. 新增**common_utils.ner.convert**模块，用于格式化NER任务数据
   
2. 在已有模块**common_utils.text_io.txt**中，新增save_to_txt方法，用于保存list数据
   + 支持保存列表数据到文本文件，如.txt, .tsv等
   + 支持数据末尾自动添加必要的换行符

## version 1.3.1
### updates
1. 新增**common_utils.web.parser**模块，用于web网页的操作
   + 支持文件资源的下载（支持代理设置），download_file
   + 支持网页下载，download_web
   + 支持根据文本内容text查找相关网页元素，get_item_by_text，返回所有相关元素列表
   + 支持根据网页元素抽取相关链接，get_related_links(item, depth=5)，支持深度设置，默认为5
   + 支持根据相关链接抽取对应的\<a\>元素，get_item_by_href(href)
   + 支持根据元素属性抽取所有的链接，get_links_by_attr(**attr)
2. 新增**pdf.read_pdf**模块， 
   + 支持从pdf文件（主要是arxiv论文）中抽取正文
   + 支持正文内容的预处理，如“合并合成词”，“过滤参考文献标记”等

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
