import React, { useEffect, useRef } from 'react'
import * as $3Dmol from '3dmol'

interface MoleculeViewerProps {
  content: string
  height?: string
}

const MoleculeViewer: React.FC<MoleculeViewerProps> = ({ content, height = '500px' }) => {
  const viewerRef = useRef<HTMLDivElement>(null)
  const viewerInstanceRef = useRef<any>(null)

  useEffect(() => {
    if (!viewerRef.current) return

    // Create viewer instance
    const config = { backgroundColor: 'white' }
    const viewer = $3Dmol.createViewer(viewerRef.current, config)
    viewerInstanceRef.current = viewer

    // Parse and add the molecule
    viewer.addModel(content, 'xyz')
    
    // Style the molecule
    viewer.setStyle({}, { 
      sphere: { radius: 0.5 },
      stick: { radius: 0.15 }
    })
    
    // Center and render
    viewer.zoomTo()
    viewer.render()

    // Handle resize
    const handleResize = () => {
      if (viewerInstanceRef.current) {
        viewerInstanceRef.current.resize()
      }
    }
    window.addEventListener('resize', handleResize)

    return () => {
      window.removeEventListener('resize', handleResize)
      if (viewerInstanceRef.current) {
        viewerInstanceRef.current.clear()
      }
    }
  }, [content])

  return (
    <div 
      ref={viewerRef} 
      style={{ 
        width: '100%', 
        height,
        position: 'relative',
        border: '1px solid #e5e7eb',
        borderRadius: '0.5rem',
        overflow: 'hidden'
      }}
    />
  )
}

export default MoleculeViewer