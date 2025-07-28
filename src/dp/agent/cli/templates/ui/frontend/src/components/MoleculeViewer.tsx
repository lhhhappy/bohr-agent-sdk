import React, { useEffect, useRef, useState } from 'react'
import { RotateCw, ZoomIn, ZoomOut, Download, Tag } from 'lucide-react'

interface MoleculeViewerProps {
  content: string
  height?: string
}

interface Atom3D {
  elem: string
  x: number
  y: number
  z: number
}

interface Viewer3D {
  addModel: (data: string, format: string) => void
  setStyle: (selection: object, style: object) => void
  getModel: () => { selectedAtoms: (selection: object) => Atom3D[] }
  addLabel: (text: string, options: object) => void
  removeAllLabels: () => void
  zoomTo: () => void
  zoom: (factor: number) => void
  render: () => void
  clear: () => void
  pngURI: () => string
}

declare global {
  interface Window {
    $3Dmol: {
      createViewer: (element: HTMLElement, options: object) => Viewer3D
    }
  }
}

const MoleculeViewer: React.FC<MoleculeViewerProps> = ({ content, height = '500px' }) => {
  const viewerRef = useRef<HTMLDivElement>(null)
  const viewerInstanceRef = useRef<Viewer3D | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [zoom, setZoom] = useState(100)
  const [showLabels, setShowLabels] = useState(true)

  useEffect(() => {
    if (!viewerRef.current) return

    // 加载 3Dmol.js
    const script = document.createElement('script')
    script.src = 'https://3dmol.org/build/3Dmol-min.js'
    script.async = true
    
    script.onload = () => {
      if (!window.$3Dmol || !viewerRef.current) return
      
      setIsLoading(false)
      
      // 创建查看器实例
      const viewer = window.$3Dmol.createViewer(viewerRef.current, {
        backgroundColor: 'white'
      })
      viewerInstanceRef.current = viewer
      
      // 添加分子模型
      viewer.addModel(content, 'xyz')
      
      // 设置样式 - 球棍模型
      viewer.setStyle({}, {
        stick: { 
          radius: 0.15,
          colorscheme: 'Jmol',
          singleBonds: true
        },
        sphere: { 
          scale: 0.3, 
          colorscheme: 'Jmol' 
        }
      })
      
      // 添加元素标签
      const atoms = viewer.getModel().selectedAtoms({})
      atoms.forEach((atom: Atom3D) => {
        viewer.addLabel(atom.elem, {
          position: { x: atom.x, y: atom.y, z: atom.z },
          backgroundColor: 'rgba(255, 255, 255, 0.8)',
          backgroundOpacity: 0.8,
          fontColor: 'black',
          fontSize: 12,
          showBackground: true,
          alignment: 'center'
        })
      })
      
      // 自动缩放并渲染
      viewer.zoomTo()
      viewer.render()
      
      // 强制重新渲染以确保正确显示
      setTimeout(() => {
        // 重新应用样式以避免渲染问题
        viewer.setStyle({}, {
          stick: { 
            radius: 0.15,
            colorscheme: 'Jmol',
            singleBonds: true
          },
          sphere: { 
            scale: 0.3, 
            colorscheme: 'Jmol' 
          }
        })
        viewer.render()
      }, 100)
    }

    script.onerror = () => {
      // console.error('Failed to load 3Dmol.js')
      setIsLoading(false)
    }
    
    document.head.appendChild(script)
    
    // 清理函数
    return () => {
      if (script.parentNode) {
        script.parentNode.removeChild(script)
      }
      if (viewerInstanceRef.current) {
        viewerInstanceRef.current?.clear()
      }
    }
  }, [content])

  // 处理缩放
  const handleZoom = (delta: number) => {
    if (!viewerInstanceRef.current) return
    
    const newZoom = Math.max(50, Math.min(200, zoom + delta))
    setZoom(newZoom)
    
    viewerInstanceRef.current.zoom(newZoom / 100)
    viewerInstanceRef.current.render()
  }

  // 重置视图
  const handleReset = () => {
    if (!viewerInstanceRef.current) return
    
    setZoom(100)
    viewerInstanceRef.current.zoomTo()
    viewerInstanceRef.current.render()
  }

  // 添加或移除标签
  const updateLabels = (show: boolean) => {
    if (!viewerInstanceRef.current) return
    
    viewerInstanceRef.current.removeAllLabels()
    
    if (show) {
      const atoms = viewerInstanceRef.current.getModel().selectedAtoms({})
      atoms.forEach((atom: Atom3D) => {
        viewerInstanceRef.current?.addLabel(atom.elem, {
          position: { x: atom.x, y: atom.y, z: atom.z },
          backgroundColor: 'rgba(255, 255, 255, 0.8)',
          backgroundOpacity: 0.8,
          fontColor: 'black',
          fontSize: 12,
          showBackground: true,
          alignment: 'center'
        })
      })
    }
    
    viewerInstanceRef.current.render()
  }

  // 切换样式
  const handleStyleChange = (style: string) => {
    if (!viewerInstanceRef.current) return
    
    switch (style) {
      case 'stick':
        viewerInstanceRef.current.setStyle({}, { 
          stick: { 
            radius: 0.15,
            colorscheme: 'Jmol',
            singleBonds: true
          } 
        })
        break
      case 'sphere':
        viewerInstanceRef.current.setStyle({}, { sphere: { colorscheme: 'Jmol' } })
        break
      case 'ball-stick':
        viewerInstanceRef.current.setStyle({}, { 
          stick: { 
            radius: 0.15,
            colorscheme: 'Jmol',
            singleBonds: true
          }, 
          sphere: { 
            scale: 0.3, 
            colorscheme: 'Jmol' 
          } 
        })
        break
      case 'cartoon':
        viewerInstanceRef.current.setStyle({}, { cartoon: { colorscheme: 'Jmol' } })
        break
    }
    
    // 保持标签显示
    updateLabels(showLabels)
    viewerInstanceRef.current.render()
  }

  // 导出图片
  const handleExport = () => {
    if (!viewerInstanceRef.current) return
    
    const pngUri = viewerInstanceRef.current.pngURI()
    const link = document.createElement('a')
    link.download = 'molecule.png'
    link.href = pngUri
    link.click()
  }

  return (
    <div className="flex flex-col h-full bg-gray-50 dark:bg-gray-900 rounded-lg overflow-hidden">
      {/* 工具栏 */}
      <div className="flex items-center justify-between p-3 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
        <div className="flex items-center gap-2">
          <button
            onClick={() => handleZoom(-25)}
            className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-md transition-colors"
            title="缩小"
            disabled={isLoading}
          >
            <ZoomOut className="w-4 h-4 text-gray-600 dark:text-gray-400" />
          </button>
          <span className="text-sm text-gray-600 dark:text-gray-400 min-w-[60px] text-center">
            {zoom}%
          </span>
          <button
            onClick={() => handleZoom(25)}
            className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-md transition-colors"
            title="放大"
            disabled={isLoading}
          >
            <ZoomIn className="w-4 h-4 text-gray-600 dark:text-gray-400" />
          </button>
          
          <div className="w-px h-6 bg-gray-300 dark:bg-gray-600 mx-1" />
          
          <button
            onClick={handleReset}
            className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-md transition-colors"
            title="重置"
            disabled={isLoading}
          >
            <RotateCw className="w-4 h-4 text-gray-600 dark:text-gray-400" />
          </button>
          
          <div className="w-px h-6 bg-gray-300 dark:bg-gray-600 mx-1" />
          
          {/* 标签切换 */}
          <button
            onClick={() => {
              setShowLabels(!showLabels)
              updateLabels(!showLabels)
            }}
            className={`p-2 rounded-md transition-colors ${
              showLabels 
                ? 'bg-blue-100 dark:bg-blue-900 text-blue-600 dark:text-blue-400' 
                : 'hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-600 dark:text-gray-400'
            }`}
            title={showLabels ? '隐藏元素标签' : '显示元素标签'}
            disabled={isLoading}
          >
            <Tag className="w-4 h-4" />
          </button>
          
          <div className="w-px h-6 bg-gray-300 dark:bg-gray-600 mx-1" />
          
          {/* 样式选择 */}
          <select
            onChange={(e) => handleStyleChange(e.target.value)}
            className="px-3 py-1.5 text-sm bg-gray-100 dark:bg-gray-700 rounded-md text-gray-700 dark:text-gray-300"
            disabled={isLoading}
          >
            <option value="ball-stick">球棍模型</option>
            <option value="stick">棍状模型</option>
            <option value="sphere">球状模型</option>
            <option value="cartoon">卡通模型</option>
          </select>
        </div>
        
        <div className="flex items-center gap-2">
          <span className="text-sm text-gray-600 dark:text-gray-400 mr-2">
            拖动旋转 • 滚轮缩放
          </span>
          <button
            onClick={handleExport}
            className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-md transition-colors"
            title="导出图片"
            disabled={isLoading}
          >
            <Download className="w-4 h-4 text-gray-600 dark:text-gray-400" />
          </button>
        </div>
      </div>

      {/* 3Dmol 查看器容器 */}
      <div className="flex-1 relative">
        {isLoading && (
          <div className="absolute inset-0 flex items-center justify-center bg-white dark:bg-gray-800">
            <div className="text-center">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto mb-2"></div>
              <p className="text-sm text-gray-600 dark:text-gray-400">加载分子查看器...</p>
            </div>
          </div>
        )}
        <div
          ref={viewerRef}
          style={{ width: '100%', height: height }}
          className="bg-white dark:bg-gray-800"
        />
      </div>
    </div>
  )
}

export default MoleculeViewer