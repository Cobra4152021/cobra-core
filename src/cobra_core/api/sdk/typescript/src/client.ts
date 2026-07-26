/**
 * Cobra Public API TypeScript SDK (reference)
 * Authentication via Bearer (ISPF). Cursor pagination. Typed error model.
 */

export const SDK_VERSION = "0.1.0";

export interface CobraErrorBody {
  error_code: string;
  message: string;
  request_id?: string;
  timestamp?: number;
  documentation_url?: string;
}

export class CobraApiError extends Error {
  error_code: string;
  request_id: string;
  status: number;
  body: CobraErrorBody;

  constructor(status: number, body: CobraErrorBody) {
    super(body.message || "API error");
    this.name = "CobraApiError";
    this.status = status;
    this.error_code = body.error_code || "http_error";
    this.request_id = body.request_id || "";
    this.body = body;
  }
}

export interface Page<T> {
  data: T[];
  limit: number;
  cursor: string | null;
  next_cursor: string | null;
}

export interface CobraClientOptions {
  baseUrl: string;
  token: string;
  organizationId?: string;
  principalId?: string;
  fetchImpl?: typeof fetch;
}

export class CobraClient {
  private baseUrl: string;
  private token: string;
  private organizationId: string;
  private principalId: string;
  private fetchImpl: typeof fetch;

  constructor(opts: CobraClientOptions) {
    this.baseUrl = opts.baseUrl.replace(/\/$/, "");
    this.token = opts.token;
    this.organizationId = opts.organizationId || "";
    this.principalId = opts.principalId || "";
    this.fetchImpl = opts.fetchImpl || fetch;
  }

  private headers(): Record<string, string> {
    const h: Record<string, string> = {
      Authorization: `Bearer ${this.token}`,
      Accept: "application/json",
      "Content-Type": "application/json",
      "X-Cobra-Sdk-Version": `typescript/${SDK_VERSION}`,
    };
    if (this.organizationId) h["X-Cobra-Org-Id"] = this.organizationId;
    if (this.principalId) h["X-Cobra-Principal-Id"] = this.principalId;
    return h;
  }

  async request<T = Record<string, unknown>>(
    method: string,
    path: string,
    query?: Record<string, string | number | undefined>,
    body?: Record<string, unknown>
  ): Promise<T> {
    const qs = new URLSearchParams();
    if (query) {
      for (const [k, v] of Object.entries(query)) {
        if (v !== undefined && v !== null && String(v) !== "") qs.set(k, String(v));
      }
    }
    const url = `${this.baseUrl}${path}${qs.toString() ? `?${qs}` : ""}`;
    const resp = await this.fetchImpl(url, {
      method,
      headers: this.headers(),
      body: body ? JSON.stringify(body) : undefined,
    });
    const text = await resp.text();
    const payload = text ? JSON.parse(text) : {};
    if (!resp.ok) {
      throw new CobraApiError(resp.status, payload as CobraErrorBody);
    }
    return payload as T;
  }

  private async page<T>(
    path: string,
    limit = 25,
    cursor?: string | null
  ): Promise<Page<T>> {
    const body = await this.request<{
      data?: T[];
      pagination?: { limit?: number; cursor?: string | null; next_cursor?: string | null };
    }>("GET", path, { limit, cursor: cursor || undefined });
    const pag = body.pagination || {};
    return {
      data: body.data || [],
      limit: pag.limit ?? limit,
      cursor: pag.cursor ?? null,
      next_cursor: pag.next_cursor ?? null,
    };
  }

  health() {
    return this.request("GET", "/api/v1/health");
  }

  status() {
    return this.request("GET", "/api/v1/status");
  }

  listOrganizations(limit = 25, cursor?: string | null) {
    return this.page("/api/v1/organizations", limit, cursor);
  }

  createCase(fields: Record<string, unknown> = {}) {
    const body = { ...fields };
    if (this.organizationId && !body.organization_id) {
      body.organization_id = this.organizationId;
    }
    return this.request("POST", "/api/v1/cases", undefined, body);
  }

  runWorkflow(workflowId: string, fields: Record<string, unknown> = {}) {
    const body = { ...fields };
    if (this.organizationId && !body.organization_id) {
      body.organization_id = this.organizationId;
    }
    return this.request("POST", `/api/v1/workflows/${workflowId}/run`, undefined, body);
  }

  retrieveEvidence(evidenceId: string) {
    return this.request("GET", `/api/v1/evidence/${evidenceId}`);
  }

  getReport(reportId: string) {
    return this.request("GET", `/api/v1/reports/${reportId}`);
  }

  openapi() {
    return this.request("GET", "/api/v1/openapi.json");
  }
}
