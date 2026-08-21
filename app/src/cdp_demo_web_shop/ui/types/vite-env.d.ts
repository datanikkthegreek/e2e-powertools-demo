/// <reference types="vite/client" />
declare const __APP_NAME__: string;

interface ImportMetaEnv {
  readonly VITE_GA4_MEASUREMENT_ID?: string;
  readonly VITE_GTM_TRANSPORT_URL?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
