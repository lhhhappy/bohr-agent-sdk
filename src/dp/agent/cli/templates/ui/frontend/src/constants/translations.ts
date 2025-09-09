export const translations = {
  zh: {
    // Connection Status
    connection: {
      connected: '已连接',
      connecting: '连接中...',
      disconnected: '未连接',
      error: '连接错误',
    },
    
    // Tool Messages
    tool: {
      executing: '正在执行',
      longRunning: '（长时间运行）',
      completed: '执行完成',
      failed: '执行失败',
      preparing: '准备执行',
      statusUpdate: '工具状态更新',
      expandResults: '展开结果',
      collapseResults: '收起结果',
      expandParams: '展开参数',
      collapseParams: '收起参数',
      toolExecuting: '工具正在执行中...',
      callParams: '调用参数:',
      executionResult: '执行结果:',
    },
    
    // UI Actions
    actions: {
      showTerminal: '显示终端',
      hideTerminal: '隐藏终端',
      showFiles: '查看文件',
      hideFiles: '隐藏文件',
      send: '发送',
      newSession: '新建对话',
      delete: '删除',
      uploadFile: '上传文件',
    },
    
    // Error Messages
    errors: {
      general: '错误',
      serverDisconnected: '未连接到服务器，请稍后重试',
      commandParse: '命令解析错误',
      commandExecution: '命令执行错误',
      permissionDenied: '权限被拒绝',
      dangerousCommand: '此命令可能有危险，已被阻止',
      fileUploadFailed: '文件上传失败',
      loadFilesFailed: '加载文件失败',
      deleteFileFailed: '删除文件失败',
      unknownError: '未知错误',
      cannotConnectToServer: '无法连接到服务器',
      getProjectListFailed: '获取项目列表失败',
      jsonFormatError: 'JSON 格式错误',
    },
    
    // Placeholders
    placeholders: {
      messageInput: '输入消息...',
      commandInput: '输入命令...',
      selectProject: '选择项目...',
    },
    
    // Session Messages
    session: {
      newConversation: '新对话',
      deleteConfirm: '确定要删除这个对话吗？',
      noSessions: '暂无对话',
      clickToStart: '点击上方按钮开始',
      justNow: '刚刚',
      minutesAgo: '分钟前',
      hoursAgo: '小时前',
      daysAgo: '天前',
      messages: '消息',
      untitled: '未命名',
    },
    
    // File Explorer
    files: {
      loading: '正在加载文件...',
      loadError: '加载文件失败',
      empty: '没有找到文件',
      deleteConfirm: '确定要删除',
      deleteSuccess: '文件删除成功',
      htmlFile: 'HTML 文件',
      showLines: '显示',
      lines: '行',
      deleteFolder: '文件夹',
      deleteFile: '文件',
      downloadFolder: '下载文件夹',
      downloadFile: '下载文件',
      fileBrowser: '文件浏览器',
      loading2: '加载',
      collapse: '收起',
      expand: '展开',
    },
    
    // Project
    project: {
      needToSelect: '需要选择项目',
      pleaseSelectFirst: '🔒 请先选择项目',
      updateSession: '更新会话列表',
      loadHistory: '加载会话历史消息',
      alreadySet: '已设置:',
      selectFromDropdown: '请从下拉列表中选择您的 Bohrium 项目以开始使用',
      checkAccessKey: '如果看不到项目列表，请检查您的 AccessKey 配置',
    },
    
    // Status
    status: {
      showingLines: '显示',
      ofLines: '/',
      lines: '行',
    },
    
    // Components
    components: {
      searchTableContent: '搜索表格内容...',
      searchText: '搜索文本...',
      lineNumber: '行号',
      wordWrapOff: '关闭自动换行',
      wordWrapOn: '开启自动换行',
      copyAll: '复制全部内容',
      foundMatches: '找到',
      matchingLines: '个匹配行',
      preview: '预览',
      source: '源代码',
      hideElementLabels: '隐藏元素标签',
      showElementLabels: '显示元素标签',
      ballStickModel: '球棍模型',
      stickModel: '棍状模型',
      sphereModel: '球状模型',
      cartoonModel: '卡通模型',
      dragToRotate: '拖动旋转 • 滚轮缩放',
      exportImage: '导出图片',
      loadingMoleculeViewer: '加载分子查看器...',
    },
  },
  
  en: {
    // Connection Status
    connection: {
      connected: 'Connected',
      connecting: 'Connecting...',
      disconnected: 'Disconnected',
      error: 'Connection Error',
    },
    
    // Tool Messages
    tool: {
      executing: 'Executing',
      longRunning: ' (long running)',
      completed: 'Completed',
      failed: 'Failed',
      preparing: 'Preparing',
      statusUpdate: 'Tool status update',
      expandResults: 'Expand results',
      collapseResults: 'Collapse results',
      expandParams: 'Expand parameters',
      collapseParams: 'Collapse parameters',
      toolExecuting: 'Tool is executing...',
      callParams: 'Call parameters:',
      executionResult: 'Execution result:',
    },
    
    // UI Actions
    actions: {
      showTerminal: 'Show Terminal',
      hideTerminal: 'Hide Terminal',
      showFiles: 'Show Files',
      hideFiles: 'Hide Files',
      send: 'Send',
      newSession: 'New Session',
      delete: 'Delete',
      uploadFile: 'Upload File',
    },
    
    // Error Messages
    errors: {
      general: 'Error',
      serverDisconnected: 'Not connected to server. Please try again later.',
      commandParse: 'Command parse error',
      commandExecution: 'Command execution error',
      permissionDenied: 'Permission denied',
      dangerousCommand: 'This command is potentially dangerous and has been blocked',
      fileUploadFailed: 'File upload failed',
      loadFilesFailed: 'Failed to load files',
      deleteFileFailed: 'Failed to delete file',
      unknownError: 'Unknown error',
      cannotConnectToServer: 'Cannot connect to server',
      getProjectListFailed: 'Failed to get project list',
      jsonFormatError: 'JSON format error',
    },
    
    // Placeholders
    placeholders: {
      messageInput: 'Type a message...',
      commandInput: 'Enter command...',
      selectProject: 'Select project...',
    },
    
    // Session Messages
    session: {
      newConversation: 'New Conversation',
      deleteConfirm: 'Are you sure you want to delete this session?',
      noSessions: 'No sessions',
      clickToStart: 'Click the button above to start',
      justNow: 'Just now',
      minutesAgo: 'minutes ago',
      hoursAgo: 'hours ago',
      daysAgo: 'days ago',
      messages: 'messages',
      untitled: 'Untitled',
    },
    
    // File Explorer
    files: {
      loading: 'Loading files...',
      loadError: 'Failed to load files',
      empty: 'No files found',
      deleteConfirm: 'Are you sure you want to delete',
      deleteSuccess: 'File deleted successfully',
      htmlFile: 'HTML File',
      showLines: 'Showing',
      lines: 'lines',
      deleteFolder: 'folder',
      deleteFile: 'file',
      downloadFolder: 'Download Folder',
      downloadFile: 'Download File',
      fileBrowser: 'File Browser',
      loading2: 'Loading',
      collapse: 'Collapse',
      expand: 'Expand',
    },
    
    // Project
    project: {
      needToSelect: 'Need to select project',
      pleaseSelectFirst: '🔒 Please select project first',
      updateSession: 'Update session list',
      loadHistory: 'Load session history',
      alreadySet: 'Already set:',
      selectFromDropdown: 'Please select your Bohrium project from the dropdown to start',
      checkAccessKey: 'If you cannot see the project list, please check your AccessKey configuration',
    },
    
    // Status
    status: {
      showingLines: 'Showing',
      ofLines: '/',
      lines: 'lines',
    },
    
    // Components
    components: {
      searchTableContent: 'Search table content...',
      searchText: 'Search text...',
      lineNumber: 'Line number',
      wordWrapOff: 'Turn off word wrap',
      wordWrapOn: 'Turn on word wrap',
      copyAll: 'Copy all content',
      foundMatches: 'Found',
      matchingLines: 'matching lines',
      preview: 'Preview',
      source: 'Source',
      hideElementLabels: 'Hide element labels',
      showElementLabels: 'Show element labels',
      ballStickModel: 'Ball & stick',
      stickModel: 'Stick',
      sphereModel: 'Sphere',
      cartoonModel: 'Cartoon',
      dragToRotate: 'Drag to rotate • Scroll to zoom',
      exportImage: 'Export image',
      loadingMoleculeViewer: 'Loading molecule viewer...',
    },
  }
}

export type Language = 'zh' | 'en'
export type TranslationKey = typeof translations.zh