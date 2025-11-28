<template>
  <div class="section">
    <div class="section-header">
      <h2 class="section-title">模型管理</h2>
      <div class="operation-buttons">
        <el-button type="primary" @click="addModel1">新增模型</el-button>
        <el-button type="success" @click="getRunLogs">获取运行日志</el-button>
        <el-button type="warning" @click="getRunningTasks">获取运行任务</el-button>
      </div>
    </div>
    
    <div class="search-area">
      <el-input
        v-model="modelSearch"
        placeholder="搜索模型名称或类型"
        clearable
        style="width: 300px"
      >
        <template #append>
          <el-button :icon="SearchIcon" @click="searchModels" />
        </template>
      </el-input>
    </div>
    
    <div class="data-table">
      <el-table :data="filteredModels" stripe style="width: 100%" v-loading="loading">
        <el-table-column prop="model_name" label="模型名称" width="180" />
        <el-table-column prop="type" label="模型类型" width="120" />
        <el-table-column prop="version" label="版本" width="100" />
        <el-table-column prop="intro" label="描述" />
        <el-table-column label="操作" width="180">
          <template #default="scope">
            <el-button size="small" @click="editModel(scope.row)">编辑</el-button>
            <el-button size="small" type="danger" @click="deleteModel(scope.row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>
    
    <div class="pagination">
      <el-pagination
        v-model:current-page="modelCurrentPage"
        v-model:page-size="modelPageSize"
        :page-sizes="[5, 10, 20]"
        :total="models.length"
        layout="total, sizes, prev, pager, next"
      />
    </div>
    
    <!-- 运行日志显示区域 -->
    <div v-if="showLogs" class="log-container">
      <div class="log-header">
        <h3>运行日志</h3>
        <el-button type="primary" size="small" @click="getRunLogs">刷新日志</el-button>
      </div>
      <div class="log-content">
        <div v-if="logsLoading" class="loading">加载中...</div>
        <div v-else-if="logs.length === 0" class="no-data">暂无日志数据</div>
        <div v-else v-for="(log, index) in logs" :key="index" class="log-line">{{ log }}</div>
      </div>
    </div>
    
    <!-- 运行任务显示区域 -->
    <div v-if="showTasks" class="log-container">
      <div class="log-header">
        <h3>运行中的任务</h3>
        <el-button type="primary" size="small" @click="getRunningTasks">刷新任务</el-button>
      </div>
      <div class="task-list">
        <div v-if="tasksLoading" class="loading">加载中...</div>
        <div v-else-if="runningTasks.length === 0" class="no-data">暂无运行中的任务</div>
        <div v-else v-for="task in runningTasks" :key="task.id" class="task-item">
          <div class="task-info">
            <div class="task-name">{{ task.name || '未命名任务' }}</div>
            <div class="task-id">任务ID: {{ task.id }}</div>
          </div>
          <div class="task-progress">
            <el-progress :percentage="task.progress || 0" />
          </div>
          <div class="task-status">
            <el-tag :type="getStatusType(task.status)">{{ task.status || '未知' }}</el-tag>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 模型编辑/添加对话框 -->
    <el-dialog
      v-model="modelDialogVisible"
      :title="isEditingModel ? '编辑模型' : '新增模型'"
      width="500px"
    >
      <el-form :model="currentModel" label-width="80px">
        <el-form-item label="容器ID">
          <el-input v-model="currentModel.container_id" disabled />
        </el-form-item>
        <el-form-item label="模型名称">
          <el-input v-model="currentModel.model_name" />
        </el-form-item>
        <el-form-item label="模型描述">
          <el-input v-model="currentModel.intro" type="textarea" :rows="3" />
        </el-form-item>
        <el-form-item label="模型文件" v-if="!isEditingModel">
          <el-upload
            ref="uploadRef"
            :auto-upload="false"
            :limit="1"
            :on-change="handleFileChange"
            :on-remove="handleFileRemove"
          >
            <el-button size="small" type="primary">点击上传</el-button>
            <template #tip>
              <div class="el-upload__tip">请上传模型文件</div>
            </template>
          </el-upload>
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="modelDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="saveModel" :loading="saveLoading">保存</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import { ref, computed, onMounted, watch, nextTick, getCurrentInstance } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { addModel, getLog, getTasking, listModel, delModel } from '@/api/container/container'

const SearchIcon = {
  template: '<svg viewBox="0 0 1024 1024" xmlns="http://www.w3.org/2000/svg" width="14" height="14"><path d="M909.6 854.5L649.9 594.8C690.2 542.7 712 479 712 412c0-80.2-31.3-155.4-87.9-212.1-56.6-56.7-132-87.9-212.1-87.9s-155.5 31.3-212.1 87.9C143.2 256.5 112 331.8 112 412c0 80.1 31.3 155.5 87.9 212.1C256.5 680.8 331.8 712 412 712c67 0 130.6-21.8 182.7-62l259.7 259.6a8.2 8.2 0 0 0 11.6 0l43.6-43.5a8.2 8.2 0 0 0 0-11.6zM570.4 570.4C528 612.7 471.8 636 412 636s-116-23.3-158.4-65.6C211.3 528 188 471.8 188 412s23.3-116.1 65.6-158.4C296 211.3 352.2 188 412 188s116.1 23.2 158.4 65.6S636 352.2 636 412s-23.3 116.1-65.6 158.4z" fill="currentColor"></path></svg>'
}

export default {
  name: 'ModelManagement',
  props: {
    containerId: {
      type: Number,
      required: true
    }
  },
  setup(props) {
    const { proxy } = getCurrentInstance();

    const models = ref([])
    const loading = ref(false)
    const saveLoading = ref(false)
    const modelSearch = ref('')
    const modelCurrentPage = ref(1)
    const modelPageSize = ref(5)
    const modelDialogVisible = ref(false)
    const isEditingModel = ref(false)

    const currentModel = ref({
      model_name: '',
      intro: '',
      file: null,
      container_id: props.containerId,
    })
 
    const uploadRef = ref(null)

    const showLogs = ref(false)
    const showTasks = ref(false)
    const logs = ref([])
    const runningTasks = ref([])
    const logsLoading = ref(false)
    const tasksLoading = ref(false)

    const filteredModels = computed(() => {
      let result = Array.isArray(models.value) ? models.value : []

      if (modelSearch.value) {
        const search = modelSearch.value.toLowerCase()
        result = result.filter(item => 
          item && item.model_name && item.model_name.toLowerCase().includes(search) || 
          item && item.type && item.type.toLowerCase().includes(search)
        )
      }

      const start = (modelCurrentPage.value - 1) * modelPageSize.value
      const end = start + modelPageSize.value
      return result.slice(start, end)
    })
    
    onMounted(() => {
      getList();
    });

    watch(() => props.containerId, (newVal, oldVal) => {
      if (newVal !== oldVal) {
        getList();
      }
    });
    
    const handleFileChange = (file) => {
      currentModel.value.file = file.raw
    }
    
    const handleFileRemove = () => {
      currentModel.value.file = null
    }
    
    // 模型操作方法
    const addModel1 = () => {
      currentModel.value = {
        model_name: '',
        intro: '',
        file: null,
        container_id: props.containerId,
      }
      isEditingModel.value = false
      modelDialogVisible.value = true

      nextTick(() => {
        if (uploadRef.value) {
          uploadRef.value.clearFiles()
        }
      })
    }
    
    const editModel = (model) => {
      currentModel.value = { 
        ...model,
        file: null 
      }
      isEditingModel.value = true
      modelDialogVisible.value = true
      nextTick(() => {
        if (uploadRef.value) {
          uploadRef.value.clearFiles()
        }
      })
    }
    
 const deleteModel = (model) => {
  ElMessageBox.confirm(
    `确定要删除模型 "${model.model_name || model.algo_name}" 吗？`,
    '警告',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    }
  ).then(() => {
    const modelNameToDelete = model.model_name || model.algo_name
    console.log('🗑️ 开始删除模型:', {
      containerId: props.containerId,
      modelName: modelNameToDelete,
      modelData: model
    })
    

    delModel(props.containerId, modelNameToDelete).then(response => {
      console.log('✅ 删除模型成功:', response)
      ElMessage.success('删除成功')
      getList() 
    }).catch(error => {
      console.error('❌ 删除失败:', error)
      console.error('📋 删除失败完整响应:', error.response)
      console.error('🔍 删除失败data:', error.response?.data)
      console.error('📝 删除失败detail:', error.response?.data?.detail)
      if (error.response?.data?.detail && Array.isArray(error.response.data.detail)) {
        error.response.data.detail.forEach((item, index) => {
          console.error(`📝 Detail[${index}]:`, item)
          if (item.loc) console.error(`   Location:`, item.loc)
          if (item.msg) console.error(`   Message:`, item.msg)
          if (item.type) console.error(`   Type:`, item.type)
        })
      }
      
      
      let errorMsg = '删除失败'
      if (error.response?.data?.detail) {
   
        if (Array.isArray(error.response.data.detail)) {
          const detailMessages = error.response.data.detail.map(item => {
            if (typeof item === 'string') return item
            if (item.msg) return item.msg
            if (item.loc && item.msg) {
              const field = item.loc[item.loc.length - 1] 
              return `${field}: ${item.msg}`
            }
            return JSON.stringify(item)
          })
          errorMsg += ': ' + detailMessages.join('; ')
        } else {
          errorMsg += ': ' + JSON.stringify(error.response.data.detail)
        }
      } else if (error.response?.data?.message) {
        errorMsg += ': ' + error.response.data.message
      } else if (error.message) {
        errorMsg += ': ' + error.message
      }
      
      console.error('💬 最终错误消息:', errorMsg)
      ElMessage.error(errorMsg)
    })
  }).catch(() => {
    console.log('👤 用户取消删除操作')
  })
}
    /** 查询模型列表 */
    function getList() {
      console.log('开始获取模型列表，containerId:', props.containerId)
      loading.value = true
      listModel(props.containerId).then(response => {
        console.log('完整响应:', response)
        console.log('响应数据:', response.data)
  
        if (response && response.data && typeof response.data === 'object') {
          const modelsArray = Object.entries(response.data).map(([model_name, modelInfo]) => {
            return {
              id: model_name, 
              model_name: model_name, 
              algo_name: model_name, 
              type: '自定义模型', 
              version: '1.0', 
              intro: modelInfo.intro || '',
              args_intro: modelInfo.args_intro || '{}',
              args: modelInfo.args || '()',
              container_id: props.containerId
            }
          })
          
          models.value = modelsArray
          console.log('转换后的模型数组:', models.value)
        } else {
          models.value = []
          console.warn('响应数据格式异常:', response)
        }
        
        loading.value = false
      }).catch(error => {
        console.error('获取模型列表失败:', error)
        loading.value = false
        ElMessage.error('获取模型列表失败')
      })
    }
    
    const saveModel = () => {
      if (!currentModel.value.model_name) {
        ElMessage.error('请输入模型名称')
        return
      }
      if (!isEditingModel.value && !currentModel.value.file) {
        ElMessage.error('请上传模型文件')
        return
      }
      
      saveLoading.value = true
      
      try {
        if (isEditingModel.value) {
          const index = models.value.findIndex(a => a.id === currentModel.value.id)
          if (index !== -1) {
            models.value[index] = { 
              ...models.value[index],
              ...currentModel.value
            }
          }
          ElMessage.success('模型更新成功')
          modelDialogVisible.value = false
        } else {
          const formData = new FormData()
          formData.append('model_name', currentModel.value.model_name)
          formData.append('intro', currentModel.value.intro || '')
          formData.append('container_id', props.containerId.toString())
          
          if (currentModel.value.file) {
            formData.append('file', currentModel.value.file)
          }
          
          addModel(formData).then(response => {
            console.log('上传模型成功:', response)
            ElMessage.success("上传成功")
            modelDialogVisible.value = false
            getList()
          }).catch(error => {
            console.error("上传错误:", error)
            if (error.response?.data?.detail) {
              ElMessage.error("上传失败: " + JSON.stringify(error.response.data.detail))
            } else {
              ElMessage.error("上传失败: " + (error.response?.data?.message || error.message))
            }
          }).finally(() => {
            saveLoading.value = false
          })
        }
      } catch (error) {
        console.error('保存模型失败:', error)
        ElMessage.error('保存失败，请重试')
        saveLoading.value = false
      }
    }
    
    const searchModels = () => {
      modelCurrentPage.value = 1
    }
   // 获取运行日志 
const getRunLogs = async () => {
  showLogs.value = true
  showTasks.value = false
  logsLoading.value = true
  
  try {
    const response = await getLog(props.containerId)
    console.log('日志响应数据:', response) 
    if (response && response.logs !== undefined) {
      if (typeof response.logs === 'string') {
        if (response.logs.trim() === '') {
          logs.value = ['暂无日志内容']
        } else {
          logs.value = response.logs.split('\n')
        }
      } else {
        logs.value = ['日志格式异常: ' + JSON.stringify(response.logs)]
      }
    } else if (response && response.data && response.data.logs !== undefined) {
      if (typeof response.data.logs === 'string') {
        if (response.data.logs.trim() === '') {
          logs.value = ['暂无日志内容']
        } else {
          logs.value = response.data.logs.split('\n')
        }
      } else {
        logs.value = ['日志格式异常: ' + JSON.stringify(response.data.logs)]
      }
    } else {
      logs.value = ['无法解析日志数据: ' + JSON.stringify(response)]
    }
    
    ElMessage.success('运行日志获取成功')
  } catch (error) {
    console.error('获取运行日志失败:', error)
    ElMessage.error('获取运行日志失败')
    logs.value = ['获取日志失败: ' + (error.response?.data?.message || error.message || '未知错误')]
  } finally {
    logsLoading.value = false
  }
}

    
    // 获取运行任务 
    const getRunningTasks = async () => {
      showTasks.value = true
      showLogs.value = false
      tasksLoading.value = true
      
      try {
        const response = await getTasking(props.containerId)
        if (Array.isArray(response)) {
          runningTasks.value = response
        } else if (response.data && Array.isArray(response.data)) {
          runningTasks.value = response.data
        } else {
          runningTasks.value = [response]
        }
        ElMessage.success('运行任务获取成功')
      } catch (error) {
        console.error('获取运行任务失败:', error)
        ElMessage.error('获取运行任务失败')
        runningTasks.value = []
      } finally {
        tasksLoading.value = false
      }
    }

    const getStatusType = (status) => {
      const statusMap = {
        '运行中': 'warning',
        '已完成': 'success',
        '失败': 'danger',
        '等待中': 'info'
      }
      return statusMap[status] || 'info'
    }
    
    return {
      models,
      modelSearch,
      modelCurrentPage,
      modelPageSize,
      modelDialogVisible,
      isEditingModel,
      currentModel,
      showLogs,
      showTasks,
      logs,
      runningTasks,
      logsLoading,
      tasksLoading,
      loading,
      saveLoading,
      filteredModels,
      SearchIcon,
      uploadRef,
      addModel1,
      editModel,
      deleteModel,
      saveModel,
      searchModels,
      getRunLogs,
      getRunningTasks,
      getStatusType,
      handleFileChange,
      handleFileRemove,
      getList
    }
  }
}
</script>

<style scoped>
.section {
  flex: 1;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  padding: 20px;
  display: flex;
  flex-direction: column;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 15px;
  border-bottom: 1px solid #ebeef5;
}

.section-title {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
}

.operation-buttons {
  display: flex;
  gap: 10px;
}

.search-area {
  margin-bottom: 15px;
}

.data-table {
  flex: 1;
}

.pagination {
  margin-top: 15px;
  display: flex;
  justify-content: flex-end;
}

.log-container {
  margin-top: 20px;
  border-top: 1px solid #ebeef5;
  padding-top: 15px;
}

.log-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.log-content {
  background-color: #1e1e1e;
  color: #d4d4d4;
  padding: 15px;
  border-radius: 4px;
  font-family: 'Courier New', monospace;
  max-height: 200px;
  overflow-y: auto;
  margin-top: 10px;
}

.task-list {
  margin-top: 10px;
}

.task-item {
  display: flex;
  justify-content: space-between;
  padding: 8px 0;
  border-bottom: 1px solid #ebeef5;
}

.task-name {
  font-weight: 500;
}

.task-progress {
  flex: 1;
  margin: 0 15px;
}

.no-data {
  text-align: center;
  color: #909399;
  padding: 20px;
}

.loading {
  text-align: center;
  color: #909399;
  padding: 20px;
}
</style>