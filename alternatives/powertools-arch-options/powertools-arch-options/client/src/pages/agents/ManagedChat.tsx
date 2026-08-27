import { useState } from 'react';
import type { FormEvent } from 'react';
import { Alert, AlertDescription, Button, Card, CardContent, CardHeader, CardTitle, Input, Skeleton, useServingInvoke } from '@databricks/appkit-ui/react';

type Alias = 'option2' | 'option3';

export function ManagedChat({ alias, title, description }: { alias: Alias; title: string; description: string }) {
  const [input, setInput] = useState('');
  const [question, setQuestion] = useState('');
  const { invoke, data, loading, error } = useServingInvoke({}, { alias });
  const submit = async (event: FormEvent) => {
    event.preventDefault();
    const value = input.trim();
    if (!value) return;
    setQuestion(value);
    await invoke({ messages: [{ role: 'user', content: value }] });
  };
  return (
    <Card className="mt-4">
      <CardHeader><CardTitle>{title}</CardTitle><p className="text-sm text-muted-foreground">{description}</p></CardHeader>
      <CardContent className="space-y-4">
        <form onSubmit={(event) => { void submit(event); }} className="flex gap-2">
          <Input aria-label={`Question for ${title}`} value={input} onChange={(e) => setInput(e.target.value)} placeholder="Ask about product performance or a product manual…" />
          <Button type="submit" disabled={loading || !input.trim()}>{loading ? 'Running…' : 'Ask'}</Button>
        </form>
        {loading && <div className="space-y-2"><Skeleton className="h-4 w-full" /><Skeleton className="h-4 w-3/4" /></div>}
        {error && <Alert variant="destructive"><AlertDescription>{String(error)}</AlertDescription></Alert>}
        {!loading && !data && !error && <p className="py-8 text-center text-sm text-muted-foreground">Ask a question to see the supervisor response and raw tool evidence.</p>}
        {data != null && <div className="space-y-3"><p className="text-sm font-medium">{question}</p><pre className="max-h-[420px] overflow-auto whitespace-pre-wrap rounded-md bg-muted p-4 text-sm">{JSON.stringify(data, null, 2)}</pre></div>}
      </CardContent>
    </Card>
  );
}
