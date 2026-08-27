import { analytics, createApp, server, serving } from '@databricks/appkit';
import { agents, aiSearch, createAgent, DatabricksAdapter, supervisorTools } from '@databricks/appkit/beta';

const option5 = createAgent({
  instructions: 'You are the Bosch Power Tools custom assistant. Route manual questions to manual_search and use the structured functions for product performance, revenue, and specifications. Cite tool evidence and say when evidence is insufficient.',
  model: DatabricksAdapter.fromSupervisorApi({ model: 'databricks-claude-sonnet-4-5' }),
  tools: () => ({
    manual_search: supervisorTools.ucFunction({
      name: 'nikks_fevm_workspace_7405607030687545.techsummit.option5_search_manuals',
      description: 'Search Bosch Power Tools product manuals using the Option 5 AI Search index.',
    }),
    product_performance: supervisorTools.ucFunction({
      name: 'nikks_fevm_workspace_7405607030687545.techsummit.option5_product_performance',
      description: 'Return product sales and performance metrics for Bosch Power Tools products.',
    }),
    revenue_by_country: supervisorTools.ucFunction({
      name: 'nikks_fevm_workspace_7405607030687545.techsummit.option5_revenue_by_country',
      description: 'Return Bosch Power Tools revenue grouped by country.',
    }),
    product_specs: supervisorTools.ucFunction({
      name: 'nikks_fevm_workspace_7405607030687545.techsummit.option5_product_specs',
      description: 'Return structured Bosch Power Tools product specifications.',
    }),
  }),
});

createApp({
  plugins: [
    agents({ agents: { option5 }, defaultAgent: 'option5', dir: false }),
    aiSearch({ indexes: { default: { columns: ['chunk_id', 'chunk_to_retrieve', 'source_path'] } } }),
    analytics(),
    serving({ endpoints: {
      option2: { env: 'DATABRICKS_OPTION2_ENDPOINT' },
      option3: { env: 'DATABRICKS_OPTION3_ENDPOINT' },
    } }),
    server(),
  ],
  onPluginsReady(appkit) {
    appkit.server.extend((app) => {
      app.get('/api/whoami', (req, res) => res.json({
        user: req.header('x-forwarded-email') ?? req.header('x-forwarded-user') ?? 'unknown',
        execution: 'The UI identifies the signed-in user. Agent calls run with the app resource credentials because serving OBO scope is unavailable in this workspace.',
      }));
    });
  },
}).catch(console.error);
