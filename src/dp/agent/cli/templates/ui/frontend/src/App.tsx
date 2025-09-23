import ChatInterface from './components/ChatInterface'
import { LanguageProvider } from './contexts/LanguageContext'

function App() {
  return (
    <LanguageProvider>
      <ChatInterface />
    </LanguageProvider>
  )
}

export default App