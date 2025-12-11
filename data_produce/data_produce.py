"""
化工连续生产日报表数据生成器 - 合理精度版
根据用量大小确定数据精度
"""
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

class DailyReportGenerator:
    def __init__(self):
        np.random.seed(42)
        self.full_days = 31      # 完整天数
        self.total_records = self.full_days +2  # 31天完整 + 1天白班 + 1天夜班

        
        # 生成所有日期时间 - 修正版
        self.all_dates = []
        base_date = datetime(2025, 1, 1)
        
        # 1月1日-1月31日（完整1+30天）- 每个日期代表该日07:30的交班时间
        for i in range(self.full_days):
            date_str = (base_date + timedelta(days=i+1)).strftime('%Y-%m-%d 07:30')
            self.all_dates.append({'date': date_str, 'type': 'full', 'shift': None})
        
        # 2月1日白班（第31天白班）- 2月1日19:30交班
        date_32_day = (base_date + timedelta(days=self.full_days)).strftime('%Y-%m-%d 19:30')
        self.all_dates.append({'date': date_32_day, 'type': 'half', 'shift': '白班'})
        
        # 2月1日夜班（第32天夜班）- 2月2日07:30交班
        date_32_night = (base_date + timedelta(days=self.full_days+1)).strftime('%Y-%m-%d 07:30')
        self.all_dates.append({'date': date_32_night, 'type': 'half', 'shift': '夜班'})

        #print(len(self.all_dates))
        # 配置
        self.config = {
            'raw_A_to_A_atomic': 0.9,
            'raw_A_to_B_atomic': 1.1,
            'raw_A_variation': 0.02,
            
            'conv_A_min': 0.88,
            'conv_A_max': 0.92,
            'conv_B_min': 0.78,
            'conv_B_max': 0.82,
            
            'catalyst_ratio': 1.07,
            'additive_ratio': 0.7,
            'steam_ratio': 0.8,
            'waterB_ratio': 0.5,
            'waterA_ratio': 0.7,
            'power_ratio': 45,
            'air_ratio': 200,
            'gas_ratio': 50,
        }
    
    def generate_raw_material(self):
        """生成原料投入数据 - 合理精度"""
        # 完整天的数据 - 31天
        product_A_count_full = np.random.choice([3,4,5], size = self.full_days)
        product_B_count_full = 8 - product_A_count_full

        #模拟单位用量
        product_A_coeff_full = np.random.uniform(1 - self.config['raw_A_variation'], 1 + self.config['raw_A_variation'], self.full_days) * self.config['raw_A_to_A_atomic']
        product_B_coeff_full = np.random.uniform(1 - self.config['raw_A_variation'], 1 + self.config['raw_A_variation'], self.full_days) * self.config['raw_A_to_B_atomic']

        # 模拟最小单元
        raw_A_to_A_full = np.round(product_A_count_full * product_A_coeff_full, 2)
        raw_A_to_B_full = np.round(product_B_count_full * product_B_coeff_full, 2)

        raw_A_full = raw_A_to_A_full + raw_A_to_B_full
       
        #白班夜班
        product_A_count_half_day = 2
        product_B_count_half_day = 2
        product_A_count_half_night = 2
        product_B_count_half_night = 2

        # 模拟最小单元
        raw_A_to_A_half_day = np.round(product_A_count_half_day * 1.01 * self.config['raw_A_to_A_atomic'], 2) 
        raw_A_to_B_half_day = np.round(product_B_count_half_day * 1.01 * self.config['raw_A_to_B_atomic'], 2)
        raw_A_to_A_half_night = np.round(product_A_count_half_night * 0.99 * self.config['raw_A_to_A_atomic'], 2)
        raw_A_to_B_half_night = np.round(product_B_count_half_night * 0.99 * self.config['raw_A_to_B_atomic'], 2)

        raw_A_half_day = raw_A_to_A_half_day + raw_A_to_B_half_day
        raw_A_half_night = raw_A_to_A_half_night + raw_A_to_B_half_night
       
        # 合并
        raw_A_total = np.concatenate([raw_A_full, np.array([raw_A_half_day]), np.array([raw_A_half_night])])
        raw_A_to_A = np.concatenate([raw_A_to_A_full, np.array([raw_A_to_A_half_day]), np.array([raw_A_to_A_half_night])])
        raw_A_to_B = np.concatenate([raw_A_to_B_full, np.array([raw_A_to_B_half_day]), np.array([raw_A_to_B_half_night])])

        product_A_count = np.concatenate([product_A_count_full, np.array([product_A_count_half_day]), np.array([product_A_count_half_night])])
        product_B_count = np.concatenate([product_B_count_full, np.array([product_B_count_half_day]), np.array([product_B_count_half_night])])
      
        return {
            'raw_A_total': raw_A_total.tolist(),
            'raw_A_to_A': raw_A_to_A.tolist(),
            'raw_A_to_B': raw_A_to_B.tolist(),
            'product_A_count':product_A_count.tolist(),
            'product_B_count':product_B_count.tolist()
        }
    
    def generate_products(self, raw_data):
        """生成产品数据 - 合理精度"""
        n_total = len(raw_data['raw_A_total'])
        
        # 转化率
        conv_A = np.random.uniform(self.config['conv_A_min'], self.config['conv_A_max'], n_total)
        conv_B = np.random.uniform(self.config['conv_B_min'], self.config['conv_B_max'], n_total)
        
        # 
        raw_A_to_A = np.array(raw_data['raw_A_to_A'])
        raw_A_to_B = np.array(raw_data['raw_A_to_B'])
        
        product_A = np.round(raw_A_to_A * conv_A, 1)
        product_B = np.round(raw_A_to_B * conv_B, 1)
        
        return {
            'product_A': product_A.tolist(),
            'product_B': product_B.tolist()
        }
    
    def generate_medium(self, product_data):
        """生成介质消耗 - 添加随机波动和白班夜班减半"""
        n_total = len(product_data['product_B'])
        product_B = np.array(product_data['product_B'])
        
        # 添加正常波动（±2%）
        catalyst_ratio_variation = np.random.uniform(0.98, 1.02, n_total)
        additive_ratio_variation = np.random.uniform(0.98, 1.02, n_total)
        
        # 基础值 + 波动
        catalyst = np.round(product_B * self.config['catalyst_ratio'] * catalyst_ratio_variation, 2)
        additive = np.round(product_B * self.config['additive_ratio'] * additive_ratio_variation, 2)
    
        return {
            'catalyst': catalyst.tolist(),
            'additive': additive.tolist()
        }
    
    def generate_energy(self, product_data):
        """生成能耗数据 - 根据不同用量确定精度"""
        product_A = np.array(product_data['product_A'])
        product_B = np.array(product_data['product_B'])
        total_product = product_A + product_B
        n_total = len(total_product)
        
        # 蒸汽约6.8吨/天，保留一位小数
        steam = np.round(total_product * self.config['steam_ratio'], 1)
        
        # 废液处理热源：全天24吨，半天12吨
        waste_steam_ratio = np.random.uniform(0.45, 0.55, n_total)
        waste_steam = np.round(steam * waste_steam_ratio, 1)
        
        # 工艺水B约4.25吨/天，保留一位小数
        water_B = np.round(total_product * self.config['waterB_ratio'], 1)
        
        # 工艺水A约5.95吨/天，保留一位小数
        water_A = np.round(total_product * self.config['waterA_ratio'], 1)
        
        # 电量约382kWh/天，整数
        power = (total_product * self.config['power_ratio']).astype(int)
        
        # 动力风约1700Nm³/天，整数
        air = (total_product * self.config['air_ratio']).astype(int)
        
        # 保护气约425Nm³/天，整数
        gas = (total_product * self.config['gas_ratio']).astype(int)
        
        return {
            'steam': steam.tolist(),
            'waste_steam': waste_steam.tolist(),
            'water_B': water_B.tolist(),
            'water_A': water_A.tolist(),
            'power': power.tolist(),
            'air': air.tolist(),
            'gas': gas.tolist()
        }
    
    def generate_waste(self, product_data):
        """生成三废数据 - 合理精度"""
        product_A = np.array(product_data['product_A'])
        product_B = np.array(product_data['product_B'])
        total_product = product_A + product_B
        n_total = len(total_product)
        
        # 雨水：0-2吨，偶尔有，保留一位小数
        rain = np.zeros(n_total)
        rain_indices = np.random.choice(range(self.full_days), 4, replace=False)
        rain[rain_indices] = np.round(np.random.uniform(0.5, 2.0, 4), 1)
        
        # 废液A：约2.55吨/天，保留一位小数
        waste_water = np.round(total_product * 0.3, 1)
        
        # 废液B（吨桶间歇排放）：0-5吨，保留一位小数
        waste_B = np.zeros(n_total)
        for i in range(self.full_days):  # 完整天
            if i % 7 == 0:  # 周一
                waste_B[i] = np.random.choice([3.0, 4.0, 5.0])
            elif i % 7 == 3:  # 周四
                waste_B[i] = np.random.choice([2.0, 3.0, 4.0])
        waste_B = np.round(waste_B, 1)
        
        # 废渣：0.8-1.2吨，偶尔有，保留一位小数
        waste_solid = np.zeros(n_total)
        solid_indices = np.random.choice(range(self.full_days), 6, replace=False)
        waste_solid[solid_indices] = np.round(np.random.uniform(0.8, 1.2, 6), 1)
        
        return {
            'rain': rain.tolist(),
            'waste_water': waste_water.tolist(),
            'waste_B': waste_B.tolist(),
            'waste_solid': waste_solid.tolist()
        }
    
    def generate_auxiliary_material(self, product_data):
        """生成辅料数据"""
        n_total = len(product_data['product_A'])
        product_A = np.array(product_data['product_A'])
        product_B = np.array(product_data['product_B'])
        
        # 产品A辅料：约10kg/吨产品A
        auxiliary_A_ratio = np.random.uniform(0.98, 1.02, n_total)
        auxiliary_A = np.round(product_A * 10 * auxiliary_A_ratio, 0).astype(int)  # kg，整数
        
        # 产品B辅料：约15kg/吨产品B
        auxiliary_B_ratio = np.random.uniform(0.98, 1.02, n_total)
        auxiliary_B = np.round(product_B * 15 * auxiliary_B_ratio, 0).astype(int)  # kg，整数
        
        return {
            'auxiliary_A': auxiliary_A.tolist(),
            'auxiliary_B': auxiliary_B.tolist()
        }
    
    def generate_tank_data(self, medium_data):
        """生成罐区液位数据 - 与实际使用量相关"""
        n_total = self.total_records
        catalyst_usage = np.array(medium_data['catalyst'])  # 腐蚀性介质用量
        additive_usage = np.array(medium_data['additive'])   # 有毒性介质用量
        
        # 腐蚀性罐区 - 两个罐，哪个液位高用哪个
        corrosive_tank1 = []
        corrosive_tank2 = []
        corrosive_unload = []
        
        # 初始液位
        tank1_level = 70.53  # 一号罐起始70%
        tank2_level = 65.32  # 二号罐起始65%
        corrosive_tank1.append(round(tank1_level, 2))
        corrosive_tank2.append(round(tank2_level, 2))
        
        # 罐容量假设：液位1% = 1.5吨（基于之前的换算）
        tank_capacity = 1.5  # 吨/%
        
        for day in range(n_total):
            
            
            # 当日腐蚀性介质用量（吨）
            daily_usage = catalyst_usage[day]
            
            # 转化为液位下降（%）
            level_decrease = daily_usage / tank_capacity
            
            # 使用液位高的罐
            if tank1_level >= tank2_level:
                # 先用一号罐
                if tank1_level >= level_decrease:
                    tank1_level -= level_decrease
                else:
                    # 一号罐不够，用完剩余用二号罐
                    remaining = level_decrease - tank1_level
                    tank1_level = 0
                    tank2_level = max(0, tank2_level - remaining)
            else:
                # 先用二号罐
                if tank2_level >= level_decrease:
                    tank2_level -= level_decrease
                else:
                    # 二号罐不够，用完剩余用一号罐
                    remaining = level_decrease - tank2_level
                    tank2_level = 0
                    tank1_level = max(0, tank1_level - remaining)
            
            # 模拟补货（当某个罐低于30%时补货到70%）
            corrosive_unload_total = 0
            if tank1_level < 30 and day < n_total-1:  # 不是最后一天
                corrosive_unload_tank1 = 30*np.random.uniform(0.95, 1.05)
                corrosive_unload_total += corrosive_unload_tank1
                tank1_level += corrosive_unload_tank1 / tank_capacity
            if tank2_level < 30 and day < n_total-1:
                corrosive_unload_tank2 = 30*np.random.uniform(0.95, 1.05)
                corrosive_unload_total += corrosive_unload_tank2
                tank2_level += corrosive_unload_tank2 / tank_capacity


            # 记录当前液位
            corrosive_tank1.append(round(tank1_level, 2))
            corrosive_tank2.append(round(tank2_level, 2))
            corrosive_unload.append(round(corrosive_unload_total,2))
        
        # 有毒性罐区 - 三个罐，同样逻辑
        toxic_tank2 = []
        toxic_tank3 = []
        toxic_unload = []
        
        # 初始液位
        toxic2_level = 74.24  # 二号罐起始74%
        toxic3_level = 60.28  # 三号罐起始60%
        toxic_tank2.append(round(toxic2_level, 2))
        toxic_tank3.append(round(toxic3_level, 2))
        
        toxic_tank_capacity = 0.6475  # 吨/%，基于51.8吨/80%
        
        for day in range(n_total):
            
            
            # 当日有毒性介质用量（吨）
            daily_usage = additive_usage[day]
            
            # 转化为液位下降（%）
            level_decrease = daily_usage / toxic_tank_capacity
            
            # 使用液位高的罐（二号或三号）
            if toxic2_level >= toxic3_level:
                # 先用二号罐
                if toxic2_level >= level_decrease:
                    toxic2_level -= level_decrease
                else:
                    # 二号罐不够，用完剩余用三号罐
                    remaining = level_decrease - toxic2_level
                    toxic2_level = 0
                    toxic3_level = max(0, toxic3_level - remaining)
            else:
                # 先用三号罐
                if toxic3_level >= level_decrease:
                    toxic3_level -= level_decrease
                else:
                    # 三号罐不够，用完剩余用二号罐
                    remaining = level_decrease - toxic3_level
                    toxic3_level = 0
                    toxic2_level = max(0, toxic2_level - remaining)
            
            # 模拟补货（当罐低于30%时补货到74%）
            toxic_unload_total = 0
            if toxic2_level < 30 and day < n_total-1:
                toxic_unload_tank2 = 20*np.random.uniform(0.95, 1.05)
                toxic_unload_total += toxic_unload_tank2
                toxic2_level += toxic_unload_total/toxic_tank_capacity
            if toxic3_level < 30 and day < n_total-1:
                toxic_unload_tank3 = 20*np.random.uniform(0.95, 1.05)
                toxic_unload_total += toxic_unload_tank3
                toxic3_level += toxic_unload_total/toxic_tank_capacity
            
            # 记录当前液位（一号罐常空）
            toxic_tank2.append(round(toxic2_level, 2))
            toxic_tank3.append(round(toxic3_level, 2))
            toxic_unload.append(round(toxic_unload_total,2))
        
        return {
            'toxic_tank2': toxic_tank2,
            'toxic_tank3': toxic_tank3,
            'toxic_unload': toxic_unload,
            'corrosive_tank1': corrosive_tank1,
            'corrosive_tank2': corrosive_tank2,
            'corrosive_unload': corrosive_unload
        }
    
    def generate_tank_stock(self, tank_data):
        """生成罐区库存吨位"""
        n_total = self.total_records
        
        stocks = {}
        
        # 有毒性罐库存（吨）
        
        # 二号罐库存：液位 × 折算系数
        toxic_tank2_array = np.array(tank_data['toxic_tank2'])
        stocks['toxic_tank2_stock'] = np.round(toxic_tank2_array * 0.6475, 2).tolist()  # 51.8/80=0.6475
        
        # 三号罐库存
        toxic_tank3_array = np.array(tank_data['toxic_tank3'])
        stocks['toxic_tank3_stock'] = np.round(toxic_tank3_array * 0.6475, 2).tolist()
        
        # 腐蚀性罐库存（吨）
        corrosive_tank1_array = np.array(tank_data['corrosive_tank1'])
        corrosive_tank2_array = np.array(tank_data['corrosive_tank2'])
        stocks['corrosive_tank1_stock'] = np.round(corrosive_tank1_array * 1.5, 2).tolist()  # 密度系数1.5
        stocks['corrosive_tank2_stock'] = np.round(corrosive_tank2_array * 1.5, 2).tolist()
        
        
        return stocks

    def generate_meter_readings(self, daily_data):
        """生成流量计读数 - 根据用量大小确定精度"""
        # 起始值（运行约6个月：10吨/天 × 180天）
        # 注意：起始值是2025年1月1日07:30的读数
        start = {
            '原料A使用流量': 1802.3,      # 吨，累计值大，取整数
            '热源': 1438.9,             # 吨
            '工艺水B': 898.6,           # 吨
            '工艺水A': 1262.3,          # 吨
            '电': 83264,             # kWh
            '动力风': 367258,         # Nm³
            '保护气': 95234,          # Nm³
            '废液A累积': 546          # 吨
        }
        
        readings = {}
        for key in start:
            readings[key] = [start[key]]
            current = start[key]
            
            for i in range(len(daily_data['raw_A_total'])):
                if key == '原料A使用流量':
                    increment = daily_data['raw_A_total'][i]  
                    current += increment
                    readings[key].append(round(current, 2))  # 累计值保留二位小数
                    
                elif key == '热源':
                    increment = daily_data['steam'][i]  # 约8吨/天
                    current += increment
                    readings[key].append(round(current, 1))
                    
                elif key == '工艺水B':
                    increment = daily_data['water_B'][i]  # 约5吨/天
                    current += increment
                    readings[key].append(round(current, 1))
                    
                elif key == '工艺水A':
                    increment = daily_data['water_A'][i]  # 约7吨/天
                    current += increment
                    readings[key].append(round(current, 1))
                    
                elif key == '电':
                    increment = daily_data['power'][i]  # 约450kWh/天
                    current += int(increment)
                    readings[key].append(int(current))  # 电表取整数
                    
                elif key == '动力风':
                    increment = daily_data['air'][i]  # 约2000Nm³/天
                    current += int(increment)
                    readings[key].append(int(current))  # 整数
                    
                elif key == '保护气':
                    increment = daily_data['gas'][i]  # 约500Nm³/天
                    current += int(increment)
                    readings[key].append(int(current))  # 整数
                    
                elif key == '废液A累积':
                    increment = daily_data['waste_water'][i]  # 约3吨/天
                    current += increment
                    readings[key].append(round(current, 1))  # 保留一位小数
        
        return readings
    
    def generate_all_data(self):
        """生成所有数据"""
        print("生成日报表数据（%d天 + 白班夜班）..."%self.full_days)
        
        # 生成基础数据
        raw_data = self.generate_raw_material()
        product_data = self.generate_products(raw_data)
        medium_data = self.generate_medium(product_data)
        energy_data = self.generate_energy(product_data)
        waste_data = self.generate_waste(product_data)
        auxiliary_data = self.generate_auxiliary_material(product_data)  # 新增辅料
        tank_data = self.generate_tank_data(medium_data)  # 新增罐区液位
        stock_data = self.generate_tank_stock(tank_data)  # 新增罐区库存

        # 合并用量数据
        daily_usage = {
            'raw_A_total': raw_data['raw_A_total'],
            'steam': energy_data['steam'],
            'water_B': energy_data['water_B'],
            'water_A': energy_data['water_A'],
            'power': energy_data['power'],
            'air': energy_data['air'],
            'gas': energy_data['gas'],
            'waste_water': waste_data['waste_water']
        }
        
        # 生成流量计读数
        meter_data = self.generate_meter_readings(daily_usage)
        
        # 整理为记录
        all_records = []
        for i, date_info in enumerate(self.all_dates):
            #in)
            record = {
                '日期时间': date_info['date'],
                '班次': date_info['shift'] if date_info['shift'] else '全天',
                
                # 原料
                
                '生产A批数':raw_data['product_A_count'][i],
                '生产B批数':raw_data['product_B_count'][i],
                '原料A总消耗_吨': raw_data['raw_A_total'][i],
                
                # 介质
                '腐蚀性介质_吨': medium_data['catalyst'][i],  # 一位小数
                '有毒性介质_吨': medium_data['additive'][i],  # 两位小数
                
                # 辅料（新增）
                '产品A辅料_kg': auxiliary_data['auxiliary_A'][i],  # 整数
                '产品B辅料_kg': auxiliary_data['auxiliary_B'][i],  # 整数
                
                # 产品
                '产品A_吨': product_data['product_A'][i],  # 一位小数
                '产品B_吨': product_data['product_B'][i],  # 一位小数
                
                # 能耗
                '总热源_吨': energy_data['steam'][i],      # 一位小数
                '废液B处理热源_吨': energy_data['waste_steam'][i],  # 一位小数
                '工艺水B_吨': energy_data['water_B'][i],   # 一位小数
                '工艺水A_吨': energy_data['water_A'][i],   # 一位小数
                '电量_kWh': energy_data['power'][i],       # 整数
                '动力风_Nm³': energy_data['air'][i],       # 整数
                '保护气_Nm³': energy_data['gas'][i],       # 整数
                
                # 三废
                '雨水_吨': waste_data['rain'][i],          # 一位小数
                '废液A转移量_吨': waste_data['waste_water'][i],  # 一位小数
                '废液B排放_吨': waste_data['waste_B'][i],  # 一位小数
                '废渣_吨': waste_data['waste_solid'][i],   # 一位小数
                
                # 罐区液位 注意：这是该班次结束时的数值
                '有毒性二号罐液位_%': tank_data['toxic_tank2'][i+1],  # 一位小数
                '有毒性三号罐液位_%': tank_data['toxic_tank3'][i+1],  # 一位小数
                '腐蚀性一号罐液位_%': tank_data['corrosive_tank1'][i+1],  # 一位小数
                '腐蚀性二号罐液位_%': tank_data['corrosive_tank2'][i+1],  # 一位小数
                # 流量计读数 - 注意：这是该班次结束时的累计值
                '原料A使用流量_吨': meter_data['原料A使用流量'][i+1],  # i+1表示该班次结束后的读数
                '原料A（生产产品A用）_吨': raw_data['raw_A_to_A'][i],
                '原料A（生产产品B用）_吨': raw_data['raw_A_to_B'][i],
                '热源流量计_吨': meter_data['热源'][i+1],
                '工艺水B流量计_吨': meter_data['工艺水B'][i+1],
                '工艺水A流量计_吨': meter_data['工艺水A'][i+1],
                '电表读数_kWh': meter_data['电'][i+1],
                '动力风流量计_Nm³': meter_data['动力风'][i+1],
                '保护气流量计_Nm³': meter_data['保护气'][i+1],
                '废液A累积流量计_吨': meter_data['废液A累积'][i+1],
                # 罐区库存 注意：这是该班次结束时的数值
                '有毒性二号罐库存_吨': stock_data['toxic_tank2_stock'][i+1],  # 一位小数
                '有毒性三号罐库存_吨': stock_data['toxic_tank3_stock'][i+1],  # 一位小数
                '腐蚀性一号罐库存_吨': stock_data['corrosive_tank1_stock'][i+1],  # 一位小数
                '腐蚀性二号罐库存_吨': stock_data['corrosive_tank2_stock'][i+1],  # 一位小数           
                
                '有毒卸车':tank_data['toxic_unload'][i],
                '腐蚀卸车':tank_data['corrosive_unload'][i],
            }
            all_records.append(record)
            
        #print(len(tank_data['toxic_tank2']))
        return all_records
    
    def save_to_excel(self, all_data):
        """保存到Excel - 仅转置版"""
        df = pd.DataFrame(all_data)
        
        with pd.ExcelWriter('化工日报表数据.xlsx', engine='openpyxl') as writer:
            # 1. 全部数据（转置）
            df_transposed = df.T  # 转置数据
            df_transposed.columns = [f"record{i+1}" for i in range(len(df_transposed.columns))]
            df_transposed.to_excel(writer, sheet_name='全部数据', index=True)
            
            # 2. 按类型拆分的转置数据
            # 完整日数据
            full_data = df[df['班次'] == '全天']
            if not full_data.empty:
                full_transposed = full_data.T
                full_transposed.columns = [f"完整日记录{i+1}" for i in range(len(full_transposed.columns))]
                full_transposed.to_excel(writer, sheet_name='完整日数据', index=True)
            
            # 白班数据
            day_shift = df[df['班次'] == '白班']
            if not day_shift.empty:
                day_transposed = day_shift.T
                day_transposed.columns = [f"白班记录{i+1}" for i in range(len(day_transposed.columns))]
                day_transposed.to_excel(writer, sheet_name='2月2日白班', index=True)
            
            # 夜班数据
            night_shift = df[df['班次'] == '夜班']
            if not night_shift.empty:
                night_transposed = night_shift.T
                night_transposed.columns = [f"夜班记录{i+1}" for i in range(len(night_transposed.columns))]
                night_transposed.to_excel(writer, sheet_name='2月2日夜班', index=True)

        
        print("数据已保存到 '化工日报表数据.xlsx'")

# 运行
if __name__ == "__main__":
    generator = DailyReportGenerator()
    all_data = generator.generate_all_data()
    
    # 保存
    generator.save_to_excel(all_data)
