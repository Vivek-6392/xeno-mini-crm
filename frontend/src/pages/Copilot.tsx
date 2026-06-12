import { Bot, Send, Sparkles, User } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'
import { ChatMessage, streamAgentChat } from '../lib/api'

const SUGGESTED = [
  'Show me my customer base overview',
  'Find customers who haven\'t ordered in the last 60 days',
  'Create a loyalty campaign for my top spenders in Mumbai',
  'How did my last campaign perform?',
  'Launch a WhatsApp win-back campaign for lapsed customers',
]

interface Message extends ChatMessage {
  streaming?: boolean
}

export default function Copilot() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput]       = useState('')
  const [loading, setLoading]   = useState(false)
  const bottomRef = useRef<HTMLDivElement>(null)
  const inputRef  = useRef<HTMLTextAreaElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  async function sendMessage(text: string) {
    if (!text.trim() || loading) return

    const userMsg: Message = { role: 'user', content: text }
    const history = messages.map(m => ({ role: m.role, content: m.content }))

    setMessages(prev => [...prev, userMsg])
    setInput('')
    setLoading(true)

    // Add placeholder assistant message
    setMessages(prev => [...prev, { role: 'assistant', content: '', streaming: true }])

    await streamAgentChat(
      text,
      history,
      // onToken
      (token) => {
        setMessages(prev => {
          const updated = [...prev]
          const last = updated[updated.length - 1]
          if (last.role === 'assistant') {
            updated[updated.length - 1] = { ...last, content: last.content + token }
          }
          return updated
        })
      },
      // onDone
      () => {
        setMessages(prev => {
          const updated = [...prev]
          const last = updated[updated.length - 1]
          if (last.role === 'assistant') {
            updated[updated.length - 1] = { ...last, streaming: false }
          }
          return updated
        })
        setLoading(false)
        inputRef.current?.focus()
      },
      // onError
      (err) => {
        setMessages(prev => {
          const updated = [...prev]
          updated[updated.length - 1] = {
            role: 'assistant',
            content: `⚠️ Error: ${err}`,
            streaming: false,
          }
          return updated
        })
        setLoading(false)
      }
    )
  }

  function handleKey(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage(input)
    }
  }

  const isEmpty = messages.length === 0

  return (
    <div className="flex flex-col h-screen">
      {/* Header */}
      <div className="flex-shrink-0 px-6 py-4 border-b border-gray-800 flex items-center gap-3">
        <div className="w-8 h-8 rounded-lg bg-violet-600/20 flex items-center justify-center">
          <Bot size={16} className="text-violet-400" />
        </div>
        <div>
          <p className="text-sm font-semibold text-white">Xeno Copilot</p>
          <p className="text-xs text-gray-500">AI-native campaign assistant</p>
        </div>
        {loading && (
          <span className="ml-auto text-xs text-violet-400 flex items-center gap-1">
            <span className="w-1.5 h-1.5 rounded-full bg-violet-400 animate-pulse" />
            Thinking…
          </span>
        )}
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-4 py-4 space-y-4">
        {isEmpty && (
          <div className="flex flex-col items-center justify-center h-full gap-6 text-center pb-16">
            <div className="w-16 h-16 rounded-2xl bg-violet-600/20 flex items-center justify-center">
              <Sparkles size={28} className="text-violet-400" />
            </div>
            <div>
              <p className="text-lg font-semibold text-white mb-1">What would you like to do today?</p>
              <p className="text-sm text-gray-500">
                I can build segments, draft messages, launch campaigns, and track results.
              </p>
            </div>
            <div className="grid gap-2 w-full max-w-lg">
              {SUGGESTED.map(s => (
                <button
                  key={s}
                  onClick={() => sendMessage(s)}
                  className="text-left text-sm px-4 py-3 rounded-xl bg-gray-800 hover:bg-gray-700 border border-gray-700 hover:border-violet-600/50 text-gray-300 hover:text-white transition-all"
                >
                  {s}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((msg, i) => (
          <div
            key={i}
            className={`flex gap-3 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            {msg.role === 'assistant' && (
              <div className="w-7 h-7 rounded-full bg-violet-600/20 flex items-center justify-center flex-shrink-0 mt-1">
                <Bot size={14} className="text-violet-400" />
              </div>
            )}

            <div
              className={`max-w-[75%] rounded-2xl px-4 py-3 text-sm leading-relaxed whitespace-pre-wrap ${
                msg.role === 'user'
                  ? 'bg-violet-600 text-white rounded-br-md'
                  : 'bg-gray-800 text-gray-200 rounded-bl-md border border-gray-700'
              } ${msg.streaming ? 'cursor-blink' : ''}`}
            >
              {msg.content || (msg.streaming ? '' : '…')}
            </div>

            {msg.role === 'user' && (
              <div className="w-7 h-7 rounded-full bg-gray-700 flex items-center justify-center flex-shrink-0 mt-1">
                <User size={14} className="text-gray-400" />
              </div>
            )}
          </div>
        ))}

        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="flex-shrink-0 px-4 py-4 border-t border-gray-800">
        <div className="flex gap-3 items-end bg-gray-800 rounded-2xl border border-gray-700 focus-within:border-violet-600/60 px-4 py-3">
          <textarea
            ref={inputRef}
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={handleKey}
            placeholder="Describe a campaign goal or ask anything…"
            rows={1}
            disabled={loading}
            className="flex-1 bg-transparent text-sm text-white placeholder-gray-600 resize-none outline-none max-h-32"
            style={{ scrollbarWidth: 'none' }}
          />
          <button
            onClick={() => sendMessage(input)}
            disabled={!input.trim() || loading}
            className="w-8 h-8 rounded-xl bg-violet-600 hover:bg-violet-500 disabled:opacity-40 disabled:cursor-not-allowed flex items-center justify-center flex-shrink-0 transition-colors"
          >
            <Send size={14} className="text-white" />
          </button>
        </div>
        <p className="text-xs text-gray-700 text-center mt-2">
          Press Enter to send · Shift+Enter for newline
        </p>
      </div>
    </div>
  )
}
