import { useEffect, useState } from 'react';
import { Badge, Card, CardContent, Tabs, TabsContent, TabsList, TabsTrigger } from '@databricks/appkit-ui/react';
import { AgentChat } from './pages/agents/AgentChat';
import { ManagedChat } from './pages/agents/ManagedChat';

interface Identity { user: string; execution: string }

export default function App() {
  const [identity, setIdentity] = useState<Identity | null>(null);
  useEffect(() => { void fetch('/api/whoami').then((r) => r.json()).then(setIdentity); }, []);

  return (
    <main className="min-h-screen bg-background p-4 md:p-8">
      <div className="mx-auto max-w-5xl space-y-5">
        <div className="space-y-2">
          <Badge variant="secondary">Architecture comparison</Badge>
          <h1 className="text-3xl font-bold">Bosch Power Tools AI Assistants</h1>
          <p className="text-muted-foreground">Three ways to combine structured analytics and product-manual knowledge.</p>
        </div>
        <Card>
          <CardContent className="pt-4 text-sm text-muted-foreground">
            Signed in as <span className="font-medium text-foreground">{identity?.user ?? 'loading…'}</span>. {identity?.execution}
          </CardContent>
        </Card>
        <Tabs defaultValue="option2">
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="option2">Option 2 · Managed</TabsTrigger>
            <TabsTrigger value="option3">Option 3 · AI Search</TabsTrigger>
            <TabsTrigger value="option5">Option 5 · Custom</TabsTrigger>
          </TabsList>
          <TabsContent value="option2">
            <ManagedChat alias="option2" title="Knowledge Assistant + Supervisor" description="A volume-backed Knowledge Assistant and structured Genie, routed by a managed Supervisor Agent." />
          </TabsContent>
          <TabsContent value="option3">
            <ManagedChat alias="option3" title="AI Parse + AI Search + Supervisor" description="Parsed and prepared manuals indexed in AI Search, exposed through a Knowledge Assistant beside structured Genie." />
          </TabsContent>
          <TabsContent value="option5"><AgentChat /></TabsContent>
        </Tabs>
        <p className="text-xs text-muted-foreground">AI-generated answers can be inaccurate. Verify claims against the displayed tool evidence and source material.</p>
      </div>
    </main>
  );
}
