"""
报表解析模块 - 所有解析功能集中在这里
"""
import re
from collections import defaultdict
from docx import Document


def parse_document(file_path):
    """解析Word日报表文档，带有错误处理"""
    try:
        doc = Document(file_path)
        content = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
    except Exception as e:
        print(f"无法读取Word文件 {file_path}: {e}")
        return None

    shift_count = 0
    reports = {
        "daily": [],
        "24hour": defaultdict(lambda: None),
        "shift_count": shift_count,
    }

    current_shift = None
    current_chemical = None

    for line_num, line in enumerate(content, 1):
        try:
            # 处理24小时统计
            if line.startswith('24小时') or line.startswith('腐蚀性供料槽'):
                key_part, val_part = split_key_value(line)
                if key_part:
                    key = key_part.replace('24小时', '').strip()
                    reports["24hour"][key] = extract_number(val_part)
                else:
                    print(f"第{line_num}行解析失败: {line}")
                continue

            # 新班次开始
            if line.startswith('工艺水A'):
                current_shift = create_shift_structure()
                reports["daily"].append(current_shift)
                shift_count = shift_count + 1
                reports["shift_count"] = shift_count
                current_chemical = None

                key, val = extract_kv(line)
                if key:
                    current_shift['basic'][key] = val
                continue

            if current_shift:
                # 处理化学品库存
                if re.match(r'^(腐蚀性|有毒性)库存', line):
                    chemical_type = 'corrosive' if '腐蚀性' in line else 'toxicity'
                    current_chemical = chemical_type
                    key, val = extract_kv(line)
                    if key:
                        current_shift[chemical_type]['stock'] = val
                    continue

                # 处理罐体数据
                if '液位' in line:
                    key, val = extract_kv(line)
                    tank_match = re.search(r'[一二三]号罐', key) if key else None
                    if tank_match and current_chemical:
                        tank_id = tank_match.group()
                        current_shift[current_chemical]['tanks'][tank_id] = val
                    continue

                # 处理生产数据
                #print('++'+line)
                if '使用量' in line:
                    #print("--"+line)
                    try:
                        # 产品A
                        if '产品A' in line:
                            auxiliary_A = re.findall(r'产品A[^0-9]*(\d+)[^0-9]*批', line)
                            if auxiliary_A:
                                current_shift['reactions']['auxiliary_A']['count'] = int(auxiliary_A[0])

                            raw_match = re.search(r'原料A使用量[：:]?\s*([\d.]+)', line.replace(' ', ''))
                            if raw_match:
                                current_shift['reactions']['auxiliary_A']['raw_volume'] = float(raw_match.group(1))

                        # 产品B
                        if '产品B' in line:
                            auxiliary_B = re.findall(r'产品B[^0-9]*(\d+)[^0-9]*批', line)
                            if auxiliary_B:
                                current_shift['reactions']['auxiliary_B']['count'] = int(auxiliary_B[0])

                            raw_match = re.search(r'原料A使用量[：:]?\s*([\d.]+)', line.replace(' ', ''))
                            if raw_match:
                                current_shift['reactions']['auxiliary_B']['raw_volume'] = float(raw_match.group(1))

                    except Exception as e:
                        print(f"第{line_num}行数据解析失败: {line}")
                        print(f"错误详情: {e}")
                    continue

                    # 处理使用/入库
                if any(k in line for k in ['使用', '入库']):
                    key, val = extract_kv(line)
                    if key and current_chemical:
                        field = 'usage' if key == '使用' else 'inbound'
                        current_shift[current_chemical][field] = val or 0
                    elif key:
                        current_shift['basic'][key] = val
                    continue
                # 处理吨桶数据
                if '废液B吨桶数量' in line:
                    try:
                        discharge = re.search(r'排(\d+)', line)
                        if discharge:
                            current_shift['tonnage']['discharge'] = int(discharge.group(1))
                        else:
                            current_shift['tonnage']['discharge'] = int(0)
                    except Exception as e:
                        print(f" 第{line_num}行数据解析失败: {line}")
                        print(f"错误详情: {e}")
                    continue

                # 其他基础数据
                if '：' in line or ':' in line:
                    key, val = extract_kv(line)
                    if key:
                        current_shift['basic'][key] = val

        except Exception as e:
            # 捕获这一行的任何解析错误
            print(f"第{line_num}行解析失败: {line}")
            print(f"错误详情: {e}")
            # 可以选择是否继续处理下一行
            continue

    # 检查解析结果
    if not reports["daily"]:
        print("警告: 没有解析到任何班次数据")
        print("请检查报表信息.docx格式是否正确")

    return reports


def create_shift_structure():
    """创建班次数据结构"""
    return {
        "basic": defaultdict(lambda: None),
        "corrosive": {
            "stock": None,
            "tanks": defaultdict(lambda: None),
            "usage": None,
            "inbound": 0
        },
        "toxicity": {
            "stock": None,
            "tanks": defaultdict(lambda: None),
            "usage": None,
            "inbound": 0
        },
        "reactions": {
            "auxiliary_A": {"count": 0, "raw_volume": 0},
            "auxiliary_B": {"count": 0, "raw_volume": 0},
        },
        "tonnage": {
            "discharge": 0,
        }
    }


def split_key_value(line):
    """分割键值对"""
    match = re.match(r'^(.+?)[：:\s]\s*(.+)$', line.strip())
    if match:
        key, value = match.groups()
        if re.match(r'^\d', value):
            return key.strip(), value.strip()

    match = re.match(r'^(.*?\D)(\d+.*)$', line.strip())
    if match:
        return match.group(1).strip(), match.group(2).strip()

    return None, None


def extract_number(text):
    """提取数字"""
    try:
        match = re.search(r'\s*([\d,.]+)', text.strip())
        if match:
            num_str = match.group(1).replace(',', '')
            if '.' in num_str:
                return float(num_str)
            else:
                return int(num_str)
        return 0
    except Exception:
        return 0


def extract_kv(text):
    """提取键值对"""
    key_part, val_part = split_key_value(text)
    if key_part and val_part:
        return key_part.strip(), extract_number(val_part)
    return None, 0