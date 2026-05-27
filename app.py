import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import math

# --- 1. 网页界面基本设置 ---
st.set_page_config(page_title="香港 EV 智能调度系统", layout="wide")
st.title("⚡ 香港中环 EV 智能调度沙盘 (Demo)")

# --- 2. 侧边栏：交互控件 ---
st.sidebar.header("🚗 车辆状态面板")
# 获取当前拖动的电量值
battery_level = st.sidebar.slider("当前剩余电量 (%)", min_value=0, max_value=100, value=50, step=1)
st.sidebar.markdown("---")

# --- 3. 核心数据准备 ---
stations_data = {
    'station_name': ['IFC Mall (国际金融中心)', 'Pacific Place (太古广场)', 'Cheung Kong Center (长江集团中心)'],
    'lat': [22.2850, 22.2775, 22.2798],
    'lon': [114.1585, 114.1645, 114.1604],
    'type': ['DC Fast (快充)', 'AC Slow (慢充)', 'AC Slow (慢充)'],
    'queue_time_min': [20, 0, 5]  # IFC 排队严重，太古空闲
}
df_stations = pd.DataFrame(stations_data)
car_location = [22.277, 114.156] 

# --- 4. 【核心新增】智能调度业务逻辑 ---
best_station = None
if battery_level <= 20:
    st.sidebar.error("⚠️ 警告：电量低于 20%，正在触发智能调度...")
    
    min_cost = float('inf') # 初始设定一个无限大的成本
    
    # 遍历所有充电站，计算综合成本
    for idx, row in df_stations.iterrows():
        # 步骤A：计算直线距离 (简单的欧式距离)
        distance = math.sqrt((row['lat'] - car_location[0])**2 + (row['lon'] - car_location[1])**2)
        # 步骤B：将距离换算为预估行驶时间 (系数放大以模拟分钟数)
        driving_time_min = distance * 1500 
        # 步骤C：综合成本模型 = 行驶时间 + 站点排队时间
        total_time_cost = driving_time_min + row['queue_time_min']
        
        # 选出成本最低的站点
        if total_time_cost < min_cost:
            min_cost = total_time_cost
            best_station = row
            best_driving_time = driving_time_min

    # 在侧边栏展示决策结果
    st.sidebar.success(f"**✅ 最优推荐：{best_station['station_name']}**")
    st.sidebar.write(f"- 🚗 预估行驶时间：约 {int(best_driving_time)} 分钟")
    st.sidebar.write(f"- ⏳ 预估排队时间：{best_station['queue_time_min']} 分钟")
    st.sidebar.write(f"- 🔌 充电桩类型：{best_station['type']}")
    st.sidebar.info("💡 决策依据：虽然 IFC 距离更近，但排队时间过长，系统已为您规避拥堵节点。")
else:
    st.sidebar.success("🔋 电量健康，可继续行驶。")

# --- 5. 绘制动态地图 ---
m = folium.Map(location=[22.282, 114.161], zoom_start=15)

# 画充电站
for idx, row in df_stations.iterrows():
    # 如果是被 AI 选中的最优站点，用显眼的紫色星星标记
    if best_station is not None and row['station_name'] == best_station['station_name']:
        icon = folium.Icon(color='purple', icon='star')
    else:
        color = 'red' if 'Fast' in row['type'] else 'blue'
        icon = folium.Icon(color=color, icon='info-sign')
        
    popup_text = f"<b>{row['station_name']}</b><br>当前排队: {row['queue_time_min']} 分钟"
    folium.Marker(location=[row['lat'], row['lon']], popup=popup_text, icon=icon).add_to(m)

# 画车子
folium.Marker(
    location=car_location,
    popup=f"<b>你的电车 (当前电量 {battery_level}%)</b>",
    icon=folium.Icon(color='green', icon='car', prefix='fa')
).add_to(m)

# 【核心新增】画出导航连线
if best_station is not None:
    folium.PolyLine(
        locations=[car_location, [best_station['lat'], best_station['lon']]],
        color="red",
        weight=5,
        opacity=0.8,
        tooltip="智能调度推荐路线"
    ).add_to(m)

st_data = st_folium(m, width=900, height=500)