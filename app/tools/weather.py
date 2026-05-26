def get_weather(city: str) -> str:
    mock_weather = {
        "北京": "北京今天晴，温度 25°C",
        "上海": "上海今天多云，温度 27°C",
        "广州": "广州今天有小雨，温度 29°C",
        "深圳": "深圳今天晴，温度 28°C",
    }

    return mock_weather.get(city, f"暂时没有 {city} 的天气数据")