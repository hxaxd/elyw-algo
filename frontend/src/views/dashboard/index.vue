<template>
  <div class="dashboard-container">
    <!-- 统计卡片区域 -->
    <el-row :gutter="20" class="mgb20">
      <el-col :span="6">
        <div class="grid-content bg-purple">
          <div class="grid-content-header">
            <i class="el-icon-s-data bg-blue"></i>
            <div class="grid-content-title">任务总数</div>
          </div>
          <div class="grid-content-body">
            <div class="grid-content-number">{{ statisticsData.task_total || 0 }}</div>
            <div class="grid-content-desc">
              <span class="text-success">运行中: {{ statisticsData.task_running || 0 }}</span>
            </div>
          </div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="grid-content bg-purple">
          <div class="grid-content-header">
            <i class="el-icon-document bg-green"></i>
            <div class="grid-content-title">文件总数</div>
          </div>
          <div class="grid-content-body">
            <div class="grid-content-number">{{ statisticsData.file_total || 0 }}</div>
            <div class="grid-content-desc">
              <span class="text-success">已处理: {{ statisticsData.file_processed || 0 }}</span>
            </div>
          </div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="grid-content bg-purple">
          <div class="grid-content-header">
            <i class="el-icon-box bg-orange"></i>
            <div class="grid-content-title">容器总数</div>
          </div>
          <div class="grid-content-body">
            <div class="grid-content-number">{{ statisticsData.container_total || 0 }}</div>
            <div class="grid-content-desc">
              <span class="text-success">运行中: {{ statisticsData.container_running || 0 }}</span>
            </div>
          </div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="grid-content bg-purple">
          <div class="grid-content-header">
            <i class="el-icon-monitor bg-red"></i>
            <div class="grid-content-title">节点总数</div>
          </div>
          <div class="grid-content-body">
            <div class="grid-content-number">{{ statisticsData.node_total || 0 }}</div>
            <div class="grid-content-desc">
              <span class="text-success">在线: {{ statisticsData.node_online || 0 }}</span>
            </div>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- 图表区域 -->
    <el-row :gutter="20" class="mgb20">
      <el-col :span="12">
        <div class="chart-wrapper">
          <div class="chart-header">任务状态分布</div>
          <div class="chart-box" ref="taskStatusChart"></div>
        </div>
      </el-col>
      <el-col :span="12">
        <div class="chart-wrapper">
          <div class="chart-header">文件类型分布</div>
          <div class="chart-box" ref="fileTypeChart"></div>
        </div>
      </el-col>
    </el-row>

    <el-row :gutter="20" class="mgb20">
      <el-col :span="12">
        <div class="chart-wrapper">
          <div class="chart-header">容器状态分布</div>
          <div class="chart-box" ref="containerStatusChart"></div>
        </div>
      </el-col>
      <el-col :span="12">
        <div class="chart-wrapper">
          <div class="chart-header">节点状态分布</div>
          <div class="chart-box" ref="nodeTypeChart"></div>
        </div>
      </el-col>
    </el-row>

    <!-- 趋势图 -->
    <el-row :gutter="20">
      <el-col :span="24">
        <div class="chart-wrapper">
          <div class="chart-header">最近7天任务趋势</div>
          <div class="chart-box" ref="taskTrendChart"></div>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup name="Dashboard">
import { ref, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { getAllStatistics } from '@/api/statistics/statistics'
import * as echarts from 'echarts'

// 数据定义
const statisticsData = ref({})
const rawStatisticsData = ref({})

// 图表DOM引用
const taskStatusChart = ref(null)
const fileTypeChart = ref(null)
const containerStatusChart = ref(null)
const nodeTypeChart = ref(null)
const taskTrendChart = ref(null)

let charts = []

/**
 * 核心工具：忽略大小写匹配统计数量
 * 解决后端返回 'Running' 而前端找 'running' 导致的 0 数据问题
 */
const getCount = (list, keyName, value) => {
  if (!list || !Array.isArray(list)) return 0
  const valStr = String(value).toLowerCase()
  // 查找匹配项
  const target = list.find(item => String(item[keyName]).toLowerCase() === valStr)
  return target ? target.count : 0
}

const fetchStatistics = async () => {
  try {
    const res = await getAllStatistics()
    console.log('完整API响应:', res)

    // 解析逻辑：根据实际响应数据结构进行解析
    let finalData = null
    
    // 根据您提供的实际响应数据，res应该包含code、msg、data等字段
    if (res && res.data && typeof res.data === 'object') {
      // 标准结构，res.data包含统计数据
      finalData = res.data
    } else if (res && res.tasks) {
      // 如果res直接包含tasks，说明已经是解包后的数据
      finalData = res
    }
    
    if (!finalData) {
      console.warn('收到响应但数据格式不匹配，无法解析:', res)
      return
    }

    rawStatisticsData.value = finalData
    
    // 将后端数据映射到前端变量 (使用 getCount 容错)
    statisticsData.value = {
      // 1. 任务
      task_total: finalData.tasks?.total || 0,
      task_running: getCount(finalData.tasks?.by_status, 'status', 'running'),
      task_completed: getCount(finalData.tasks?.by_status, 'status', 'completed') || getCount(finalData.tasks?.by_status, 'status', 'success'),
      task_failed: getCount(finalData.tasks?.by_status, 'status', 'failed'),
      
      // 2. 文件
      file_total: finalData.files?.total || 0,
      file_processed: getCount(finalData.files?.by_root, 'root', 'processed'),
      
      // 3. 容器 (后端现在返回 by_status)
      container_total: finalData.containers?.total || 0,
      container_running: getCount(finalData.containers?.by_status, 'status', 'running'),
      container_stopped: getCount(finalData.containers?.by_status, 'status', 'stopped') || getCount(finalData.containers?.by_status, 'status', 'exited'),
      
      // 4. 节点
      node_total: finalData.nodes?.total || 0,
      node_online: getCount(finalData.nodes?.by_status, 'status', 'online') || getCount(finalData.nodes?.by_status, 'status', '健康')
    }

    console.log('解析后的展示数据:', statisticsData.value)

    nextTick(() => {
      initCharts()
    })
    
  } catch (error) {
    console.error('获取统计数据失败:', error)
  }
}

// 统一图表初始化
const initCharts = () => {
  charts.forEach(c => c.dispose()) // 清理旧图表
  charts = []

  // 1. 任务状态 (圆环图)
  createPieChart(
    taskStatusChart, 
    '任务状态', 
    rawStatisticsData.value.tasks?.by_status, 
    'status'
  )

  // 2. 文件类型 (圆环图)
  createPieChart(
    fileTypeChart, 
    '文件类型', 
    rawStatisticsData.value.files?.by_type, 
    'type',
    // 自定义格式化函数，处理特殊文件类型
    (name) => {
      if (name === 'image') return '图片'
      if (name === 'file') return '文件'
      if (name === 'dir') return '目录'
      return name
    }
  )

  // 3. 容器状态 (圆环图)
  createPieChart(
    containerStatusChart, 
    '容器状态', 
    rawStatisticsData.value.containers?.by_status, 
    'status'
  )

  // 4. 节点状态 (圆环图)
  createPieChart(
    nodeTypeChart, 
    '节点状态', 
    rawStatisticsData.value.nodes?.by_status, 
    'status'
  )

  // 5. 趋势图 (折线图)
  if (taskTrendChart.value) {
    const chart = echarts.init(taskTrendChart.value)
    const trendData = rawStatisticsData.value.tasks?.by_date || []
    
    chart.setOption({
      tooltip: { trigger: 'axis' },
      grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
      xAxis: { 
        type: 'category', 
        boundaryGap: false, 
        data: trendData.map(i => i.date) 
      },
      yAxis: { type: 'value' },
      series: [{
        name: '任务量',
        type: 'line',
        smooth: true,
        areaStyle: { opacity: 0.2, color: '#409EFF' },
        itemStyle: { color: '#409EFF' },
        data: trendData.map(i => i.count)
      }]
    })
    charts.push(chart)
  }
}

// 创建饼图的通用函数
const createPieChart = (domRef, title, dataList, nameKey, customFormatter) => {
  if (!domRef.value) return
  const chart = echarts.init(domRef.value)
  
  // 转换数据格式
  const seriesData = (dataList || []).map(item => ({
    value: item.count,
    name: item[nameKey] || '未知'
  }))

  // 默认格式化函数
  const defaultFormatter = function(name) {
    // 对特殊状态值进行友好显示
    if (name === 'None') return '离线'
    if (name === '') return '未知状态'
    if (name === 'image') return '图片'
    if (name === 'file') return '文件'
    if (name === 'dir') return '目录'
    return name
  }

  // 使用自定义格式化函数或默认格式化函数
  const formatter = customFormatter || defaultFormatter

  chart.setOption({
    tooltip: { 
      trigger: 'item',
      formatter: '{a} <br/>{b}: {c} ({d}%)'
    },
    legend: { 
      bottom: 0, 
      left: 'center',
      formatter: formatter
    },
    series: [{
      name: title,
      type: 'pie',
      radius: ['40%', '70%'],
      avoidLabelOverlap: false,
      itemStyle: { borderRadius: 10, borderColor: '#fff', borderWidth: 2 },
      label: { 
        show: true,
        formatter: function(params) {
          // 对特殊状态值进行友好显示
          let name = formatter(params.name)
          return `${name}: ${params.value}`
        }
      },
      emphasis: { label: { show: true, fontSize: 14, fontWeight: 'bold' } },
      data: seriesData.length ? seriesData : [{value: 0, name: '暂无数据'}]
    }]
  })
  charts.push(chart)
}

const resizeHandler = () => charts.forEach(c => c.resize())

onMounted(() => {
  fetchStatistics()
  window.addEventListener('resize', resizeHandler)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', resizeHandler)
  charts.forEach(c => c.dispose())
})
</script>

<style lang="scss" scoped>
.dashboard-container {
  padding: 20px;
  background-color: #f0f2f5;
  min-height: calc(100vh - 84px);

  .mgb20 { margin-bottom: 20px; }

  .grid-content {
    display: flex;
    align-items: center;
    height: 100px;
    background: #fff;
    border-radius: 4px;
    padding: 0 20px;
    box-shadow: 0 2px 12px 0 rgba(0,0,0,.1);

    .grid-content-header {
      display: flex;
      flex-direction: column;
      align-items: center;
      margin-right: 20px;
      i { font-size: 30px; margin-bottom: 10px; padding: 10px; border-radius: 6px; color: #fff; }
      .grid-content-title { font-size: 14px; color: #666; }
      .bg-blue { background: #409EFF; }
      .bg-green { background: #67C23A; }
      .bg-orange { background: #E6A23C; }
      .bg-red { background: #F56C6C; }
    }

    .grid-content-body {
      flex: 1;
      display: flex;
      flex-direction: column;
      justify-content: center;
      .grid-content-number { font-size: 24px; font-weight: bold; color: #333; margin-bottom: 5px; }
      .grid-content-desc { font-size: 13px; color: #999; .text-success { color: #67C23A; } }
    }
  }

  .chart-wrapper {
    background: #fff;
    padding: 16px 16px 0;
    margin-bottom: 32px;
    border-radius: 4px;
    box-shadow: 0 2px 12px 0 rgba(0,0,0,.1);
    .chart-header { font-size: 16px; font-weight: bold; color: #333; margin-bottom: 15px; padding-left: 10px; border-left: 4px solid #409EFF; }
    .chart-box { height: 300px; width: 100%; }
  }
}
</style>