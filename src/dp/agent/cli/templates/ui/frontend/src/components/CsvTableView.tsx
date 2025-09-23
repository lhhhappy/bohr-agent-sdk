import React, { useState, useMemo } from 'react'
import { ArrowUpDown, ArrowUp, ArrowDown, Search } from 'lucide-react'

interface CsvTableViewProps {
  content: string
}

const CsvTableView: React.FC<CsvTableViewProps> = ({ content }) => {
  const [sortColumn, setSortColumn] = useState<number | null>(null)
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('asc')
  const [searchTerm, setSearchTerm] = useState('')

  const { headers, rows } = useMemo(() => {
    const lines = content.trim().split('\n')
    if (lines.length === 0) return { headers: [], rows: [] }

    const parseCSVLine = (line: string) => {
      const result = []
      let current = ''
      let inQuotes = false
      
      for (let i = 0; i < line.length; i++) {
        const char = line[i]
        
        if (char === '"') {
          if (inQuotes && line[i + 1] === '"') {
            current += '"'
            i++
          } else {
            inQuotes = !inQuotes
          }
        } else if (char === ',' && !inQuotes) {
          result.push(current.trim())
          current = ''
        } else {
          current += char
        }
      }
      
      result.push(current.trim())
      return result
    }

    const headers = parseCSVLine(lines[0])
    const rows = lines.slice(1).map(line => parseCSVLine(line))
    
    return { headers, rows }
  }, [content])

  const filteredAndSortedRows = useMemo(() => {
    let filtered = rows
    
    if (searchTerm) {
      filtered = rows.filter(row =>
        row.some(cell => 
          cell.toLowerCase().includes(searchTerm.toLowerCase())
        )
      )
    }
    
    if (sortColumn !== null) {
      filtered = [...filtered].sort((a, b) => {
        const aVal = a[sortColumn] || ''
        const bVal = b[sortColumn] || ''
        
        const aNum = parseFloat(aVal)
        const bNum = parseFloat(bVal)
        
        if (!isNaN(aNum) && !isNaN(bNum)) {
          return sortDirection === 'asc' ? aNum - bNum : bNum - aNum
        }
        
        const comparison = aVal.localeCompare(bVal)
        return sortDirection === 'asc' ? comparison : -comparison
      })
    }
    
    return filtered
  }, [rows, searchTerm, sortColumn, sortDirection])

  const handleSort = (columnIndex: number) => {
    if (sortColumn === columnIndex) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc')
    } else {
      setSortColumn(columnIndex)
      setSortDirection('asc')
    }
  }

  const getSortIcon = (columnIndex: number) => {
    if (sortColumn !== columnIndex) {
      return <ArrowUpDown className="w-3 h-3 text-gray-400" />
    }
    return sortDirection === 'asc' ? 
      <ArrowUp className="w-3 h-3 text-blue-500" /> : 
      <ArrowDown className="w-3 h-3 text-blue-500" />
  }

  return (
    <div className="flex flex-col h-full">
      <div className="p-4 border-b border-gray-200 dark:border-gray-700">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="搜索表格内容..."
            className="w-full pl-9 pr-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
        <div className="mt-2 text-xs text-gray-500">
          显示 {filteredAndSortedRows.length} / {rows.length} 行
        </div>
      </div>
      
      <div className="flex-1 overflow-auto">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 dark:bg-gray-900 sticky top-0 z-10">
            <tr>
              {headers.map((header, index) => (
                <th
                  key={index}
                  className="px-4 py-3 text-left font-medium text-gray-700 dark:text-gray-300 border-b border-gray-200 dark:border-gray-700 cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-800"
                  onClick={() => handleSort(index)}
                >
                  <div className="flex items-center gap-2">
                    <span className="truncate">{header}</span>
                    {getSortIcon(index)}
                  </div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="bg-white dark:bg-gray-800">
            {filteredAndSortedRows.map((row, rowIndex) => (
              <tr
                key={rowIndex}
                className="hover:bg-gray-50 dark:hover:bg-gray-700 border-b border-gray-100 dark:border-gray-700"
              >
                {row.map((cell, cellIndex) => (
                  <td
                    key={cellIndex}
                    className="px-4 py-2 text-gray-700 dark:text-gray-300"
                  >
                    <div className="truncate max-w-xs" title={cell}>
                      {cell}
                    </div>
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
        
        {filteredAndSortedRows.length === 0 && (
          <div className="text-center py-8 text-gray-500">
            {searchTerm ? '没有找到匹配的数据' : '表格为空'}
          </div>
        )}
      </div>
    </div>
  )
}

export default CsvTableView