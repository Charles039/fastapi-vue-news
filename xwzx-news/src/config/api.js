/**
 * API配置文件
 * 包含API基础URL和AI问答功能所需的API参数
 */

// API基础URL配置
export const apiConfig = {
  // 后端API基础URL
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000',
}

export const aiChatConfig = {
  // OpenAI API地址
  apiEndpoint: 'https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions',

  // AI 页面当前已禁用。密钥不得放入浏览器端源码；恢复功能时应由后端代理调用。
  apiKey: '',
  // 使用的模型
  model: 'qwen3-max-preview'
}
