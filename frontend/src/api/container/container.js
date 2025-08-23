import request from '@/utils/request'

// 查询容器列表
export function listContainer(query) {
  return request({
    url: '/container/container/list',
    method: 'get',
    params: query
  })
}

// 查询容器详细
export function getContainer(id) {
  return request({
    url: '/container/container/' + id,
    method: 'get'
  })
}

// 新增容器
export function addContainer(data) {
  return request({
    url: '/container/container',
    method: 'post',
    data: data
  })
}

// 修改容器
export function updateContainer(data) {
  return request({
    url: '/container/container',
    method: 'put',
    data: data
  })
}

// 删除容器
export function delContainer(id) {
  return request({
    url: '/container/container/' + id,
    method: 'delete'
  })
}
