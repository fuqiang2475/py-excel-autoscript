import openpyxl
from openpyxl.utils import get_column_letter, column_index_from_string
from copy import copy
import re
from calendar import monthrange
from .static import LiquidLevelValidator

# ==================== 基本操作 ====================

def load_workbook(file_path):
    """加载工作簿"""
    return openpyxl.load_workbook(file_path, data_only=False)

# ==================== 查找功能 ====================

def find_target_column(ws, target_row, start_col, end_col, prefix_str):
    """
    查找包含特定前缀的列

    参数:
        ws: 工作表
        target_row: 查找行号
        start_col: 起始列字母
        end_col: 结束列字母
        prefix_str: 要匹配的前缀
    """
    start_idx = column_index_from_string(start_col)
    end_idx = column_index_from_string(end_col)

    for col in range(start_idx, end_idx + 1):
        cell = ws.cell(row=target_row, column=col)
        if cell.value and str(cell.value).startswith(prefix_str):
            return get_column_letter(col)

    raise ValueError(f"未找到以 '{prefix_str}' 开头的列")


def find_target_row(ws, target_col, start_row, end_row, prefix_str):
    """
    查找包含特定前缀的行

    参数:
        ws: 工作表
        target_col: 查找列字母
        start_row: 起始行号
        end_row: 结束行号
        prefix_str: 要匹配的前缀
    """
    col_idx = column_index_from_string(target_col)

    for row in range(start_row, end_row + 1):
        cell = ws.cell(row=row, column=col_idx)
        if cell.value and str(cell.value).startswith(prefix_str):
            return row

    raise ValueError(f"未找到以 '{prefix_str}' 开头的行")


def find_date_column(ws, target_row, start_col, end_col, target_date_str):
    """
    查找包含指定日期的列

    参数:
        ws: 工作表
        target_row: 查找行号
        start_col: 起始列字母
        end_col: 结束列字母
        target_date_str: 目标日期字符串 (格式: YYYY/MM/DD)
    """
    from datetime import datetime

    start_idx = column_index_from_string(start_col)
    end_idx = column_index_from_string(end_col)

    # 解析目标日期
    try:
        target_date = datetime.strptime(target_date_str, "%Y/%m/%d").date()
    except:
        # 尝试其他格式
        for fmt in ["%Y-%m-%d", "%Y年%m月%d日"]:
            try:
                target_date = datetime.strptime(target_date_str, fmt).date()
                break
            except:
                continue
        else:
            raise ValueError(f"无法解析日期格式: {target_date_str}")

    for col in range(start_idx, end_idx + 1):
        cell = ws.cell(row=target_row, column=col)
        cell_value = cell.value

        # 检查日期类型
        if isinstance(cell_value, datetime):
            if cell_value.date() == target_date:
                return get_column_letter(col)

        # 检查字符串类型
        elif isinstance(cell_value, str):
            for fmt in ["%Y/%m/%d", "%Y-%m-%d", "%Y年%m月%d日"]:
                try:
                    parsed_date = datetime.strptime(cell_value, fmt).date()
                    if parsed_date == target_date:
                        return get_column_letter(col)
                except:
                    continue

    raise ValueError(f"未找到日期为 {target_date_str} 的列")


def find_first_empty_row(ws, column_letter):
    """
    查找指定列的第一个空行

    参数:
        ws: 工作表
        column_letter: 列字母
    """
    col_idx = column_index_from_string(column_letter)
    max_row = 100  # 假设最大100行

    for row in range(max_row, 0, -1):
        if ws.cell(row=row, column=col_idx).value is not None:
            return row + 1

    return 1


# ==================== 单元格操作 ====================

def update_excel_based_on_prefix(ws, search_col, dest_col,start_row=3, prefix_str='', write_content=''):
    """
    功能说明：
    在Excel指定列的第三行开始查找以特定字符开头的内容，
    找到后在同一行的目标列写入指定内容

    参数：
    - search_col: 要查找的列字母（如"A"）
    - dest_col: 要写入的目标列字母（如"B"）
    - start_row: 起始行号（默认3）
    - prefix_str: 要匹配的起始字符串
    - write_content: 匹配成功后写入的内容
    """
    # 加载工作簿和工作表

    # 将列字母转换为数字索引
    search_col_idx = column_index_from_string(search_col)
    dest_col_idx = column_index_from_string(dest_col)

    # 遍历指定列
    for row in ws.iter_rows(min_row=start_row,max_row=100,
                            min_col=search_col_idx,
                            max_col=search_col_idx):
        cell = row[0]
        # 检查单元格内容是否以指定前缀开头
        if cell.value and str(cell.value).startswith(prefix_str):
            # 在目标列写入内容
            ws.cell(row=cell.row, column=dest_col_idx, value=write_content)
            break

    return ws  # 返回修改后的工作簿对象，供后续保存


def copy_cell_range(ws, src_col, tgt_col, rows):
    """
    复制指定行的单元格

    参数:
        ws: 工作表
        src_col: 源列字母
        tgt_col: 目标列字母
        rows: 行号列表
    """
    src_idx = column_index_from_string(src_col)
    tgt_idx = column_index_from_string(tgt_col)

    for row in rows:
        src_value = ws.cell(row=row, column=src_idx).value
        ws.cell(row=row, column=tgt_idx, value=src_value)


def clear_cell_range(ws, start_row, end_row, start_col, end_col):
    """
    清除指定范围内的单元格

    参数:
        ws: 工作表
        start_row: 起始行
        end_row: 结束行
        start_col: 起始列字母
        end_col: 结束列字母
    """
    start_idx = column_index_from_string(start_col)
    end_idx = column_index_from_string(end_col)

    for row in range(start_row, end_row + 1):
        for col in range(start_idx, end_idx + 1):
            ws.cell(row=row, column=col).value = None


# ==================== 公式处理 ====================

def adjust_formula(formula, old_col, new_col):
    """
    调整公式中的列引用

    参数:
        formula: 原始公式
        old_col: 旧列字母
        new_col: 新列字母
    """
    # 构建正则表达式模式
    pattern = r'(?<![!$\'\w])(' + re.escape(old_col) + r')(?=(\$?\d+|\$?[A-Z]+\$?\d+))'

    def replacer(match):
        original = match.group(1)
        old_idx = column_index_from_string(original)
        new_idx = column_index_from_string(new_col)
        offset = new_idx - old_idx
        return get_column_letter(column_index_from_string(original) + offset)

    return re.sub(pattern, replacer, formula, flags=re.IGNORECASE)


def change_formula_column(ws, target_col, old_col, new_col):
    """
    修改指定列中的公式

    参数:
        ws: 工作表
        target_col: 目标列字母
        old_col: 旧列字母
        new_col: 新列字母
    """
    target_idx = column_index_from_string(target_col)
    max_row = find_first_empty_row(ws, target_col) + 1

    for row in range(2, max_row):
        cell = ws.cell(row=row, column=target_idx)
        if cell.data_type == 'f' and cell.value:  # 公式单元格
            new_formula = adjust_formula(cell.value, old_col, new_col)
            cell.value = new_formula


def extract_column_from_formula(ws, cell_address="F4"):
    """
    从公式中提取列字母

    参数:
        ws: 工作表
        cell_address: 单元格地址
    """
    cell = ws[cell_address]
    formula = cell.value

    if not formula or not isinstance(formula, str):
        return None

    # 匹配列字母
    pattern = r'([A-Z]{1,3})(?=\d)'
    match = re.search(pattern, formula)
    return match.group(1) if match else None


def fill_formula_from_left(ws, target_col, target_rows, num_columns):
    """
    从左侧列复制公式

    参数:
        ws: 工作表
        target_col: 目标列字母
        target_rows: 目标行号列表
        num_columns: 要填充的列数
    """
    target_idx = column_index_from_string(target_col)
    source_idx = target_idx - num_columns

    if source_idx < 1:
        raise ValueError("目标列左侧没有足够的列")

    for row in target_rows:
        source_cell = ws.cell(row=row, column=source_idx)

        # 检查是否是公式
        if source_cell.data_type == 'f' and source_cell.value:
            # 向右填充公式
            for offset in range(num_columns):
                current_col = source_idx + offset + 1
                target_cell = ws.cell(row=row, column=current_col)

                # 使用openpyxl的公式翻译器
                from openpyxl.formula.translate import Translator
                translator = Translator(source_cell.value, origin=source_cell.coordinate)
                target_cell.value = translator.translate_formula(target_cell.coordinate)

                # 复制格式
                target_cell.font = copy(source_cell.font)
                target_cell.border = copy(source_cell.border)
                target_cell.fill = copy(source_cell.fill)
                target_cell.alignment = copy(source_cell.alignment)

#每月建表格时删除无公式的内容
def clear_non_formula_cells(ws, target_col_letter,target_row_list):
    # 计算左侧列号
    target_col_num = column_index_from_string(target_col_letter)
    if target_col_num < 1:
        raise ValueError("目标列非有效列")

    # 遍历目标行
    for row in target_row_list:
        row_num = row
        target_cell = ws.cell(row=row_num, column=target_col_num)

        # 仅处理包含公式的单元格
        if target_cell.value and is_formula_cell(target_cell):
            pass
        else:
            target_cell.value = None


def is_formula_cell(cell):
    """
    检查单元格是否包含公式

    参数:
        cell: 单元格对象
    """
    if not cell or not cell.value:
        return False

    if cell.data_type == 'f':  # 公式类型
        formula = cell.value.replace('=', '')
        pattern = r'\$?[A-Za-z]+\$?\d+|:[A-Za-z]+\d+|\b[A-Za-z]+\d+\b'
        return bool(re.search(pattern, formula))

    return False


# ==================== 便捷函数 ====================

def column_add(column_letter, offset):
    """
    列字母偏移

    参数:
        column_letter: 原始列字母
        offset: 偏移量
    """
    idx = column_index_from_string(column_letter)
    return get_column_letter(idx + offset)

# ==================== 高级功能 ====================
def keep_only_one_sheet(wb,wsName):

    # 获取需要删除的表单名称（除12月外的所有表单）
    sheets_to_delete = [name for name in wb.sheetnames if name != wsName]

    # 删除不需要的表单
    for sheet_name in sheets_to_delete:
        del wb[sheet_name]

#构筑年累计的公式
def add_sheet_to_formula(ws,target_col_letter,pre_target_col_letter,pre_col_letter,start_row,end_row,sheet_name,Jan_flag = False):
    """
    在指定列范围内，为每个单元格的公式添加新工作表的引用

    参数:
    ws -- 目标工作表对象
    target_col_letter -- 要修改的列字母 (如 'AN')
    start_row -- 起始行号 (包含)
    end_row -- 结束行号 (包含)
    sheet_name -- 要添加的工作表名称 (如 '3月')
    """
    # 为工作表名称添加单引号（如果名称包含特殊字符需要转义）
    quoted_sheet_name = f"'{sheet_name}'" if not sheet_name.startswith("'") else sheet_name

    for row in range(start_row, end_row + 1):
        cell = f"{target_col_letter}{row}"
        pre_cell = f"={pre_col_letter}{row}"

        # 构建要添加的新部分
        if Jan_flag:
            new_part = ""
        else:
            new_part = str(f"+{quoted_sheet_name}!{pre_target_col_letter}{row}")
        src_cell = ws.cell(row=row,column = column_index_from_string(target_col_letter))
        if src_cell.value and is_formula_cell(src_cell):
            # 如果已有公式，直接追加新部分
            ws[cell].value = pre_cell + new_part


def setup_monthly_dates(ws, start_date, days_in_month, start_col="AQ"):
    """
    设置月度日期列

    参数:
        ws: 工作表
        start_date: 起始日期 (datetime对象)
        days_in_month: 当月天数
        start_col: 起始列字母
    """
    from datetime import timedelta

    col_idx = column_index_from_string(start_col)

    for day in range(days_in_month):
        current_date = start_date + timedelta(days=day)
        ws.cell(row=2, column=col_idx + day, value=current_date)

# ==================== 具体操作 ====================
#月度表格维护
def create_monthly_sheet(wb, output_path,today):
    """
    创建月度工作表

    参数:
        wb: 工作簿
        source_sheet_name: 源工作表名称
        new_sheet_name: 新工作表名称
    """

    #检查: 每月2日新建表单, 每年1月2日新建表格
    import datetime
    #两天前才是上个月
    two_days_prior = (today - datetime.timedelta(days=2))
    if today.day == 2:
        if today.month == 1:
            keep_only_one_sheet(wb, f"{two_days_prior.month}" + "月")

        src_sheet = wb[f"{two_days_prior.month}" + "月"]
        copied_sheet = wb.copy_worksheet(src_sheet)
        copied_sheet.title = f"{today.month}" + "月"
        wb.save(output_path)

        if today.day == 1:
            wsName = f"{two_days_prior.month}" + "月"
        else:
            wsName = f"{today.month}" + "月"

        ws = wb[wsName]
        pre_src = f"{two_days_prior.year}/{two_days_prior.month}/{two_days_prior.day}"
        lst_col_src_minus = find_date_column(ws, target_row=2, start_col="AQ", end_col="BW",
                                             target_date_str=pre_src)
        lst_col_src = column_add(lst_col_src_minus, 1)
        pre_tgt = f"{two_days_prior.year}/{two_days_prior.month}/{1}"
        lst_col_tgt = find_date_column(ws, target_row=2, start_col="AQ", end_col="BW",
                                       target_date_str=pre_tgt)
        # 搬运
        row_end_range = find_first_empty_row(ws, lst_col_tgt) + 1
        # copy-row-list会把公式错误复制，这里排除公式。 分析src列哪些不是公式
        copy_row_list = []
        for i in range(3, row_end_range):
            if is_formula_cell(ws.cell(row=i, column=column_index_from_string(lst_col_src))):
                pass
            else:
                copy_row_list = copy_row_list + [i]

        copy_cell_range(ws, lst_col_src, lst_col_tgt, copy_row_list)
        # 清除无效数据
        clear_cell_range(ws, 2, row_end_range, column_add(lst_col_tgt, 1), column_add(lst_col_tgt, 31))
        # 当月替换
        year, month = today.year, today.month
        _, days_in_month = monthrange(year, month)
        # 抄表
        next_month = (today + datetime.timedelta(days=31))
        dates_cb = [
            f"{year}/{month}/{day}"  # 直接生成目标格式
            for day in range(1, days_in_month + 1)
        ]
        dates_cb += [f"{next_month.year}/{next_month.month}/{1}"]
        # 消耗
        dates_xh = [
            f"{year}/{month}/{day}"  # 直接生成目标格式
            for day in range(1, days_in_month + 1)
        ]
        # 先改抄表
        for col_index, date_str in enumerate(dates_cb, start=1):
            ws.cell(row=2, column=column_index_from_string(lst_col_tgt) + col_index - 1, value=date_str)
        # 消耗
        lst_col_tgt_xh = find_date_column(ws, target_row=2, start_col="H", end_col="AO",
                                          target_date_str=pre_tgt)
        row_end_range = find_first_empty_row(ws, lst_col_tgt_xh) + 1
        clear_cell_range(ws, 2, row_end_range, column_add(lst_col_tgt_xh, 1), column_add(lst_col_tgt_xh, 30))
        for col_index, date_str in enumerate(dates_xh, start=1):
            ws.cell(row=2, column=column_index_from_string(lst_col_tgt_xh) + col_index - 1, value=date_str)
        target_row_list_yes = [i for i in range(3, row_end_range)]
        clear_non_formula_cells(ws, lst_col_tgt_xh, target_row_list_yes)

        # 找年累计
        nlg_col = find_target_column(ws, 1, "AL", "AQ", "年累计")
        pre_ws = wb[f"{two_days_prior.month}" + "月"]
        pre_nlg_col = find_target_column(pre_ws, 1, "AL", "AQ", "年累计")
        ylg_col = find_target_column(ws, 1, "AL", "AQ", "月累计")

        nlg_end_row = find_first_empty_row(ws, nlg_col)

        jan_flag = (today.month == 1)
        add_sheet_to_formula(ws, nlg_col, pre_nlg_col, ylg_col, 3, nlg_end_row, f"{two_days_prior.month}" + "月", jan_flag)

        print("已修改年累计公式")
        print("已完成本月表单建立")

        wb.save(output_path)
        if today.month == 1:
            keep_only_one_sheet(wb, f"{today.month}" + "月")
            print("仅仅保留本月表单")
        wb.save(output_path)


#每日更新列
def daily_update(wb,ws,output_path,today):
    # 找到那一列以前使用的列标

    old_col = extract_column_from_formula(ws)
    import datetime
    yesterday = (today - datetime.timedelta(days=1))
    # 需要改写的是F列,序号为5
    # 如:5月4日时,要填5月3日那一列
    target_date_str_yes = f"{yesterday.year}/{yesterday.month}/{yesterday.day}"
    # 昨日消耗里的一列
    new_col_yes = find_date_column(ws, target_row=2, start_col="H", end_col="AO",
                                   target_date_str=target_date_str_yes)
    # 今日统计要填今天
    target_date_str_today = f"{today.year}/{today.month}/{today.day}"
    if today.day == 1:
        # 打算给在流量抄表数据里加一列
        yes_col = find_date_column(ws, target_row=2, start_col="AQ", end_col="BW",
                                   target_date_str=target_date_str_yes)
        cell = ws.cell(row=2, column=(column_index_from_string(yes_col) + 1))
        cell.value = target_date_str_today
    # 今日统计的一列
    new_col_today = find_date_column(ws, target_row=2, start_col="AQ", end_col="BW",
                                     target_date_str=target_date_str_today)
    # 将F列的序号修改
    change_formula_column(ws, "F", old_col, new_col_yes)
    print("每日列标轮替完成")
    wb.save(output_path)
    wb.active = ws

    # 实现简易的拖动功能
    # 昨日消耗需要扩充的公式
    if today.day != 2:
        target_row_list_yes = [i for i in range(1, 50)]
        num_columns_yes = yesterday.day - 1
        # 昨日消耗
        fill_formula_from_left(ws, new_col_yes, target_row_list_yes, num_columns_yes)
    # 今日统计需要扩充的公式
    target_row_list_today = [i for i in range(1, 35)]
    # 今日统计
    num_columns_today = yesterday.day
    fill_formula_from_left(ws, new_col_today, target_row_list_today, num_columns_today)
    print("公式拖动完成")


    # 将表中,今日库存复制到昨日库存
    row_start_range = find_target_row(ws, "A", 1, 100, "设备名称")
    row_end_range = find_first_empty_row(ws, "A") + 1
    copy_row_list = [i for i in range(row_start_range + 1, row_end_range)]
    src_col = find_target_column(ws, row_start_range, "A", "P", "今日早晨")
    tgt_col = find_target_column(ws, row_start_range, "A", "P", "昨日早晨")
    sb_col = find_target_column(ws, row_start_range, "A", "P", "设备名称")
    if today.day == 1:
        month_col = find_target_column(ws, row_start_range, "A", "P", "上月末")
        copy_cell_range(ws, tgt_col, month_col, copy_row_list)
        print("原昨日7:30库存已覆盖上月末库存")
    copy_cell_range(ws, src_col, tgt_col, copy_row_list)
    ls_row = find_target_row(ws, sb_col, row_start_range, row_start_range + 50, "腐蚀性供料槽")
    ls_col = column_index_from_string(src_col)

    print("原今日7:30库存已覆盖昨日库存7:30")
    return ls_row,ls_col,new_col_yes,new_col_today

#将report转为填写用的excel_report
def write_excel_report(report,idx):
    validator = LiquidLevelValidator()
    if report["shift_count"]==2:

        lssyqk = "="+str(report['daily'][0]['corrosive']['usage'])+"+"+str(report['daily'][1]['corrosive']['usage'])
        yasyqk = "="+str(report['daily'][0]['toxicity']['usage'])+"+"+str(report['daily'][1]['toxicity']['usage'])
        tdmypf = "="+str(report['daily'][0]['tonnage']['discharge'])+"+"+str(report['daily'][1]['tonnage']['discharge'])
        sgtd = "="+str(report['daily'][0]['reactions']['auxiliary_B']['raw_volume'])+"+"+str(report['daily'][1]['reactions']['auxiliary_B']['raw_volume'])
        sgfms= "="+str(report['daily'][0]['reactions']['auxiliary_A']['raw_volume']) + "+"+str(report['daily'][1]['reactions']['auxiliary_A'][
            'raw_volume'])

    else:#只有一班
        lssyqk = "="+str(report['daily'][0]['corrosive']['usage'])
        yasyqk = "="+str(report['daily'][0]['toxicity']['usage'])
        tdmypf = "="+str(report['daily'][0]['tonnage']['discharge'])
        sgtd = "="+str(report['daily'][0]['reactions']['auxiliary_B']['raw_volume'])
        sgfms= "="+str(report['daily'][0]['reactions']['auxiliary_A']['raw_volume'])
    excel_report_left = {
        "腐蚀性介质使用情况": lssyqk,
        "有毒性介质使用情况": yasyqk,
        "废液A转移量": tdmypf,
        "废液B排放": tdmypf,
        "废液B处理热源量":"="+str(report['24hour']['废液B处理热源流量'])+"*24" if len(report['24hour'])>1 else None,
    }
    excel_report_right = {
        "有毒性一号罐": "/",
        "有毒性二号罐液位": report['daily'][idx]['toxicity']['tanks']['二号罐'] ,
        "有毒性三号罐液位": report['daily'][idx]['toxicity']['tanks']['三号罐'] ,
        "腐蚀性一号罐液位": report['daily'][idx]['corrosive']['tanks']['一号罐'] ,
        "腐蚀性二号罐液位": report['daily'][idx]['corrosive']['tanks']['二号罐'] ,
        "原料A累计接收流量计数据": report['daily'][idx]['basic']['原料A使用流量'] ,
        "原料A（生产产品B用）": sgtd,
        "原料A（生产产品A用）": sgfms,
        "热源流量计读数": float(report['daily'][idx]['basic']['热源']),
        "工艺水B流量计读数": report['daily'][idx]['basic']['工艺水B'] ,
        "工艺水A流量计读数": float(report['daily'][idx]['basic']['工艺水A']) ,
        "电表读数": report['daily'][idx]['basic']['用电量'] ,
        "动力风流量计读数": report['daily'][idx]['basic']['动力风'] ,
        "保护气流量计读数": report['daily'][idx]['basic']['保护气'] ,
        "废液A累积流量计读数": report['daily'][idx]['basic']['废液A转移累积量'] ,
        "有毒性二号罐库存吨位":validator.get_tonnage(validator.validate_input(report['daily'][idx]['toxicity']['tanks']['二号罐'])),
        "有毒性三号罐库存吨位": validator.get_tonnage(validator.validate_input(report['daily'][idx]['toxicity']['tanks']['三号罐']))
    }
    excel_report = [excel_report_left,excel_report_right]
    return excel_report

def write_excel(wb,sheet_name,excel_report,new_col_yes,new_col_today):
    ws = wb[sheet_name]
    today_list = find_target_column(ws,3,"A","BW","有毒性一号罐")
    yes_list = find_target_column(ws,3,"A","BW","原料A使用情况")

    for key,val in excel_report[0].items():
        ws = update_excel_based_on_prefix(ws,yes_list,new_col_yes,3,key,val)
    for key, val in excel_report[1].items():
        ws = update_excel_based_on_prefix(ws, today_list, new_col_today, 3, key, val)
    return wb
