/** GET /api/v1/providers list item. */
export interface ProviderInfo {
  id: string;
  name: string;
  status: "available" | "unavailable";
}

/** GET /api/v1/models list item. */
export interface ModelInfo {
  id: string;
  providerId: string;
  name: string;
  inputPricePer1k: number;
  outputPricePer1k: number;
}
