<template>
  <div class="map-page">
    <div class="sidebar" :class="{ collapsed: isSidebarCollapsed }">
      <div class="sidebar-header">
        <h3>线路管理</h3>
        <button class="collapse-btn" @click="toggleSidebar">
          {{ isSidebarCollapsed ? '>' : '<' }}
        </button>
      </div>
      
      <div class="sidebar-content" v-show="!isSidebarCollapsed">
        <div class="search-box">
          <input 
            v-model="searchText" 
            placeholder="搜索线路..." 
            class="search-input"
          />
        </div>
        
        <div class="section-title">线路列表</div>
        <div class="lines-list">
          <div 
            v-for="line in filteredLines" 
            :key="line.id"
            class="line-item"
            :class="{ active: activeLineId === line.id }"
            @click="selectLine(line)"
          >
            <div class="line-color" :style="{ backgroundColor: line.color }"></div>
            <div class="line-info">
              <div class="line-name">{{ line.name }}</div>
              <div class="line-stats">
                <span class="tower-count">{{ line.towers.length }}个塔</span>
                <span class="line-status" :style="{ color: getStatusColor(line.status) }">
                  {{ line.status }}
                </span>
              </div>
            </div>
          </div>
        </div>

        <div class="action-buttons">
          <button class="btn btn-primary" @click="showAllLines">
            显示所有线路
          </button>
          <button class="btn btn-secondary" @click="clearAllLines">
            清除显示
          </button>
        </div>
      </div>
    </div>

    <!-- 地图容器 -->
    <div class="map-container" :class="{ 'sidebar-collapsed': isSidebarCollapsed }">
      <div id="map" class="map"></div>
      
      <!-- 图例 -->
      <div class="map-legend">
        <div class="legend-title">节点状态图例</div>
        <div class="legend-items">
          <div class="legend-item" v-for="(text, status) in statusText" :key="status">
            <span 
              class="legend-dot" 
              :style="{ backgroundColor: statusColors[status] }"
            ></span>
            <span>{{ text }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { onMounted, onBeforeUnmount, ref, computed } from 'vue'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'

//  Leaflet 默认图标问题 
delete L.Icon.Default.prototype._getIconUrl
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.7.1/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.7.1/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.7.1/dist/images/marker-shadow.png',
})

export default {
  name: 'DandongMap',
  setup() {
    // 响应式数据
    const isSidebarCollapsed = ref(false)
    const searchText = ref('')
    const activeLineId = ref(null)
    
    // 状态颜色映射
    const statusColors = {
      completed: '#52c41a',  // 绿色
      running: '#1890ff',    // 蓝色
      pending: '#faad14',    // 黄色
      abnormal: '#ff4d4f',   // 红色
    }

    // 状态文字映射
    const statusText = {
      completed: '已完成',
      running: '进行中',
      pending: '待处理',
      abnormal: '异常',
    }

    // 线路状态颜色映射
    const lineStatusColors = {
      '运行中': '#52c41a',
      '正常运行': '#52c41a',
      '维护中': '#faad14',
      '已停用': '#999',
      '异常': '#ff4d4f'
    }

    // 线路数据
    const linesData = ref([
      {
        id: 1,
        name: '丹东主干线1',
        color: '#1890ff',
        status: '运行中',
        towers: [
          { id: 1, coordinates: [40.1291, 124.3947], status: 'completed', name: '1号塔' },
          { id: 2, coordinates: [40.1391, 124.4047], status: 'running', name: '2号塔' },
          { id: 3, coordinates: [40.1491, 124.4147], status: 'pending', name: '3号塔' },
          { id: 4, coordinates: [40.1591, 124.4247], status: 'abnormal', name: '4号塔' },
        ]
      },
      {
        id: 2,
        name: '丹东支线2',
        color: '#52c41a',
        status: '正常运行',
        towers: [
          { id: 5, coordinates: [40.1691, 124.4347], status: 'completed', name: '5号塔' },
          { id: 6, coordinates: [40.1791, 124.4447], status: 'running', name: '6号塔' },
          { id: 7, coordinates: [40.1891, 124.4547], status: 'pending', name: '7号塔' },
        ]
      },
      {
        id: 3,
        name: '开发区线路3',
        color: '#faad14',
        status: '维护中',
        towers: [
          { id: 8, coordinates: [40.1991, 124.4647], status: 'completed', name: '8号塔' },
          { id: 9, coordinates: [40.2091, 124.4747], status: 'abnormal', name: '9号塔' },
          { id: 10, coordinates: [40.2191, 124.4847], status: 'running', name: '10号塔' },
        ]
      },
      {
        id: 4,
        name: '备用线路4',
        color: '#722ed1',
        status: '已停用',
        towers: [
          { id: 11, coordinates: [40.2291, 124.4947], status: 'completed', name: '11号塔' },
          { id: 12, coordinates: [40.2391, 124.5047], status: 'completed', name: '12号塔' },
        ]
      }
    ])

    // 计算属性
    const filteredLines = computed(() => {
      if (!searchText.value) return linesData.value
      return linesData.value.filter(line => 
        line.name.toLowerCase().includes(searchText.value.toLowerCase())
      )
    })

    // Leaflet 相关变量
    let map = null
    let lineLayers = {}
    let towerLayers = {}

    // 方法
    const toggleSidebar = () => {
      isSidebarCollapsed.value = !isSidebarCollapsed.value
    }

    const getStatusColor = (status) => {
      return lineStatusColors[status] || '#999'
    }

    // 创建自定义图标 
    const createTowerIcon = (status, name) => {
      const color = statusColors[status] || '#1890ff'
      
      //  SVG 图标
      const svg = `
        <svg width="30" height="30" viewBox="0 0 30 30">
          <circle cx="15" cy="15" r="12" fill="${color}" stroke="#fff" stroke-width="3"/>
          <text x="15" y="15" text-anchor="middle" dominant-baseline="central" fill="#fff" font-size="8" font-weight="bold">${name}</text>
        </svg>
      `
      
      return L.divIcon({
        html: svg,
        className: 'tower-icon',
        iconSize: [30, 30],
        iconAnchor: [15, 15],
      })
    }

    const clearAllLayers = () => {
      Object.values(lineLayers).forEach(layer => {
        if (layer && map.hasLayer(layer)) {
          map.removeLayer(layer)
        }
      })
      Object.values(towerLayers).forEach(layer => {
        if (layer && map.hasLayer(layer)) {
          map.removeLayer(layer)
        }
      })
      lineLayers = {}
      towerLayers = {}
    }

    // 显示指定线路
    const showLine = (line) => {
      clearAllLayers()
      activeLineId.value = line.id
      
      console.log('显示线路:', line.name, '包含塔数量:', line.towers.length)

      // 创建线路
      const lineCoordinates = line.towers.map(tower => 
        L.latLng(tower.coordinates[0], tower.coordinates[1])
      )
      
      const lineLayer = L.polyline(lineCoordinates, {
        color: line.color,
        weight: 4,
        opacity: 0.8,
        dashArray: line.status === '已停用' ? '10, 5' : null,
        lineJoin: 'round'
      }).addTo(map)

      lineLayers[line.id] = lineLayer

      // 创建输电塔标记
      const towerLayer = L.layerGroup().addTo(map)
      
      line.towers.forEach(tower => {
        const { coordinates, status, name, id } = tower
        const marker = L.marker([coordinates[0], coordinates[1]], {
          icon: createTowerIcon(status, name)
        }).addTo(towerLayer)
        
        marker.bindPopup(`
          <div class="tower-popup">
            <h3>${name}</h3>
            <p><strong>线路:</strong> ${line.name}</p>
            <p><strong>ID:</strong> ${id}</p>
            <p><strong>状态:</strong> <span style="color: ${statusColors[status]}">${statusText[status]}</span></p>
            <p><strong>坐标:</strong> ${coordinates[0].toFixed(4)}, ${coordinates[1].toFixed(4)}</p>
          </div>
        `)
        
        marker.on('mouseover', function() {
          this.openPopup()
        })
        
        marker.on('mouseout', function() {
          this.closePopup()
        })
      })

      towerLayers[line.id] = towerLayer

      // 自动适配线路范围
      setTimeout(() => {
        const group = new L.featureGroup([lineLayer, towerLayer])
        map.fitBounds(group.getBounds().pad(0.1), {
          duration: 1,
          maxZoom: 12
        })
      }, 100)
    }

    // 选择线路
    const selectLine = (line) => {
      console.log('选择线路:', line.name)
      showLine(line)
    }

    // 显示所有线路
    const showAllLines = () => {
      clearAllLayers()
      activeLineId.value = null
      console.log('显示所有线路')
      
      let allFeatures = []
      
      linesData.value.forEach(line => {
        // 创建线路
        const lineCoordinates = line.towers.map(tower => 
          L.latLng(tower.coordinates[0], tower.coordinates[1])
        )
        
        const lineLayer = L.polyline(lineCoordinates, {
          color: line.color,
          weight: 3,
          opacity: 0.6,
          dashArray: line.status === '已停用' ? '5, 3' : null,
          lineJoin: 'round'
        }).addTo(map)

        lineLayers[line.id] = lineLayer
        allFeatures.push(lineLayer)

        // 创建输电塔标记
        const towerLayer = L.layerGroup().addTo(map)
        
        line.towers.forEach(tower => {
          const { coordinates, status, name, id } = tower
          const marker = L.marker([coordinates[0], coordinates[1]], {
            icon: createTowerIcon(status, name)
          }).addTo(towerLayer)
          
          marker.bindPopup(`
            <div class="tower-popup">
              <h3>${name}</h3>
              <p><strong>线路:</strong> ${line.name}</p>
              <p><strong>ID:</strong> ${id}</p>
              <p><strong>状态:</strong> <span style="color: ${statusColors[status]}">${statusText[status]}</span></p>
              <p><strong>坐标:</strong> ${coordinates[0].toFixed(4)}, ${coordinates[1].toFixed(4)}</p>
            </div>
          `)
          
          marker.on('mouseover', function() {
            this.openPopup()
          })
          
          marker.on('mouseout', function() {
            this.closePopup()
          })
        })

        towerLayers[line.id] = towerLayer
      })

      // 自动适配所有线路范围
      setTimeout(() => {
        const group = new L.featureGroup(allFeatures)
        map.fitBounds(group.getBounds().pad(0.1), {
          duration: 1,
          maxZoom: 10
        })
      }, 200)
    }

    // 清除所有线路显示
    const clearAllLines = () => {
      clearAllLayers()
      activeLineId.value = null
      console.log('清除所有线路显示')
    }

    // 初始化地图
    const initMap = () => {
      console.log('初始化地图...')
      
      const mapElement = document.getElementById('map')
      if (!mapElement) {
        console.error('地图容器未找到')
        return
      }

      // 初始化地图
      map = L.map('map').setView([40.1591, 124.4247], 11)
      console.log('地图实例创建成功')
      
      // 添加底图图层 
      L.tileLayer('https://webst01.is.autonavi.com/appmaptile?style=6&x={x}&y={y}&z={z}', {
        attribution: '© 高德地图',
        maxZoom: 18,
      }).addTo(map)

      console.log('底图加载完成，线路数据:', linesData.value)

      // 初始显示所有线路
      showAllLines()
    }

    onMounted(() => {
      console.log('组件挂载完成')
      setTimeout(() => {
        initMap()
      }, 100)
    })

    onBeforeUnmount(() => {
      if (map) {
        map.remove()
        map = null
        console.log('地图清理完成')
      }
    })

    return {
      isSidebarCollapsed,
      searchText,
      activeLineId,
      filteredLines,
      statusColors,
      statusText,
      toggleSidebar,
      selectLine,
      showAllLines,
      clearAllLines,
      getStatusColor
    }
  }
}
</script>

<style scoped>
.map-page {
  position: relative;
  width: 100vw;
  height: 100vh;
  overflow: hidden;
}

/* 侧边栏样式 */
.sidebar {
  position: absolute;
  left: 0;
  top: 0;
  width: 320px;
  height: 100%;
  background: #fff;
  box-shadow: 2px 0 8px rgba(0, 0, 0, 0.15);
  z-index: 1000;
  transition: transform 0.3s ease;
  display: flex;
  flex-direction: column;
}

.sidebar.collapsed {
  transform: translateX(-280px);
}

.sidebar-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid #f0f0f0;
  background: #fafafa;
}

.sidebar-header h3 {
  margin: 0;
  color: #1890ff;
  font-size: 16px;
  font-weight: 600;
}

.collapse-btn {
  width: 24px;
  height: 24px;
  border: none;
  background: #1890ff;
  color: white;
  border-radius: 4px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  transition: background-color 0.3s;
}

.collapse-btn:hover {
  background: #40a9ff;
}

.sidebar-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.search-box {
  padding: 16px 20px;
  border-bottom: 1px solid #f0f0f0;
}

.search-input {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #d9d9d9;
  border-radius: 4px;
  outline: none;
  transition: border-color 0.3s;
  font-size: 14px;
}

.search-input:focus {
  border-color: #1890ff;
  box-shadow: 0 0 0 2px rgba(24, 144, 255, 0.2);
}

.section-title {
  padding: 12px 20px;
  font-size: 14px;
  font-weight: 600;
  color: #666;
  background: #fafafa;
  border-bottom: 1px solid #f0f0f0;
}

.lines-list {
  flex: 1;
  overflow-y: auto;
  padding: 0;
  margin-bottom: 80px;
}

.line-item {
  display: flex;
  align-items: center;
  padding: 12px 20px;
  border-bottom: 1px solid #f5f5f5;
  cursor: pointer;
  transition: all 0.3s;
}

.line-item:hover {
  background-color: #f5f5f5;
}

.line-item.active {
  background-color: #e6f7ff;
  border-right: 3px solid #1890ff;
}

.line-color {
  width: 16px;
  height: 16px;
  border-radius: 4px;
  margin-right: 12px;
  flex-shrink: 0;
  border: 1px solid rgba(0, 0, 0, 0.1);
}

.line-info {
  flex: 1;
  min-width: 0;
}

.line-name {
  font-weight: 500;
  color: #333;
  margin-bottom: 4px;
  font-size: 14px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.line-stats {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: #666;
}

.tower-count {
  color: #999;
}

.line-status {
  font-weight: 500;
}


.action-buttons {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  padding: 16px 20px;
  background: #fff;
  border-top: 1px solid #f0f0f0;
  display: flex;
  flex-direction: column;
  gap: 8px;
  z-index: 10;
}

.btn {
  padding: 8px 16px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.3s;
}

.btn-primary {
  background: #1890ff;
  color: white;
}

.btn-primary:hover {
  background: #40a9ff;
}

.btn-secondary {
  background: #f5f5f5;
  color: #666;
  border: 1px solid #d9d9d9;
}

.btn-secondary:hover {
  background: #e6f6ff;
  color: #1890ff;
  border-color: #1890ff;
}

/* 地图容器样式 */
.map-container {
  position: absolute;
  left: 320px;
  top: 0;
  right: 0;
  bottom: 0;
  transition: left 0.3s ease;
  display: flex;
  flex-direction: column;
}

.map-container.sidebar-collapsed {
  left: 40px;
}

.map {
  flex: 1;
  background: #f5f5f5;
}

.map-legend {
  padding: 12px 20px;
  background: #fff;
  border-top: 1px solid #f0f0f0;
}

.legend-title {
  font-size: 14px;
  font-weight: 600;
  color: #333;
  margin-bottom: 8px;
}

.legend-items {
  display: flex;
  gap: 24px;
  flex-wrap: wrap;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: #333;
}

.legend-dot {
  display: inline-block;
  width: 12px;
  height: 12px;
  border-radius: 50%;
  border: 2px solid #fff;
  box-shadow: 0 0 3px rgba(0, 0, 0, 0.2);
}

/* 深度选择器 */
:deep(.tower-icon) {
  background: transparent !important;
  border: none !important;
}

:deep(.leaflet-popup-content) {
  margin: 12px 16px;
  min-width: 200px;
}

:deep(.leaflet-popup-content .tower-popup h3) {
  margin: 0 0 8px 0;
  color: #1890ff;
  font-size: 16px;
  font-weight: 600;
}

:deep(.leaflet-popup-content .tower-popup p) {
  margin: 4px 0;
  font-size: 14px;
  line-height: 1.4;
}

:deep(.leaflet-popup-tip) {
  background: #fff;
}

:deep(.leaflet-popup-content-wrapper) {
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}
</style>