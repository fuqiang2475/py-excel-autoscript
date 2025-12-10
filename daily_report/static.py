class LiquidLevelValidator:
    def __init__(self):
        pass

    def validate_input(self, input_value):
        """输入处理与验证核心逻辑"""
        if not isinstance(input_value, (int, float)):
            raise ValueError("有毒性罐液位数据非浮点数")

        if not (0 < input_value <= 100):
            raise ValueError("有毒性罐液位数据异常")

        return round(input_value, 0) if input_value >= 1 else 1

    def get_tonnage(self, processed_level):
        """精确查询核心算法"""
        x = processed_level
        #拟合的估算函数，已脱敏
        return round(0.6475 * x,2)