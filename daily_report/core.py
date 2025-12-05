"""
核心处理模块 - 日报表处理主逻辑
"""
import os
import shutil
import datetime
import traceback

# 导入其他模块
from . import parser
from . import excel_ops



def process_daily_report(config):
    """
    处理日报表的主函数

    Args:
        config: 配置字典，包含：
            'run_date': run_date,运行日期
            'yesterday_file': yesterday_file,昨日报表名称
            'today_file': today_file,今日报表名称
            'input_docx': '报表信息.docx',Word文档路径
            'output_dir': '.',输出目录
            'verbose': is_debug,是否详细输出
    """
    try:
        # 1. 生成今日文件名
        today_file = config['today_file']
        output_path = str(os.path.join(config['output_dir'], today_file))
        yesterday_file = config['yesterday_file']
        input_path = str(os.path.join(config['output_dir'], yesterday_file))

        if config.get('verbose', False):
            print(f"输出文件: {output_path}")

        # 2. 复制昨日报表作为模板
        if config.get('verbose', False):
            print("复制Excel模板...")
        shutil.copy2(input_path, output_path)

        # 3.每月维护
        wb = excel_ops.load_workbook(output_path)

        today = config['run_date']
        yesterday = (today - datetime.timedelta(days=1))

        if today.day == 1:
            wsName = f"{yesterday.month}" + "月"
        else:
            wsName = f"{today.month}" + "月"
        excel_ops.create_monthly_sheet(wb,output_path, today)

        # 4.当日的表格修改公式
        ws = wb[wsName]
        ls_row,ls_col,new_col_yes,new_col_today = excel_ops.daily_update(wb,ws,output_path,today)

        # 5. 解析Word文档
        if config.get('verbose', False):
            print("解析报表信息...")
        report = parser.parse_document(config['input_docx'])

        # 6. 处理Excel文件
        if report["shift_count"] > 0:
            cal_num = 0
            if report["shift_count"] == 2:
                if report['daily'][0]['basic']['仪表风'] <= report['daily'][1]['basic']['仪表风']:
                    cal_num = 1
                excel_report = excel_ops.write_excel_report(report, cal_num)
            elif report["shift_count"] == 1:
                input("请确认是否昨日只有一个班的报表?(按回车键继续)")
                excel_report = excel_ops.write_excel_report(report, cal_num)
            else:
                input("文件输入超过2个班的日报表,请重新检查 报表信息.docx 文件!")
                wb.close()
                exit()
            ls_cell = ws.cell(row=ls_row, column=ls_col)
            ls_cell.value = "=" + str(report['24hour']['硫酸高位槽总液位']) + "*0.057" if len(
                report['24hour']) > 1 else None
            if len(report['24hour']) < 1:
                print("建议将24小时报表也复制到报表信息中")
            print("不要忘记修改今日库存")
        else:
            wb.close()
            exit()

        wb = excel_ops.write_excel(wb, wsName, excel_report, new_col_yes, new_col_today)
        wb.save(output_path)
        wb.close()
        input("大部分信息已填充(按回车键结束)")

        if config.get('verbose', False):
            print("处理完成")

        return True

    except Exception as e:
        print(f"处理失败: {e}")
        if config.get('verbose', False):
            traceback.print_exc()
        return False





