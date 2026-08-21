import { useQuery, useSuspenseQuery, useMutation } from "@tanstack/react-query";
import type { UseQueryOptions, UseSuspenseQueryOptions, UseMutationOptions } from "@tanstack/react-query";
export class ApiError extends Error {
    status: number;
    statusText: string;
    body: unknown;
    constructor(status: number, statusText: string, body: unknown){
        super(`HTTP ${status}: ${statusText}`);
        this.name = "ApiError";
        this.status = status;
        this.statusText = statusText;
        this.body = body;
    }
}
export interface AccountIn {
    city: string;
    country: string;
    date_of_birth: string;
    email: string;
    first_name: string;
    house_number: string;
    postal_code: string;
    street: string;
    surname: string;
}
export interface AccountOut {
    city: string;
    country: string;
    date_of_birth: string;
    email: string;
    first_name: string;
    house_number: string;
    id: string;
    postal_code: string;
    street: string;
    surname: string;
}
export interface AnalyticsOut {
    abandoned_carts: number;
    page_views: number;
    purchases: number;
    registrations: number;
    total_events: number;
}
export interface CartItemIn {
    product_id: string;
    quantity?: number;
}
export interface CartItemOut {
    account_id: string;
    cart_id?: string | null;
    id: string;
    line_total_eur: number;
    product: ProductOut;
    product_id: string;
    quantity: number;
}
export interface CartItemPatch {
    quantity: number;
}
export interface ComplexValue {
    display?: string | null;
    primary?: boolean | null;
    ref?: string | null;
    type?: string | null;
    value?: string | null;
}
export interface EventAck {
    status: string;
}
export interface EventIn {
    event_name: string;
    language?: string | null;
    page_location?: string | null;
    page_referrer?: string | null;
    page_title?: string | null;
    screen_resolution?: string | null;
    web_input_data: Record<string, unknown>;
}
export interface HTTPValidationError {
    detail?: ValidationError[];
}
export interface Name {
    family_name?: string | null;
    given_name?: string | null;
}
export interface PipelineRunOut {
    run_id: number;
    run_page_url?: string | null;
}
export interface PipelineRunStatusOut {
    finished: boolean;
    life_cycle_state?: string | null;
    result_state?: string | null;
    run_id: number;
}
export interface ProductDetailOut {
    description: string;
    id: string;
    image_url: string;
    long_description?: string | null;
    name: string;
    price_eur: number;
    specs?: Record<string, unknown> | null;
}
export interface ProductOut {
    description: string;
    id: string;
    image_url: string;
    name: string;
    price_eur: number;
}
export interface PurchaseLineOut {
    id: string;
    line_total_eur: number;
    name_snapshot: string;
    product_id: string;
    quantity: number;
    unit_price_eur: number;
}
export interface PurchaseOut {
    account_email: string;
    account_id: string;
    account_name: string;
    cart_id?: string | null;
    created_at: string;
    id: string;
    lines: PurchaseLineOut[];
    total_eur: number;
}
export interface TablePreviewOut {
    columns: string[];
    fqn: string;
    name: string;
    row_limit: number;
    rows: (string | null)[][];
    truncated: boolean;
}
export interface User {
    active?: boolean | null;
    display_name?: string | null;
    emails?: ComplexValue[] | null;
    entitlements?: ComplexValue[] | null;
    external_id?: string | null;
    groups?: ComplexValue[] | null;
    id?: string | null;
    name?: Name | null;
    roles?: ComplexValue[] | null;
    schemas?: UserSchema[] | null;
    user_name?: string | null;
}
export const UserSchema = {
    "urn:ietf:params:scim:schemas:core:2.0:User": "urn:ietf:params:scim:schemas:core:2.0:User",
    "urn:ietf:params:scim:schemas:extension:workspace:2.0:User": "urn:ietf:params:scim:schemas:extension:workspace:2.0:User"
} as const;
export type UserSchema = typeof UserSchema[keyof typeof UserSchema];
export interface ValidationError {
    ctx?: Record<string, unknown>;
    input?: unknown;
    loc: (string | number)[];
    msg: string;
    type: string;
}
export interface VersionOut {
    version: string;
}
export const listAccounts = async (options?: RequestInit): Promise<{
    data: AccountOut[];
}> =>{
    const res = await fetch("/api/accounts", {
        ...options,
        method: "GET"
    });
    if (!res.ok) {
        const body = await res.text();
        let parsed: unknown;
        try {
            parsed = JSON.parse(body);
        } catch  {
            parsed = body;
        }
        throw new ApiError(res.status, res.statusText, parsed);
    }
    return {
        data: await res.json()
    };
};
export const listAccountsKey = ()=>{
    return [
        "/api/accounts"
    ] as const;
};
export function useListAccounts<TData = {
    data: AccountOut[];
}>(options?: {
    query?: Omit<UseQueryOptions<{
        data: AccountOut[];
    }, ApiError, TData>, "queryKey" | "queryFn">;
}) {
    return useQuery({
        queryKey: listAccountsKey(),
        queryFn: ()=>listAccounts(),
        ...options?.query
    });
}
export function useListAccountsSuspense<TData = {
    data: AccountOut[];
}>(options?: {
    query?: Omit<UseSuspenseQueryOptions<{
        data: AccountOut[];
    }, ApiError, TData>, "queryKey" | "queryFn">;
}) {
    return useSuspenseQuery({
        queryKey: listAccountsKey(),
        queryFn: ()=>listAccounts(),
        ...options?.query
    });
}
export const createAccount = async (data: AccountIn, options?: RequestInit): Promise<{
    data: AccountOut;
}> =>{
    const res = await fetch("/api/accounts", {
        ...options,
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            ...options?.headers
        },
        body: JSON.stringify(data)
    });
    if (!res.ok) {
        const body = await res.text();
        let parsed: unknown;
        try {
            parsed = JSON.parse(body);
        } catch  {
            parsed = body;
        }
        throw new ApiError(res.status, res.statusText, parsed);
    }
    return {
        data: await res.json()
    };
};
export function useCreateAccount(options?: {
    mutation?: UseMutationOptions<{
        data: AccountOut;
    }, ApiError, AccountIn>;
}) {
    return useMutation({
        mutationFn: (data)=>createAccount(data),
        ...options?.mutation
    });
}
export interface GetAccountParams {
    account_id: string;
}
export const getAccount = async (params: GetAccountParams, options?: RequestInit): Promise<{
    data: AccountOut;
}> =>{
    const res = await fetch(`/api/accounts/${params.account_id}`, {
        ...options,
        method: "GET"
    });
    if (!res.ok) {
        const body = await res.text();
        let parsed: unknown;
        try {
            parsed = JSON.parse(body);
        } catch  {
            parsed = body;
        }
        throw new ApiError(res.status, res.statusText, parsed);
    }
    return {
        data: await res.json()
    };
};
export const getAccountKey = (params?: GetAccountParams)=>{
    return [
        "/api/accounts/{account_id}",
        params
    ] as const;
};
export function useGetAccount<TData = {
    data: AccountOut;
}>(options: {
    params: GetAccountParams;
    query?: Omit<UseQueryOptions<{
        data: AccountOut;
    }, ApiError, TData>, "queryKey" | "queryFn">;
}) {
    return useQuery({
        queryKey: getAccountKey(options.params),
        queryFn: ()=>getAccount(options.params),
        ...options?.query
    });
}
export function useGetAccountSuspense<TData = {
    data: AccountOut;
}>(options: {
    params: GetAccountParams;
    query?: Omit<UseSuspenseQueryOptions<{
        data: AccountOut;
    }, ApiError, TData>, "queryKey" | "queryFn">;
}) {
    return useSuspenseQuery({
        queryKey: getAccountKey(options.params),
        queryFn: ()=>getAccount(options.params),
        ...options?.query
    });
}
export interface DeleteAccountParams {
    account_id: string;
}
export const deleteAccount = async (params: DeleteAccountParams, options?: RequestInit): Promise<void> =>{
    const res = await fetch(`/api/accounts/${params.account_id}`, {
        ...options,
        method: "DELETE"
    });
    if (!res.ok) {
        const body = await res.text();
        let parsed: unknown;
        try {
            parsed = JSON.parse(body);
        } catch  {
            parsed = body;
        }
        throw new ApiError(res.status, res.statusText, parsed);
    }
    return;
};
export function useDeleteAccount(options?: {
    mutation?: UseMutationOptions<void, ApiError, {
        params: DeleteAccountParams;
    }>;
}) {
    return useMutation({
        mutationFn: (vars)=>deleteAccount(vars.params),
        ...options?.mutation
    });
}
export interface GetCartParams {
    account_id: string;
}
export const getCart = async (params: GetCartParams, options?: RequestInit): Promise<{
    data: CartItemOut[];
}> =>{
    const res = await fetch(`/api/accounts/${params.account_id}/cart`, {
        ...options,
        method: "GET"
    });
    if (!res.ok) {
        const body = await res.text();
        let parsed: unknown;
        try {
            parsed = JSON.parse(body);
        } catch  {
            parsed = body;
        }
        throw new ApiError(res.status, res.statusText, parsed);
    }
    return {
        data: await res.json()
    };
};
export const getCartKey = (params?: GetCartParams)=>{
    return [
        "/api/accounts/{account_id}/cart",
        params
    ] as const;
};
export function useGetCart<TData = {
    data: CartItemOut[];
}>(options: {
    params: GetCartParams;
    query?: Omit<UseQueryOptions<{
        data: CartItemOut[];
    }, ApiError, TData>, "queryKey" | "queryFn">;
}) {
    return useQuery({
        queryKey: getCartKey(options.params),
        queryFn: ()=>getCart(options.params),
        ...options?.query
    });
}
export function useGetCartSuspense<TData = {
    data: CartItemOut[];
}>(options: {
    params: GetCartParams;
    query?: Omit<UseSuspenseQueryOptions<{
        data: CartItemOut[];
    }, ApiError, TData>, "queryKey" | "queryFn">;
}) {
    return useSuspenseQuery({
        queryKey: getCartKey(options.params),
        queryFn: ()=>getCart(options.params),
        ...options?.query
    });
}
export interface AddToCartParams {
    account_id: string;
}
export const addToCart = async (params: AddToCartParams, data: CartItemIn, options?: RequestInit): Promise<{
    data: CartItemOut;
}> =>{
    const res = await fetch(`/api/accounts/${params.account_id}/cart`, {
        ...options,
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            ...options?.headers
        },
        body: JSON.stringify(data)
    });
    if (!res.ok) {
        const body = await res.text();
        let parsed: unknown;
        try {
            parsed = JSON.parse(body);
        } catch  {
            parsed = body;
        }
        throw new ApiError(res.status, res.statusText, parsed);
    }
    return {
        data: await res.json()
    };
};
export function useAddToCart(options?: {
    mutation?: UseMutationOptions<{
        data: CartItemOut;
    }, ApiError, {
        params: AddToCartParams;
        data: CartItemIn;
    }>;
}) {
    return useMutation({
        mutationFn: (vars)=>addToCart(vars.params, vars.data),
        ...options?.mutation
    });
}
export interface ClearCartParams {
    account_id: string;
}
export const clearCart = async (params: ClearCartParams, options?: RequestInit): Promise<void> =>{
    const res = await fetch(`/api/accounts/${params.account_id}/cart`, {
        ...options,
        method: "DELETE"
    });
    if (!res.ok) {
        const body = await res.text();
        let parsed: unknown;
        try {
            parsed = JSON.parse(body);
        } catch  {
            parsed = body;
        }
        throw new ApiError(res.status, res.statusText, parsed);
    }
    return;
};
export function useClearCart(options?: {
    mutation?: UseMutationOptions<void, ApiError, {
        params: ClearCartParams;
    }>;
}) {
    return useMutation({
        mutationFn: (vars)=>clearCart(vars.params),
        ...options?.mutation
    });
}
export interface UpdateCartItemParams {
    account_id: string;
    product_id: string;
}
export const updateCartItem = async (params: UpdateCartItemParams, data: CartItemPatch, options?: RequestInit): Promise<{
    data: CartItemOut;
}> =>{
    const res = await fetch(`/api/accounts/${params.account_id}/cart/${params.product_id}`, {
        ...options,
        method: "PATCH",
        headers: {
            "Content-Type": "application/json",
            ...options?.headers
        },
        body: JSON.stringify(data)
    });
    if (!res.ok) {
        const body = await res.text();
        let parsed: unknown;
        try {
            parsed = JSON.parse(body);
        } catch  {
            parsed = body;
        }
        throw new ApiError(res.status, res.statusText, parsed);
    }
    return {
        data: await res.json()
    };
};
export function useUpdateCartItem(options?: {
    mutation?: UseMutationOptions<{
        data: CartItemOut;
    }, ApiError, {
        params: UpdateCartItemParams;
        data: CartItemPatch;
    }>;
}) {
    return useMutation({
        mutationFn: (vars)=>updateCartItem(vars.params, vars.data),
        ...options?.mutation
    });
}
export interface RemoveCartItemParams {
    account_id: string;
    product_id: string;
}
export const removeCartItem = async (params: RemoveCartItemParams, options?: RequestInit): Promise<void> =>{
    const res = await fetch(`/api/accounts/${params.account_id}/cart/${params.product_id}`, {
        ...options,
        method: "DELETE"
    });
    if (!res.ok) {
        const body = await res.text();
        let parsed: unknown;
        try {
            parsed = JSON.parse(body);
        } catch  {
            parsed = body;
        }
        throw new ApiError(res.status, res.statusText, parsed);
    }
    return;
};
export function useRemoveCartItem(options?: {
    mutation?: UseMutationOptions<void, ApiError, {
        params: RemoveCartItemParams;
    }>;
}) {
    return useMutation({
        mutationFn: (vars)=>removeCartItem(vars.params),
        ...options?.mutation
    });
}
export interface CheckoutParams {
    account_id: string;
}
export const checkout = async (params: CheckoutParams, options?: RequestInit): Promise<{
    data: PurchaseOut;
}> =>{
    const res = await fetch(`/api/accounts/${params.account_id}/checkout`, {
        ...options,
        method: "POST"
    });
    if (!res.ok) {
        const body = await res.text();
        let parsed: unknown;
        try {
            parsed = JSON.parse(body);
        } catch  {
            parsed = body;
        }
        throw new ApiError(res.status, res.statusText, parsed);
    }
    return {
        data: await res.json()
    };
};
export function useCheckout(options?: {
    mutation?: UseMutationOptions<{
        data: PurchaseOut;
    }, ApiError, {
        params: CheckoutParams;
    }>;
}) {
    return useMutation({
        mutationFn: (vars)=>checkout(vars.params),
        ...options?.mutation
    });
}
export const analyticsOverview = async (options?: RequestInit): Promise<{
    data: AnalyticsOut;
}> =>{
    const res = await fetch("/api/analytics/overview", {
        ...options,
        method: "GET"
    });
    if (!res.ok) {
        const body = await res.text();
        let parsed: unknown;
        try {
            parsed = JSON.parse(body);
        } catch  {
            parsed = body;
        }
        throw new ApiError(res.status, res.statusText, parsed);
    }
    return {
        data: await res.json()
    };
};
export const analyticsOverviewKey = ()=>{
    return [
        "/api/analytics/overview"
    ] as const;
};
export function useAnalyticsOverview<TData = {
    data: AnalyticsOut;
}>(options?: {
    query?: Omit<UseQueryOptions<{
        data: AnalyticsOut;
    }, ApiError, TData>, "queryKey" | "queryFn">;
}) {
    return useQuery({
        queryKey: analyticsOverviewKey(),
        queryFn: ()=>analyticsOverview(),
        ...options?.query
    });
}
export function useAnalyticsOverviewSuspense<TData = {
    data: AnalyticsOut;
}>(options?: {
    query?: Omit<UseSuspenseQueryOptions<{
        data: AnalyticsOut;
    }, ApiError, TData>, "queryKey" | "queryFn">;
}) {
    return useSuspenseQuery({
        queryKey: analyticsOverviewKey(),
        queryFn: ()=>analyticsOverview(),
        ...options?.query
    });
}
export interface TablePreviewParams {
    table_key: string;
}
export const tablePreview = async (params: TablePreviewParams, options?: RequestInit): Promise<{
    data: TablePreviewOut;
}> =>{
    const res = await fetch(`/api/analytics/tables/${params.table_key}`, {
        ...options,
        method: "GET"
    });
    if (!res.ok) {
        const body = await res.text();
        let parsed: unknown;
        try {
            parsed = JSON.parse(body);
        } catch  {
            parsed = body;
        }
        throw new ApiError(res.status, res.statusText, parsed);
    }
    return {
        data: await res.json()
    };
};
export const tablePreviewKey = (params?: TablePreviewParams)=>{
    return [
        "/api/analytics/tables/{table_key}",
        params
    ] as const;
};
export function useTablePreview<TData = {
    data: TablePreviewOut;
}>(options: {
    params: TablePreviewParams;
    query?: Omit<UseQueryOptions<{
        data: TablePreviewOut;
    }, ApiError, TData>, "queryKey" | "queryFn">;
}) {
    return useQuery({
        queryKey: tablePreviewKey(options.params),
        queryFn: ()=>tablePreview(options.params),
        ...options?.query
    });
}
export function useTablePreviewSuspense<TData = {
    data: TablePreviewOut;
}>(options: {
    params: TablePreviewParams;
    query?: Omit<UseSuspenseQueryOptions<{
        data: TablePreviewOut;
    }, ApiError, TData>, "queryKey" | "queryFn">;
}) {
    return useSuspenseQuery({
        queryKey: tablePreviewKey(options.params),
        queryFn: ()=>tablePreview(options.params),
        ...options?.query
    });
}
export interface CurrentUserParams {
    "X-Forwarded-Host"?: string | null;
    "X-Forwarded-Preferred-Username"?: string | null;
    "X-Forwarded-User"?: string | null;
    "X-Forwarded-Email"?: string | null;
    "X-Request-Id"?: string | null;
    "X-Forwarded-Access-Token"?: string | null;
}
export const currentUser = async (params?: CurrentUserParams, options?: RequestInit): Promise<{
    data: User;
}> =>{
    const res = await fetch("/api/current-user", {
        ...options,
        method: "GET",
        headers: {
            ...(params?.["X-Forwarded-Host"] != null && {
                "X-Forwarded-Host": params["X-Forwarded-Host"]
            }),
            ...(params?.["X-Forwarded-Preferred-Username"] != null && {
                "X-Forwarded-Preferred-Username": params["X-Forwarded-Preferred-Username"]
            }),
            ...(params?.["X-Forwarded-User"] != null && {
                "X-Forwarded-User": params["X-Forwarded-User"]
            }),
            ...(params?.["X-Forwarded-Email"] != null && {
                "X-Forwarded-Email": params["X-Forwarded-Email"]
            }),
            ...(params?.["X-Request-Id"] != null && {
                "X-Request-Id": params["X-Request-Id"]
            }),
            ...(params?.["X-Forwarded-Access-Token"] != null && {
                "X-Forwarded-Access-Token": params["X-Forwarded-Access-Token"]
            }),
            ...options?.headers
        }
    });
    if (!res.ok) {
        const body = await res.text();
        let parsed: unknown;
        try {
            parsed = JSON.parse(body);
        } catch  {
            parsed = body;
        }
        throw new ApiError(res.status, res.statusText, parsed);
    }
    return {
        data: await res.json()
    };
};
export const currentUserKey = (params?: CurrentUserParams)=>{
    return [
        "/api/current-user",
        params
    ] as const;
};
export function useCurrentUser<TData = {
    data: User;
}>(options?: {
    params?: CurrentUserParams;
    query?: Omit<UseQueryOptions<{
        data: User;
    }, ApiError, TData>, "queryKey" | "queryFn">;
}) {
    return useQuery({
        queryKey: currentUserKey(options?.params),
        queryFn: ()=>currentUser(options?.params),
        ...options?.query
    });
}
export function useCurrentUserSuspense<TData = {
    data: User;
}>(options?: {
    params?: CurrentUserParams;
    query?: Omit<UseSuspenseQueryOptions<{
        data: User;
    }, ApiError, TData>, "queryKey" | "queryFn">;
}) {
    return useSuspenseQuery({
        queryKey: currentUserKey(options?.params),
        queryFn: ()=>currentUser(options?.params),
        ...options?.query
    });
}
export const ingestEvent = async (data: EventIn, options?: RequestInit): Promise<{
    data: EventAck;
}> =>{
    const res = await fetch("/api/events", {
        ...options,
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            ...options?.headers
        },
        body: JSON.stringify(data)
    });
    if (!res.ok) {
        const body = await res.text();
        let parsed: unknown;
        try {
            parsed = JSON.parse(body);
        } catch  {
            parsed = body;
        }
        throw new ApiError(res.status, res.statusText, parsed);
    }
    return {
        data: await res.json()
    };
};
export function useIngestEvent(options?: {
    mutation?: UseMutationOptions<{
        data: EventAck;
    }, ApiError, EventIn>;
}) {
    return useMutation({
        mutationFn: (data)=>ingestEvent(data),
        ...options?.mutation
    });
}
export const runTriggeredPipeline = async (options?: RequestInit): Promise<{
    data: PipelineRunOut;
}> =>{
    const res = await fetch("/api/jobs/triggered-pipeline/run", {
        ...options,
        method: "POST"
    });
    if (!res.ok) {
        const body = await res.text();
        let parsed: unknown;
        try {
            parsed = JSON.parse(body);
        } catch  {
            parsed = body;
        }
        throw new ApiError(res.status, res.statusText, parsed);
    }
    return {
        data: await res.json()
    };
};
export function useRunTriggeredPipeline(options?: {
    mutation?: UseMutationOptions<{
        data: PipelineRunOut;
    }, ApiError, void>;
}) {
    return useMutation({
        mutationFn: ()=>runTriggeredPipeline(),
        ...options?.mutation
    });
}
export interface GetTriggeredPipelineRunParams {
    run_id: number;
}
export const getTriggeredPipelineRun = async (params: GetTriggeredPipelineRunParams, options?: RequestInit): Promise<{
    data: PipelineRunStatusOut;
}> =>{
    const res = await fetch(`/api/jobs/triggered-pipeline/runs/${params.run_id}`, {
        ...options,
        method: "GET"
    });
    if (!res.ok) {
        const body = await res.text();
        let parsed: unknown;
        try {
            parsed = JSON.parse(body);
        } catch  {
            parsed = body;
        }
        throw new ApiError(res.status, res.statusText, parsed);
    }
    return {
        data: await res.json()
    };
};
export const getTriggeredPipelineRunKey = (params?: GetTriggeredPipelineRunParams)=>{
    return [
        "/api/jobs/triggered-pipeline/runs/{run_id}",
        params
    ] as const;
};
export function useGetTriggeredPipelineRun<TData = {
    data: PipelineRunStatusOut;
}>(options: {
    params: GetTriggeredPipelineRunParams;
    query?: Omit<UseQueryOptions<{
        data: PipelineRunStatusOut;
    }, ApiError, TData>, "queryKey" | "queryFn">;
}) {
    return useQuery({
        queryKey: getTriggeredPipelineRunKey(options.params),
        queryFn: ()=>getTriggeredPipelineRun(options.params),
        ...options?.query
    });
}
export function useGetTriggeredPipelineRunSuspense<TData = {
    data: PipelineRunStatusOut;
}>(options: {
    params: GetTriggeredPipelineRunParams;
    query?: Omit<UseSuspenseQueryOptions<{
        data: PipelineRunStatusOut;
    }, ApiError, TData>, "queryKey" | "queryFn">;
}) {
    return useSuspenseQuery({
        queryKey: getTriggeredPipelineRunKey(options.params),
        queryFn: ()=>getTriggeredPipelineRun(options.params),
        ...options?.query
    });
}
export const listProducts = async (options?: RequestInit): Promise<{
    data: ProductOut[];
}> =>{
    const res = await fetch("/api/products", {
        ...options,
        method: "GET"
    });
    if (!res.ok) {
        const body = await res.text();
        let parsed: unknown;
        try {
            parsed = JSON.parse(body);
        } catch  {
            parsed = body;
        }
        throw new ApiError(res.status, res.statusText, parsed);
    }
    return {
        data: await res.json()
    };
};
export const listProductsKey = ()=>{
    return [
        "/api/products"
    ] as const;
};
export function useListProducts<TData = {
    data: ProductOut[];
}>(options?: {
    query?: Omit<UseQueryOptions<{
        data: ProductOut[];
    }, ApiError, TData>, "queryKey" | "queryFn">;
}) {
    return useQuery({
        queryKey: listProductsKey(),
        queryFn: ()=>listProducts(),
        ...options?.query
    });
}
export function useListProductsSuspense<TData = {
    data: ProductOut[];
}>(options?: {
    query?: Omit<UseSuspenseQueryOptions<{
        data: ProductOut[];
    }, ApiError, TData>, "queryKey" | "queryFn">;
}) {
    return useSuspenseQuery({
        queryKey: listProductsKey(),
        queryFn: ()=>listProducts(),
        ...options?.query
    });
}
export interface GetProductParams {
    product_id: string;
}
export const getProduct = async (params: GetProductParams, options?: RequestInit): Promise<{
    data: ProductDetailOut;
}> =>{
    const res = await fetch(`/api/products/${params.product_id}`, {
        ...options,
        method: "GET"
    });
    if (!res.ok) {
        const body = await res.text();
        let parsed: unknown;
        try {
            parsed = JSON.parse(body);
        } catch  {
            parsed = body;
        }
        throw new ApiError(res.status, res.statusText, parsed);
    }
    return {
        data: await res.json()
    };
};
export const getProductKey = (params?: GetProductParams)=>{
    return [
        "/api/products/{product_id}",
        params
    ] as const;
};
export function useGetProduct<TData = {
    data: ProductDetailOut;
}>(options: {
    params: GetProductParams;
    query?: Omit<UseQueryOptions<{
        data: ProductDetailOut;
    }, ApiError, TData>, "queryKey" | "queryFn">;
}) {
    return useQuery({
        queryKey: getProductKey(options.params),
        queryFn: ()=>getProduct(options.params),
        ...options?.query
    });
}
export function useGetProductSuspense<TData = {
    data: ProductDetailOut;
}>(options: {
    params: GetProductParams;
    query?: Omit<UseSuspenseQueryOptions<{
        data: ProductDetailOut;
    }, ApiError, TData>, "queryKey" | "queryFn">;
}) {
    return useSuspenseQuery({
        queryKey: getProductKey(options.params),
        queryFn: ()=>getProduct(options.params),
        ...options?.query
    });
}
export const listPurchases = async (options?: RequestInit): Promise<{
    data: PurchaseOut[];
}> =>{
    const res = await fetch("/api/purchases", {
        ...options,
        method: "GET"
    });
    if (!res.ok) {
        const body = await res.text();
        let parsed: unknown;
        try {
            parsed = JSON.parse(body);
        } catch  {
            parsed = body;
        }
        throw new ApiError(res.status, res.statusText, parsed);
    }
    return {
        data: await res.json()
    };
};
export const listPurchasesKey = ()=>{
    return [
        "/api/purchases"
    ] as const;
};
export function useListPurchases<TData = {
    data: PurchaseOut[];
}>(options?: {
    query?: Omit<UseQueryOptions<{
        data: PurchaseOut[];
    }, ApiError, TData>, "queryKey" | "queryFn">;
}) {
    return useQuery({
        queryKey: listPurchasesKey(),
        queryFn: ()=>listPurchases(),
        ...options?.query
    });
}
export function useListPurchasesSuspense<TData = {
    data: PurchaseOut[];
}>(options?: {
    query?: Omit<UseSuspenseQueryOptions<{
        data: PurchaseOut[];
    }, ApiError, TData>, "queryKey" | "queryFn">;
}) {
    return useSuspenseQuery({
        queryKey: listPurchasesKey(),
        queryFn: ()=>listPurchases(),
        ...options?.query
    });
}
export interface DeletePurchaseParams {
    purchase_id: string;
}
export const deletePurchase = async (params: DeletePurchaseParams, options?: RequestInit): Promise<void> =>{
    const res = await fetch(`/api/purchases/${params.purchase_id}`, {
        ...options,
        method: "DELETE"
    });
    if (!res.ok) {
        const body = await res.text();
        let parsed: unknown;
        try {
            parsed = JSON.parse(body);
        } catch  {
            parsed = body;
        }
        throw new ApiError(res.status, res.statusText, parsed);
    }
    return;
};
export function useDeletePurchase(options?: {
    mutation?: UseMutationOptions<void, ApiError, {
        params: DeletePurchaseParams;
    }>;
}) {
    return useMutation({
        mutationFn: (vars)=>deletePurchase(vars.params),
        ...options?.mutation
    });
}
export const version = async (options?: RequestInit): Promise<{
    data: VersionOut;
}> =>{
    const res = await fetch("/api/version", {
        ...options,
        method: "GET"
    });
    if (!res.ok) {
        const body = await res.text();
        let parsed: unknown;
        try {
            parsed = JSON.parse(body);
        } catch  {
            parsed = body;
        }
        throw new ApiError(res.status, res.statusText, parsed);
    }
    return {
        data: await res.json()
    };
};
export const versionKey = ()=>{
    return [
        "/api/version"
    ] as const;
};
export function useVersion<TData = {
    data: VersionOut;
}>(options?: {
    query?: Omit<UseQueryOptions<{
        data: VersionOut;
    }, ApiError, TData>, "queryKey" | "queryFn">;
}) {
    return useQuery({
        queryKey: versionKey(),
        queryFn: ()=>version(),
        ...options?.query
    });
}
export function useVersionSuspense<TData = {
    data: VersionOut;
}>(options?: {
    query?: Omit<UseSuspenseQueryOptions<{
        data: VersionOut;
    }, ApiError, TData>, "queryKey" | "queryFn">;
}) {
    return useSuspenseQuery({
        queryKey: versionKey(),
        queryFn: ()=>version(),
        ...options?.query
    });
}
