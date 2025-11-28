<template>
  <div class="dashboard-container">
    <!-- 页面头部 - 用户信息 -->
    <div class="pageHeaderContent">
      <div class="avatar">
        <a-avatar size="large" :src="currentUser.avatar" />
      </div>
      <div class="content">
        <div class="contentTitle">
          早安，{{ currentUser.name }}，祝你开心每一天！
        </div>
        <div>{{ currentUser.title }} | {{ currentUser.group }}</div>
      </div>
    </div>

    <!-- 统计数据看板 -->
    <div class="statistics-board">
      <a-row :gutter="16">
        <a-col :xs="24" :sm="12" :md="6">
          <div class="stat-card">
            <div class="stat-icon" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);">
              <FileTextOutlined />
            </div>
            <div class="stat-content">
              <div class="stat-label">任务总量</div>
              <div class="stat-value">{{ totalTasks }}</div>
              <div class="stat-trend">
                <CaretUpOutlined style="color: #52c41a" />
                <span style="color: #52c41a">12.5%</span>
                <span class="stat-desc">较昨日</span>
              </div>
            </div>
          </div>
        </a-col>
        <a-col :xs="24" :sm="12" :md="6">
          <div class="stat-card">
            <div class="stat-icon" style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);">
              <CheckCircleOutlined />
            </div>
            <div class="stat-content">
              <div class="stat-label">完成率</div>
              <div class="stat-value">{{ completionRate }}%</div>
              <div class="stat-trend">
                <CaretUpOutlined style="color: #52c41a" />
                <span style="color: #52c41a">3.2%</span>
                <span class="stat-desc">较昨日</span>
              </div>
            </div>
          </div>
        </a-col>
        <a-col :xs="24" :sm="12" :md="6">
          <div class="stat-card">
            <div class="stat-icon" style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);">
              <AppstoreOutlined />
            </div>
            <div class="stat-content">
              <div class="stat-label">识别部件总数</div>
              <div class="stat-value">{{ recognizedParts }}</div>
              <div class="stat-trend">
                <CaretUpOutlined style="color: #52c41a" />
                <span style="color: #52c41a">8.7%</span>
                <span class="stat-desc">较昨日</span>
              </div>
            </div>
          </div>
        </a-col>
        <a-col :xs="24" :sm="12" :md="6">
          <div class="stat-card">
            <div class="stat-icon" style="background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);">
              <AimOutlined />
            </div>
            <div class="stat-content">
              <div class="stat-label">缺陷检测准确率</div>
              <div class="stat-value">{{ detectionAccuracy }}%</div>
              <div class="stat-trend">
                <CaretUpOutlined style="color: #52c41a" />
                <span style="color: #52c41a">1.5%</span>
                <span class="stat-desc">较昨日</span>
              </div>
            </div>
          </div>
        </a-col>
      </a-row>
    </div>

    <!-- 主体内容区 -->
    <div class="content-area">
      <a-row :gutter="24">
        <!-- 左侧：关键指标仪表盘 -->
        <a-col :xs="24" :lg="10">
          <a-card title="关键指标仪表盘" :bordered="false" class="dashboard-card">
            <div ref="gaugeChartContainer" style="width: 100%; height: 400px;"></div>
          </a-card>

          <a-card 
            title="任务状态分布" 
            :bordered="false" 
            class="dashboard-card" 
            style="margin-top: 24px;"
          >
            <div ref="pieChartContainer" style="width: 100%; height: 300px;"></div>
          </a-card>
        </a-col>

        <!-- 右侧：趋势图和平台数据 -->
        <a-col :xs="24" :lg="14">
          <a-card :bordered="false" class="dashboard-card">
            <template #title>
              <div class="card-title-wrapper">
                <span>平台关键指标趋势（过去24小时）</span>
                <a-radio-group v-model:value="timeRange" size="small" style="margin-left: 16px;">
                  <a-radio-button value="24h">24小时</a-radio-button>
                  <a-radio-button value="7d">7天</a-radio-button>
                  <a-radio-button value="30d">30天</a-radio-button>
                </a-radio-group>
              </div>
            </template>
            <div ref="trendChartContainer" style="width: 100%; height: 400px;"></div>
          </a-card>

          <a-card 
            title="实时处理性能" 
            :bordered="false" 
            class="dashboard-card"
            style="margin-top: 24px;"
          >
            <div ref="barChartContainer" style="width: 100%; height: 300px;"></div>
          </a-card>
        </a-col>
      </a-row>

      
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, watch } from 'vue';
import * as echarts from 'echarts';
import {
  FileTextOutlined,
  CheckCircleOutlined,
  AppstoreOutlined,
  AimOutlined,
  CaretUpOutlined,
} from '@ant-design/icons-vue';

defineOptions({
  name: "DashBoard",
});

// 用户信息
const currentUser = {
  avatar: "https://gw.alipayobjects.com/zos/rmsportal/BiazfanxmamNRoxxVxka.png",
  name: "系统管理员",
  title: "AI检测专家",
  group: "电力巡检事业群－智能检测平台部－算法开发组",
};

// 统计数据
const totalTasks = ref(1234);
const completionRate = ref(95.6);
const recognizedParts = ref(5678);
const detectionAccuracy = ref(98.2);
const timeRange = ref('24h');

// 进行中的任务
const runningTasks = [
  {
    id: "task1",
    title: "高压线路关键部件识别任务",
    logo: "https://gw.alipayobjects.com/zos/rmsportal/WdGqmHpayyMjiEhcKoVE.png",
    description: "针对复杂背景下的金具识别与定位，实时处理巡检图像",
    progress: 75,
    updatedAt: "2分钟前",
    member: "巡检算法组",
  },
  {
    id: "task2",
    title: "缺陷检测批量任务",
    logo: "https://gw.alipayobjects.com/zos/rmsportal/zOsKZmFRdUtvpqCImOVY.png",
    description: "使用深度学习模型检测绝缘子缺陷，支持多图像输入",
    progress: 45,
    updatedAt: "10分钟前",
    member: "模型部署组",
  },
  {
    id: "task3",
    title: "遥感数据预处理任务",
    logo: "https://gw.alipayobjects.com/zos/rmsportal/dURIMkkrRFpPgTuzkwnB.png",
    description: "图像增强与标注，准备用于后续识别与检测",
    progress: 90,
    updatedAt: "5分钟前",
    member: "数据管理组",
  },
  {
    id: "task4",
    title: "算力平台优化任务",
    logo: "https://gw.alipayobjects.com/zos/rmsportal/sfjbOqnsXXJgNCjCzDBL.png",
    description: "GPU资源调度与模型推理加速",
    progress: 60,
    updatedAt: "15分钟前",
    member: "运维组",
  },
  {
    id: "task5",
    title: "报警规则验证任务",
    logo: "https://gw.alipayobjects.com/zos/rmsportal/siCrBXXhmvTQGWPNLBow.png",
    description: "模拟缺陷场景下的报警触发测试",
    progress: 30,
    updatedAt: "20分钟前",
    member: "测试组",
  },
  {
    id: "task6",
    title: "模型性能评估任务",
    logo: "https://gw.alipayobjects.com/zos/rmsportal/kZzEzemZyKLKFsojXItE.png",
    description: "对新部署模型进行准确率和速度评估",
    progress: 85,
    updatedAt: "8分钟前",
    member: "算法开发组",
  },
];

// 系统


// ECharts 图表实例
const gaugeChartContainer = ref();
const trendChartContainer = ref();
const pieChartContainer = ref();
const barChartContainer = ref();

let gaugeChart, trendChart, pieChart, barChart;

// 初始化仪表盘图表
const initGaugeChart = () => {
  gaugeChart = echarts.init(gaugeChartContainer.value);
  
  const option = {
    series: [
      {
        type: 'gauge',
        center: ['25%', '50%'],
        radius: '80%',
        startAngle: 225,
        endAngle: -45,
        min: 0,
        max: 100,
        axisLine: {
          lineStyle: {
            width: 20,
            color: [
              [0.6, '#ff4d4f'],
              [0.8, '#faad14'],
              [1, '#52c41a']
            ]
          }
        },
        pointer: {
          itemStyle: {
            color: 'auto'
          }
        },
        axisTick: {
          distance: -20,
          length: 5,
          lineStyle: {
            color: '#fff',
            width: 1
          }
        },
        splitLine: {
          distance: -20,
          length: 20,
          lineStyle: {
            color: '#fff',
            width: 2
          }
        },
        axisLabel: {
          distance: 15,
          color: 'auto',
          fontSize: 12
        },
        detail: {
          valueAnimation: true,
          formatter: '{value}%',
          color: 'auto',
          fontSize: 20,
          offsetCenter: [0, '70%']
        },
        title: {
          offsetCenter: [0, '90%'],
          fontSize: 14
        },
        data: [
          {
            value: completionRate.value,
            name: '任务完成率'
          }
        ]
      },
      {
        type: 'gauge',
        center: ['75%', '50%'],
        radius: '80%',
        startAngle: 225,
        endAngle: -45,
        min: 0,
        max: 100,
        axisLine: {
          lineStyle: {
            width: 20,
            color: [
              [0.9, '#faad14'],
              [0.95, '#52c41a'],
              [1, '#1890ff']
            ]
          }
        },
        pointer: {
          itemStyle: {
            color: 'auto'
          }
        },
        axisTick: {
          distance: -20,
          length: 5,
          lineStyle: {
            color: '#fff',
            width: 1
          }
        },
        splitLine: {
          distance: -20,
          length: 20,
          lineStyle: {
            color: '#fff',
            width: 2
          }
        },
        axisLabel: {
          distance: 15,
          color: 'auto',
          fontSize: 12
        },
        detail: {
          valueAnimation: true,
          formatter: '{value}%',
          color: 'auto',
          fontSize: 20,
          offsetCenter: [0, '70%']
        },
        title: {
          offsetCenter: [0, '90%'],
          fontSize: 14
        },
        data: [
          {
            value: detectionAccuracy.value,
            name: '检测准确率'
          }
        ]
      }
    ]
  };
  
  gaugeChart.setOption(option);
};

// 初始化趋势图表
const initTrendChart = () => {
  trendChart = echarts.init(trendChartContainer.value);
  
  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'cross'
      }
    },
    legend: {
      data: ['处理图像数量', '平均响应时间(s)', '错误率(%)']
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: ['00:00', '02:00', '04:00', '06:00', '08:00', '10:00', '12:00', 
             '14:00', '16:00', '18:00', '20:00', '22:00', '24:00']
    },
    yAxis: [
      {
        type: 'value',
        name: '数量',
        position: 'left',
        axisLabel: {
          formatter: '{value}'
        }
      },
      {
        type: 'value',
        name: '时间/错误率',
        position: 'right',
        axisLabel: {
          formatter: '{value}'
        }
      }
    ],
    series: [
      {
        name: '处理图像数量',
        type: 'line',
        smooth: true,
        data: [120, 140, 150, 180, 210, 250, 280, 300, 290, 270, 240, 200, 180],
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(24, 144, 255, 0.3)' },
            { offset: 1, color: 'rgba(24, 144, 255, 0.05)' }
          ])
        },
        itemStyle: {
          color: '#1890ff'
        }
      },
      {
        name: '平均响应时间(s)',
        type: 'line',
        smooth: true,
        yAxisIndex: 1,
        data: [2.1, 2.0, 1.9, 2.2, 2.5, 2.3, 2.1, 1.8, 1.9, 2.0, 2.1, 2.2, 2.3],
        itemStyle: {
          color: '#52c41a'
        }
      },
      {
        name: '错误率(%)',
        type: 'line',
        smooth: true,
        yAxisIndex: 1,
        data: [1.2, 1.1, 0.9, 1.3, 1.5, 1.2, 1.0, 0.8, 0.9, 1.1, 1.2, 1.3, 1.4],
        itemStyle: {
          color: '#ff4d4f'
        }
      }
    ]
  };
  
  trendChart.setOption(option);
};

// 初始化饼图
const initPieChart = () => {
  pieChart = echarts.init(pieChartContainer.value);
  
  const option = {
    tooltip: {
      trigger: 'item',
      formatter: '{a} <br/>{b}: {c} ({d}%)'
    },
    legend: {
      orient: 'vertical',
      left: 'left'
    },
    series: [
      {
        name: '任务状态',
        type: 'pie',
        radius: ['40%', '70%'],
        avoidLabelOverlap: false,
        itemStyle: {
          borderRadius: 10,
          borderColor: '#fff',
          borderWidth: 2
        },
        label: {
          show: false,
          position: 'center'
        },
        emphasis: {
          label: {
            show: true,
            fontSize: 20,
            fontWeight: 'bold'
          }
        },
        labelLine: {
          show: false
        },
        data: [
          { value: 580, name: '已完成', itemStyle: { color: '#52c41a' } },
          { value: 320, name: '进行中', itemStyle: { color: '#1890ff' } },
          { value: 234, name: '待处理', itemStyle: { color: '#faad14' } },
          { value: 100, name: '已失败', itemStyle: { color: '#ff4d4f' } }
        ]
      }
    ]
  };
  
  pieChart.setOption(option);
};

// 初始化柱状图
const initBarChart = () => {
  barChart = echarts.init(barChartContainer.value);
  
  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'shadow'
      }
    },
    legend: {
      data: ['图像识别', '缺陷检测', '数据预处理']
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: ['00:00', '04:00', '08:00', '12:00', '16:00', '20:00', '24:00']
    },
    yAxis: {
      type: 'value',
      name: '处理时间(ms)'
    },
    series: [
      {
        name: '图像识别',
        type: 'bar',
        data: [120, 132, 101, 134, 90, 130, 110],
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: '#83bff6' },
            { offset: 1, color: '#188df0' }
          ])
        }
      },
      {
        name: '缺陷检测',
        type: 'bar',
        data: [220, 182, 191, 234, 290, 330, 310],
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: '#95de64' },
            { offset: 1, color: '#52c41a' }
          ])
        }
      },
      {
        name: '数据预处理',
        type: 'bar',
        data: [150, 232, 201, 154, 190, 230, 210],
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: '#ffd666' },
            { offset: 1, color: '#faad14' }
          ])
        }
      }
    ]
  };
  
  barChart.setOption(option);
};

// 窗口大小调整处理
const handleResize = () => {
  gaugeChart?.resize();
  trendChart?.resize();
  pieChart?.resize();
  barChart?.resize();
};

// 监听时间范围变化
watch(timeRange, (newVal) => {
  console.log('时间范围切换：', newVal);
  // 这里可以根据时间范围重新加载数据
});

onMounted(() => {
  initGaugeChart();
  initTrendChart();
  initPieChart();
  initBarChart();
  
  window.addEventListener('resize', handleResize);
});

onBeforeUnmount(() => {
  gaugeChart?.dispose();
  trendChart?.dispose();
  pieChart?.dispose();
  barChart?.dispose();
  window.removeEventListener('resize', handleResize);
});
</script>

<style scoped lang="less">
.dashboard-container {
  background: #f0f2f5;
  min-height: 100vh;
  padding: 24px;
}

.pageHeaderContent {
  display: flex;
  padding: 24px;
  margin-bottom: 24px;
  background: #fff;
  border-radius: 4px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);

  .avatar {
    flex: 0 0 72px;
  }

  .content {
    flex: 1;
    margin-left: 24px;

    .contentTitle {
      margin-bottom: 12px;
      color: rgba(0, 0, 0, 0.85);
      font-weight: 500;
      font-size: 20px;
      line-height: 28px;
    }

    div:last-child {
      color: rgba(0, 0, 0, 0.45);
      line-height: 22px;
    }
  }
}

.statistics-board {
  margin-bottom: 24px;

  .stat-card {
    display: flex;
    align-items: center;
    padding: 24px;
    background: #fff;
    border-radius: 8px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
    transition: all 0.3s;

    &:hover {
      transform: translateY(-4px);
      box-shadow: 0 4px 16px rgba(0, 0, 0, 0.12);
    }

    .stat-icon {
      display: flex;
      align-items: center;
      justify-content: center;
      width: 64px;
      height: 64px;
      border-radius: 12px;
      font-size: 32px;
      color: #fff;
      margin-right: 16px;
    }

    .stat-content {
      flex: 1;

      .stat-label {
        color: rgba(0, 0, 0, 0.45);
        font-size: 14px;
        margin-bottom: 8px;
      }

      .stat-value {
        color: rgba(0, 0, 0, 0.85);
        font-size: 28px;
        font-weight: 600;
        line-height: 1;
        margin-bottom: 8px;
      }

      .stat-trend {
        display: flex;
        align-items: center;
        gap: 4px;
        font-size: 12px;

        .stat-desc {
          color: rgba(0, 0, 0, 0.45);
        }
      }
    }
  }
}

.content-area {
  .dashboard-card {
    border-radius: 4px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);

    :deep(.ant-card-head) {
      border-bottom: 1px solid #f0f0f0;
    }

    .card-title-wrapper {
      display: flex;
      align-items: center;
      justify-content: space-between;
    }
  }
}

.resource-item {
  margin-bottom: 24px;

  &:last-child {
    margin-bottom: 0;
  }

  .resource-label {
    display: flex;
    align-items: center;
    margin-bottom: 8px;
    color: rgba(0, 0, 0, 0.65);
    font-size: 14px;
  }
}

.quick-nav {
  :deep(.ant-btn) {
    height: 40px;
    font-size: 14px;
  }
}

.projectList {
  :deep(.ant-card-meta-description) {
    height: 44px;
    overflow: hidden;
    color: rgba(0, 0, 0, 0.45);
    line-height: 22px;
  }

  .cardTitle {
    font-size: 0;

    a {
      display: inline-block;
      height: 24px;
      margin-left: 12px;
      color: rgba(0, 0, 0, 0.85);
      font-size: 14px;
      line-height: 24px;
      vertical-align: top;

      &:hover {
        color: #1890ff;
      }
    }
  }

  .projectGrid {
    width: 33.33%;
    padding: 24px;
  }

  .projectItemContent {
    margin-top: 12px;

    .datetime {
      color: rgba(0, 0, 0, 0.45);
      font-size: 12px;
    }
  }
}

.activeCard {
  .activitiesList {
    padding: 0 24px 8px;

    .username {
      color: rgba(0, 0, 0, 0.85);
      font-weight: 500;
    }

    .event {
      color: rgba(0, 0, 0, 0.65);
    }

    .datetime {
      color: rgba(0, 0, 0, 0.25);
      font-size: 12px;
    }
  }
}

@media screen and (max-width: 768px) {
  .projectList .projectGrid {
    width: 50%;
  }
}

@media screen and (max-width: 576px) {
  .dashboard-container {
    padding: 12px;
  }

  .pageHeaderContent {
    flex-direction: column;

    .content {
      margin-left: 0;
      margin-top: 16px;
    }
  }

  .projectList .projectGrid {
    width: 100%;
  }
}
</style>
