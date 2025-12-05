#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
日报表处理系统
普通模式：双击运行，交互操作
调试模式：创建DEBUG.txt，按指定日期运行
"""
import os
import sys
import datetime


def check_debug_mode():
    """检查DEBUG.txt文件"""
    if not os.path.exists("DEBUG.txt"):
        return False,None

    try:
        with open("DEBUG.txt", 'r', encoding='utf-8') as f:
            content = f.read().strip()

        if not content:
            return True,None

        # 尝试解析日期
        for fmt in ['%Y-%m-%d','%Y/%m/%d','%Y-%#m-%#d','%Y/%#m/%#d',"%Y%m%d"]:
            try:
                date = datetime.datetime.strptime(content, fmt).date()
                print(f" {date}")
                return True,date
            except:
                continue

        print(f"识别异常: {content}")
        return True,None

    except:
        print(f"未知错误")
        sys.exit(1)


def generate_today_filename(yesterday_file, run_date):
    """根据昨日报表文件名生成今日文件名"""
    import re

    # 提取装置名称部分（去掉日期）
    # 匹配模式：某某装置日报表(2025-12-4).xlsx
    pattern = r'^(.*?)装置日报表\(\d{4}-\d{1,2}-\d{1,2}\)\.xlsx$'
    match = re.match(pattern, os.path.basename(yesterday_file))

    if match:
        # 提取装置名称部分
        device_part = match.group(1)  # 某某装置
        today_filename = f"{device_part}装置日报表({run_date.strftime('%Y-%#m-%#d')}).xlsx"
        return today_filename
    else:
        # 如果匹配失败，用默认格式
        print("请检查命名是否符合规范")
        return f"装置日报表({run_date.strftime('%Y-%#m-%#d')}).xlsx"

def get_yesterday_file(run_date):
    """查找昨日报表文件"""
    import glob
    yesterday = run_date - datetime.timedelta(days=1)

    pattern = f"*装置日报表({yesterday.strftime('%Y-%#m-%#d')}).xlsx"

    files = [f for f in glob.glob(pattern) if not f.startswith('~$')]
    if files:
        files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
        return files[0]
    return None

def run_core(is_debug,run_date):
    if run_date is None:
        run_date = datetime.date.today()

    # 检查文件
    if not os.path.exists("报表信息.docx"):
        print("错误: 找不到 报表信息.docx")
        return

    yesterday_file = get_yesterday_file(run_date)
    if not yesterday_file:
        print("错误: 找不到昨日报表，请查找文件是否存在或者命名不符规范")
        return

    # 确认操作
    today_file = generate_today_filename(yesterday_file, run_date)


    if os.path.exists(today_file):
        response = input("文件已存在，是否覆盖？(Y/N): ").upper()
        if response != 'Y':
            print("操作取消")
            return

    try:
        from daily_report.core import process_daily_report

        config = {
            'run_date': run_date,
            'yesterday_file': yesterday_file,
            'today_file': today_file,
            'input_docx': '报表信息.docx',
            'output_dir': '.',
            'verbose': is_debug
        }

        success = process_daily_report(config)

        if success:
            pass
        else:
            print("处理失败，请手动接管")

    except Exception as e:
        print(f"出错: {e}")



def main():
    try:
        is_debug, debug_date = check_debug_mode()

        if is_debug:
            # 调试模式：启用详细的异常捕获
            try:
                run_core(is_debug, debug_date)
            except Exception as e:
                print(f"程序出错: {e}")
                input("\n按回车键退出...")
                sys.exit(1)
        else:
            # 非调试模式：不捕获详细异常，只处理键盘中断
            run_core(is_debug, debug_date)

    except KeyboardInterrupt:
        print("\n程序被中断")
        sys.exit(0)


if __name__ == '__main__':
    main()