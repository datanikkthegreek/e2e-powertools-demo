import { useEffect, useRef, useState } from 'react';
import type { FormEvent } from 'react';
import { type AgentChatEvent, Alert, AlertDescription, Button, Card, CardContent, CardHeader, CardTitle, Input, useAgentChat } from '@databricks/appkit-ui/react';

interface Message { id: string; role: 'user' | 'assistant' | 'tool'; content: string; toolName?: string }

export function AgentChat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [pending, setPending] = useState<string | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);
  const onEvent = (event: AgentChatEvent) => {
    if (event.type === 'response.output_item.added' && event.item?.type === 'function_call') {
      setMessages((items) => [...items, { id: crypto.randomUUID(), role: 'tool', toolName: event.item?.name, content: event.item?.arguments ?? '' }]);
    }
  };
  const { content, isStreaming, error, send } = useAgentChat({ agent: 'option5', onEvent });
  useEffect(() => {
    // Streaming content is mirrored into the pending transcript row.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    if (pending) setMessages((items) => items.map((item) => item.id === pending ? { ...item, content } : item));
  }, [content, pending]);
  useEffect(() => { scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight }); }, [messages]);
  const submit = async (event: FormEvent) => {
    event.preventDefault();
    const value = input.trim();
    if (!value || isStreaming) return;
    const assistantId = crypto.randomUUID();
    setMessages((items) => [...items, { id: crypto.randomUUID(), role: 'user', content: value }, { id: assistantId, role: 'assistant', content: '' }]);
    setInput(''); setPending(assistantId); await send(value); setPending(null);
  };
  return (
    <Card className="mt-4">
      <CardHeader><CardTitle>Custom Agent Framework</CardTitle><p className="text-sm text-muted-foreground">A custom AppKit agent routes directly to AI Search and structured Unity Catalog functions.</p></CardHeader>
      <CardContent className="space-y-4">
        <div ref={scrollRef} className="max-h-[420px] min-h-48 space-y-3 overflow-auto">
          {messages.length === 0 && <p className="py-16 text-center text-sm text-muted-foreground">Ask a question to see the custom agent and its tool calls.</p>}
          {messages.map((message) => message.role === 'tool' ?
            <div key={message.id} className="border-l-2 pl-3 text-xs text-muted-foreground"><span className="font-semibold">tool · {message.toolName}</span><pre className="whitespace-pre-wrap">{message.content}</pre></div> :
            <div key={message.id} className={`rounded-md p-3 text-sm ${message.role === 'user' ? 'ml-12 bg-primary/10' : 'mr-12 bg-muted'}`}><div className="mb-1 text-xs text-muted-foreground">{message.role}</div><div className="whitespace-pre-wrap">{message.content || '…'}</div></div>)}
        </div>
        {error && <Alert variant="destructive"><AlertDescription>{error}</AlertDescription></Alert>}
        <form onSubmit={(event) => { void submit(event); }} className="flex gap-2"><Input aria-label="Question for custom agent" value={input} onChange={(e) => setInput(e.target.value)} placeholder="Ask about product performance or a product manual…" /><Button type="submit" disabled={isStreaming || !input.trim()}>{isStreaming ? 'Running…' : 'Ask'}</Button></form>
      </CardContent>
    </Card>
  );
}
