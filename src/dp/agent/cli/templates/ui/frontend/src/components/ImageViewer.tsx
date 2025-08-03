import React, { useState } from 'react'
import { ZoomIn, ZoomOut, RotateCw, Download } from 'lucide-react'

interface ImageViewerProps {
  src: string
  alt?: string
}

const ImageViewer: React.FC<ImageViewerProps> = ({ src, alt = 'Image preview' }) => {
  const [scale, setScale] = useState(1)
  const [rotation, setRotation] = useState(0)

  const handleZoomIn = () => {
    setScale(prev => Math.min(prev + 0.25, 3))
  }

  const handleZoomOut = () => {
    setScale(prev => Math.max(prev - 0.25, 0.25))
  }

  const handleRotate = () => {
    setRotation(prev => (prev + 90) % 360)
  }

  const handleDownload = () => {
    const link = document.createElement('a')
    link.href = src
    link.download = alt
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  }

  const handleReset = () => {
    setScale(1)
    setRotation(0)
  }

  return (
    <div className="flex flex-col h-full bg-gray-50 dark:bg-gray-900 rounded-lg overflow-hidden">
      {/* Toolbar */}
      <div className="flex items-center justify-between p-3 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
        <div className="flex items-center gap-2">
          <button
            onClick={handleZoomOut}
            className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-md transition-colors"
            title="缩小"
          >
            <ZoomOut className="w-4 h-4 text-gray-600 dark:text-gray-400" />
          </button>
          <span className="text-sm text-gray-600 dark:text-gray-400 min-w-[60px] text-center">
            {Math.round(scale * 100)}%
          </span>
          <button
            onClick={handleZoomIn}
            className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-md transition-colors"
            title="放大"
          >
            <ZoomIn className="w-4 h-4 text-gray-600 dark:text-gray-400" />
          </button>
          <div className="w-px h-6 bg-gray-300 dark:bg-gray-600 mx-1" />
          <button
            onClick={handleRotate}
            className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-md transition-colors"
            title="旋转"
          >
            <RotateCw className="w-4 h-4 text-gray-600 dark:text-gray-400" />
          </button>
          <button
            onClick={handleReset}
            className="px-3 py-1.5 text-sm hover:bg-gray-100 dark:hover:bg-gray-700 rounded-md transition-colors text-gray-600 dark:text-gray-400"
            title="重置"
          >
            重置
          </button>
        </div>
        <button
          onClick={handleDownload}
          className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-md transition-colors"
          title="下载"
        >
          <Download className="w-4 h-4 text-gray-600 dark:text-gray-400" />
        </button>
      </div>

      {/* Image Container */}
      <div className="flex-1 overflow-auto p-8 flex items-center justify-center">
        <div
          className="transition-transform duration-200 ease-in-out"
          style={{
            transform: `scale(${scale}) rotate(${rotation}deg)`,
            transformOrigin: 'center'
          }}
        >
          <img
            src={src}
            alt={alt}
            className="max-w-full h-auto shadow-lg rounded-lg"
            style={{ maxHeight: '80vh' }}
          />
        </div>
      </div>
    </div>
  )
}

export default ImageViewer