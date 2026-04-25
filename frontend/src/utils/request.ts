import axios from 'axios'

// Axios 实例：baseURL 来自 Vite 环境变量，便于开发和生产环境切换。
const request = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
  timeout: 60000,
})

// 响应拦截：统一取出后端返回结构，业务错误交给页面处理。
request.interceptors.response.use(
  (response) => response.data,
  (error) => {
    return Promise.reject(error)
  },
)

export default request
