import React, { createContext, useState, useContext, useEffect, ReactNode } from 'react'
import { Language, translations, TranslationKey } from '../constants/translations'

interface LanguageContextType {
  language: Language
  setLanguage: (lang: Language) => void
  t: TranslationKey
}

const LanguageContext = createContext<LanguageContextType | undefined>(undefined)

export const LanguageProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [language, setLanguage] = useState<Language>(() => {
    // 从localStorage读取保存的语言设置，默认为中文
    const saved = localStorage.getItem('app-language')
    return (saved === 'en' || saved === 'zh') ? saved : 'zh'
  })
  
  useEffect(() => {
    // 保存语言设置到localStorage
    localStorage.setItem('app-language', language)
  }, [language])
  
  const value = {
    language,
    setLanguage,
    t: translations[language]
  }
  
  return (
    <LanguageContext.Provider value={value}>
      {children}
    </LanguageContext.Provider>
  )
}

export const useLanguage = () => {
  const context = useContext(LanguageContext)
  if (!context) {
    throw new Error('useLanguage must be used within a LanguageProvider')
  }
  return context
}