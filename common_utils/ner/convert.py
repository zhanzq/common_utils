# encoding=utf-8
# created @2023/11/21
# created by zhanzq
#
import os.path

from common_utils.text_io.txt import load_from_jsonl, save_to_txt


def _get_tag(tag, start, end):
    """
    生成实体对应的tag序列
    :param tag: 实体的tag类别
    :param start: 实体的开始位置
    :param end: 实体的结束位置
    :return: a list, 如["B-floor", "E-floor"]
    """
    length = end - start
    if length == 1:
        return [f"S-{tag}"]
    elif length == 2:
        return [f"B-{tag}", f"E-{tag}"]
    else:
        return [f"B-{tag}"] + [f"I-{tag}"]*(length-2) + [f"E-{tag}"]


def _convert_json_to_ner_format(json_obj):
    text = json_obj["text"]
    entities = json_obj["entities"]
    out = ["O"]*len(text)

    for entity in entities:
        tag = entity["slot-name"]
        start = entity["start-index"]
        end = entity["end-index"]
        out[start:end] = _get_tag(tag=tag, start=start, end=end)

    out = [ch for ch in text] + ["[SEP]"] + out
    out_s = " ".join(out)

    return out_s


def convert_jsonl_to_ner_format(jsonl_data_path, output_data_path):
    """
    将jsonl模式的数据转换为ner训练格式数据
    :param jsonl_data_path:
    :param output_data_path:
    :return:

    示例：
    输入为
    {
        "entities": [
            {"end-index": 2, "slot-name": "floor", "start-index": 0, "value": "1层"},
            {"end-index": 4, "slot-name": "deviceName", "start-index": 2, "value": "面板"}
        ],
        "intent-name": "openDevice",
        "text": "1层面板启动"
    }
    输出为
    "1 层 面 板 启 动 [SEP] floor_start floor_end deviceName_start deviceName_end O O"
    """

    data_lst = load_from_jsonl(jsonl_path=jsonl_data_path)
    out_lines = [_convert_json_to_ner_format(it) for it in data_lst]
    out_dir = os.path.dirname(output_data_path)
    os.makedirs(out_dir, exist_ok=True)
    save_to_txt(data_lst=out_lines, output_path=output_data_path)

    print(f"write {len(data_lst)} records into {output_data_path}")
