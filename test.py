from convert.js import revert_js_from_xlsx
from TPL import TplItem
from text_io.excel import load_json_list_from_xlsx, save_json_list_into_xlsx
from utils import parse_code_condition

def test_tpl_analysis(version="v1"):
    tpl_path = "/Users/zhanzq/Downloads/intent_to_command_with_param_{}.xlsx".format(version)
    tpl_dct = load_json_list_from_xlsx(xlsx_path=tpl_path)
    car_tp = "E38"
    conditions = dict()
    perception_data = dict()
    branch_info = dict()
    intent_info = dict()
    for car_type, tpl_items in tpl_dct.items():
        if car_tp and car_tp != car_type:
            continue
        for i, tpl_item in enumerate(tpl_items):
            tpl_item = TplItem(tpl_item=tpl_item)
            for key, val in tpl_item.data.items():
                perception_data[key] = perception_data.get(key, 0) + val
            for key, val in tpl_item.conditions.items():
                conditions[key] = conditions.get(key, 0) + val
            domain = tpl_item.domain
            branch = tpl_item.branch.split("=")[0]
            if branch != "" and branch != "default":
                if domain in branch_info:
                    branch_info[branch].add(domain)
                else:
                    branch_info[branch] = set([domain])

            intent = tpl_item.intent
            if intent not in intent_info:
                intent_info[intent] = 1
            else:
                intent_info[intent] += 1

    data_lst = [{"感知点": key, "频率": val} for key, val in perception_data.items()]
    data_lst.sort(key=lambda it: -it["频率"])
    save_json_list_into_xlsx(json_lst=data_lst, xlsx_path="/Users/zhanzq/Downloads/tpl_info_0324.xlsx", sheet_name="E38感知点信息")

    cond_lst = [{"判断条件": key, "频率": val} for key, val in conditions.items()]
    cond_lst.sort(key=lambda it: -it["频率"])
    save_json_list_into_xlsx(json_lst=cond_lst, xlsx_path="/Users/zhanzq/Downloads/tpl_info_0324.xlsx", sheet_name="E38判断条件信息")

    branch_lst = [{"槽位": key, "domain_lst": ", ".join(list(val))} for key, val in branch_info.items()]
    save_json_list_into_xlsx(json_lst=branch_lst, xlsx_path="/Users/zhanzq/Downloads/tpl_info_0324.xlsx", sheet_name="E38槽位信息")

    cond_lst = [{"intent": key, "频率": val} for key, val in intent_info.items()]
    cond_lst.sort(key=lambda it: -it["频率"])
    save_json_list_into_xlsx(json_lst=cond_lst, xlsx_path="/Users/zhanzq/Downloads/tpl_info_0324.xlsx", sheet_name="E38意图信息")

    # tpl_v4 = TPL(tpl_xlsx_path=tpl_v4_path)
    # tpl_v4.analysis_tpl_data(version="v4", car_type="E38")

    # tpl_pre_path = "/Users/zhanzq/github/xp-car-nlu/tools/gen/config/intent_to_command_with_param_pre.xlsx"
    # tpl_pre = TPL(tpl_xlsx_path=tpl_pre_path)
    # tpl_pre.analysis_tpl_data(version="pre", car_type="E38")


def test_parse_code_condition():
    tpl = """
    if(eqMethod(0,data('get.car.level'))){
    tts('当前配置没有这个功能哦');
    nlg(\"PN_unsupport_AB_1\");
    return;
}
var(_currentMode,data('combo.get.current.user.mode'));
if(eqMethod('spacecapsule_mode_movie',_currentMode)){
    if(data('is.unity.app.top','XPPlugin_SpaceCapsuleMainPageApp')){
        var('XPPlugin_SpaceCapsuleMainPageApp');
    }else{
        var(_appName,'XPPlugin_SpaceCapsuleApp');
    }
    var(_unityStatus,data('unity.app.close',param(\"{'app_name':'%1$s'}\",_appName)));
    if(eqMethod(_unityStatus,1)){
        tts('要关闭的内容已经关了哦');
        nlg(\"PN_pageAlreadyClosed\");
    }elif(eqMethod(_unityStatus,2)){
        tts('桌面无法关闭哦');
        nlg(\"PN_closeMap_AB_1\");
    }elif(eqMethod(_unityStatus,3)){
        tts('请先操作当前弹窗');
        nlg(\"PN_popUp_AB_1\");
    }elif(eqMethod(_unityStatus,4)){
    }elif(eqMethod(_unityStatus,0)){
        tts('好哒');
        nlg(\"PN_control_samrtspace_xplay_close_1\");
    }else{
        tts('关闭失败');
        nlg(\"PN_generalError_AB_2\");
    }
}else{
    tts('要关闭的内容已经关了哦');
    nlg(\"PN_pageAlreadyClosed\");
}
		"""
    tpl = """
    if(eqMethod(0,data('get.car.level'))){
  tts('当前配置没有这个功能哦');
  nlg("PN_unsupport_AB_1");
  return;
}
var(_currentMode,data('combo.get.current.user.mode'));
if(eqMethod('spacecapsule_mode_movie', _currentMode)){

        if(data('is.unity.app.top','XPPlugin_SpaceCapsuleMainPageApp')){
            var(app_name,'XPPlugin_SpaceCapsuleMainPageApp');
        }else{
           var(_appName,'XPPlugin_SpaceCapsuleApp');
        }

        var(_unityStatus,data('unity.app.close',param("{'app_name':'%1$s'}",_appName)));
        if(eqMethod(_unityStatus,1)){
            tts('要关闭的内容已经关了哦');
            nlg("PN_pageAlreadyClosed");
        }elif(eqMethod(_unityStatus,2)){
            tts('桌面无法关闭哦');
            nlg("PN_closeMap_AB_1");
        }elif(eqMethod(_unityStatus,3)){
            tts('请先操作当前弹窗');
            nlg("PN_popUp_AB_1");
        }elif(eqMethod(_unityStatus,4)){
        }elif(eqMethod(_unityStatus,0)){
            tts('好哒');
            nlg("PN_control_samrtspace_xplay_close_1");
        }else{
            tts('关闭失败');
            nlg("PN_generalError_AB_2");
        }


}else{
 tts('要关闭的内容已经关了哦');
 nlg("PN_pageAlreadyClosed");
}
"""
    parse_code_condition(tpl)


if __name__ == "__main__":
    # test_save_jsons_into_xlsx()
    # test_load_jsons_from_xlsx()
    # test_tpl_analysis(version="merged-pre-0401")

    # process_slot_info()

    # from TPL import parse_perceptual_data, get_from_adjust_info
    # data_dct = parse_perceptual_data(perceptual_data_path="/Users/zhanzq/Downloads/感知点汇总.xlsx")
    # res = get_from_adjust_info()
    #
    # codes = "tts('hello');"
    #
    # param_dct = TplItem.get_param_dct(format_codes=codes)
    # print(param_dct)
    # for cond in []:
    #     new_cond = TplItem.convert_cond_to_exact_info(cond, param_dct)
    #     print("convert {} to {}".format(cond, new_cond))
    #
    # js_path = "/Users/zhanzq/Downloads/tpl_js_0402"
    # xlsx_path = "/Users/zhanzq/Downloads/intent_to_command_with_param_merged-0402.xlsx"
    # revert_js_from_xlsx(js_path=js_path, xlsx_path=xlsx_path)

    test_parse_code_condition()
