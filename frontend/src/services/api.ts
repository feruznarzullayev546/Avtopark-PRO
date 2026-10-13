const BASE_URL = (import.meta as any).env?.VITE_API_URL || "https://avtopark-pro-2.onrender.com";
const API = `${BASE_URL.replace(/\/$/, "")}/api/v1`;

function getCookie(name: string) {
  return document.cookie.split("; ").find(row => row.startsWith(`${name}=`))?.split("=")[1];
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const method = (init?.method || "GET").toUpperCase();
  const headers = new Headers(init?.headers);
  headers.set("Accept", "application/json");
  headers.set("Accept-Language", localStorage.getItem("avtopark_lang") || "uz");
  const branchId = localStorage.getItem("avtopark_active_branch_id");
  if (branchId) headers.set("X-Branch-ID", branchId);
  if (method !== "GET" && method !== "HEAD") {
    if (!(init?.body instanceof FormData)) headers.set("Content-Type", "application/json");
    const csrf = getCookie("csrftoken");
    if (csrf) headers.set("X-CSRFToken", decodeURIComponent(csrf));
  }
  const res = await fetch(`${API}${path}`, { credentials: "include", ...init, headers });
  if (!res.ok) {
    let message = `API ${res.status}`;
    try { const body = await res.json(); if (body?.error) message = body.error; } catch {}
    throw new Error(message);
  }
  return res.json();
}

export const api = {
  csrf: () => request<{csrfToken:string}>("/csrf/"),
  login: async (username: string, password: string) => {
    // Har safar login qilishdan oldin serverdan CSRF token olib kelinadi
    await api.csrf();
    return request("/auth/login/", {
      method: "POST",
      body: JSON.stringify({ username, password })
    });
  },
  logout: () => request("/auth/logout/", {method:"POST"}),
  me: () => request<import("../types/api").Me>("/me/"),
  uploadAvatar: (file:File) => { const fd=new FormData(); fd.append("avatar",file); return request<any>("/auth/profile/avatar/", {method:"POST",body:fd}); },
  removeAvatar: () => request<any>("/auth/profile/avatar/", {method:"DELETE"}),
  chatContacts: () => request<any>("/chat/contacts/"),
  chatConversation: (userId:number) => request<any>(`/chat/${userId}/`),
  sendChatMessage: (userId:number,body:string) => request<any>(`/chat/${userId}/`, {method:"POST",body:JSON.stringify({body})}),
  companyContext: () => request<any>("/companies/context/"),
  switchCompany: (company_id:number) => request<any>("/companies/switch/", {method:"POST",body:JSON.stringify({company_id})}),
  createCompany: (data:any) => request<any>("/companies/create/", {method:"POST",body:JSON.stringify(data)}),
  updateCompany: (data:any) => request<any>("/companies/update/", {method:"PATCH",body:JSON.stringify(data)}),
  companyMembers: () => request<any>("/companies/members/"),
  inviteCompanyMember: (data:any) => request<any>("/companies/invite/", {method:"POST",body:JSON.stringify(data)}),
  updateCompanyMember: (id:number,data:any) => request<any>(`/companies/members/${id}/`, {method:"PATCH",body:JSON.stringify(data)}),
  enterpriseContext: () => request<any>("/enterprise/context/"),
  enterpriseControlPlane: () => request<any>("/enterprise/control-plane/"),
  switchOrganization: (organization_id:number) => request<any>("/enterprise/switch/", {method:"POST",body:JSON.stringify({organization_id})}),
  createOrganization: (data:any) => request<any>("/enterprise/organizations/create/", {method:"POST",body:JSON.stringify(data)}),
  branches: () => request<any>("/enterprise/branches/"),
  createBranch: (data:any) => request<any>("/enterprise/branches/create/", {method:"POST",body:JSON.stringify(data)}),
  switchBranch: (branch_id:number) => request<any>("/enterprise/branches/switch/", {method:"POST",body:JSON.stringify({branch_id})}),
  branchMembers: (branch_id:number) => request<any>(`/enterprise/branches/${branch_id}/members/`),
  upsertBranchMember: (branch_id:number,data:any) => request<any>(`/enterprise/branches/${branch_id}/members/upsert/`, {method:"POST",body:JSON.stringify(data)}),
  accessRoles: () => request<any>("/access/roles/"),
  createAccessRole: (data:any) => request<any>("/access/roles/create/", {method:"POST",body:JSON.stringify(data)}),
  updateAccessRole: (id:number,data:any) => request<any>(`/access/roles/${id}/`, {method:"PATCH",body:JSON.stringify(data)}),
  accessAudit: () => request<any>("/access/audit/?limit=200"),
  accessApprovals: () => request<any>("/access/approvals/"),
  requestApproval: (data:any) => request<any>("/access/approvals/request/", {method:"POST",body:JSON.stringify(data)}),
  decideApproval: (id:number,data:any) => request<any>(`/access/approvals/${id}/decide/`, {method:"POST",body:JSON.stringify(data)}),
  accessSecurity: () => request<any>("/access/security/"),
  billingOverview: () => request<any>("/billing/overview/"),
  platformOverview: () => request<any>("/platform/overview/"),
  platformCompanyStatus: (id:number,status:string) => request<any>(`/platform/company/${id}/status/`, {method:"POST",body:JSON.stringify({status})}),
  platformOrganizationStatus: (id:number,status:string) => request<any>(`/platform/organization/${id}/status/`, {method:"POST",body:JSON.stringify({status})}),
  platformSecurityEvents: () => request<any>("/platform/security-events/"),
  platformSessions: () => request<any>("/platform/sessions/"),
  platformRevokeSession: (id:number) => request<any>(`/platform/sessions/${id}/revoke/`, {method:"POST"}),
  changePlan: (data:any) => request<any>("/billing/change-plan/", {method:"POST",body:JSON.stringify(data)}),
  payInvoice: (id:number,data:any) => request<any>(`/billing/invoices/${id}/pay/`, {method:"POST",body:JSON.stringify(data)}),
  submitReceipt: (id:number,data:FormData) => request<any>(`/billing/invoices/${id}/receipt/`, {method:"POST",body:data}),
  adminPayments: () => request<any>("/billing/admin/payments/"),
  adminPaymentDecision: (id:number,data:any) => request<any>(`/billing/admin/payments/${id}/decide/`, {method:"POST",body:JSON.stringify(data)}),
  adminCards: () => request<any>("/billing/admin/cards/"),
  adminCardSave: (data:any) => request<any>("/billing/admin/cards/save/", {method:"POST",body:JSON.stringify(data)}),
  adminCardDelete: (id:number) => request<any>(`/billing/admin/cards/${id}/delete/`, {method:"POST"}),
  acceptCompanyInvite: (token:string) => request<any>("/companies/invitations/accept/", {method:"POST",body:JSON.stringify({token})}),
  dashboard: () => request<import("../pages/Dashboard").DashboardData>("/dashboard/"),
  vehicles: () => request("/vehicles/"),
  vehicleMeta: () => request<any>("/vehicles/meta/"),
  createVehicle: (data:any) => request("/vehicles/create/", {method:"POST",body:data instanceof FormData ? data : JSON.stringify(data)}),
  updateVehicle: (id:number,data:any) => request(`/vehicles/${id}/`, {method:"PATCH",body:data instanceof FormData ? data : JSON.stringify(data)}),
  createVehicleModel: (data:any) => request("/vehicles/models/create/", {method:"POST",body:JSON.stringify(data)}),
  register: (data:any) => request("/auth/register/", {method:"POST",body:JSON.stringify(data)}),
  deleteVehicle: (id:number) => request(`/vehicles/${id}/delete/`, {method:"DELETE"}),
  drivers: () => request("/drivers/"),
  createDriver: (data:any) => request("/drivers/create/", {method:"POST",body:JSON.stringify(data)}),
  updateDriver: (id:number,data:any) => request(`/drivers/${id}/`, {method:"PATCH",body:JSON.stringify(data)}),
  deleteDriver: (id:number) => request(`/drivers/${id}/delete/`, {method:"DELETE"}),
  routes: () => request("/routes/"),
  trips: () => request<{results: import("../pages/Trips").Trip[]}>("/trips/"),
  notifications: (companyId?:string) => request<any>(`/notifications/${companyId ? `?company_id=${encodeURIComponent(companyId)}` : ""}`),
  sendNotification: (data:any) => request<any>("/notifications/", {method:"POST",body:JSON.stringify(data)}),
  notificationCompanies: () => request<any>("/notifications/companies/"),
  manageNotification: (id:number,data?:any) => request<any>(`/notifications/${id}/manage/`, {method:data ? "PATCH" : "DELETE",...(data?{body:JSON.stringify(data)}:{})}),
  warehouse: () => request<any>("/warehouse/"),
  fuel: (params="") => request<any>(`/fuel/${params}`),
  fuelStations: () => request<any>("/fuel/stations/"),
  createFuelStation: (data:any) => request<any>("/fuel/stations/", {method:"POST",body:JSON.stringify(data)}),
  submitDriverGas: (data:any) => request<any>("/fuel/driver-submit/", {method:"POST",body:JSON.stringify(data)}),
  maintenance: () => request<any>("/maintenance/"),
  finance: (vehicle="") => request<any>(`/finance/${vehicle ? `?vehicle_id=${encodeURIComponent(vehicle)}` : ""}`),
  createOtherExpense: (data:any) => request("/finance/other/create/", {method:"POST",body:JSON.stringify(data)}),
  replacements: (vehicle="", service="") => request<any>(`/replacements/?vehicle=${encodeURIComponent(vehicle)}&service=${encodeURIComponent(service)}`),
  createMaintenance: (data:any) => request("/maintenance/create/", {method:"POST",body:JSON.stringify(data)}),
  updateMaintenance: (id:number,data:any) => request(`/maintenance/${id}/`, {method:"PATCH",body:JSON.stringify(data)}),
  completeMaintenance: (id:number,data:any) => request(`/maintenance/${id}/complete/`, {method:"POST",body:JSON.stringify(data)}),
  checkMaintenanceNotifications: () => request("/maintenance/check-notifications/", {method:"POST"}),
  createFuel: (data:any) => request("/fuel/create/", {method:"POST",body:JSON.stringify(data)}),
  updateFuel: (id:number,data:any) => request(`/fuel/${id}/`, {method:"PATCH",body:JSON.stringify(data)}),
  warehouseMeta: () => request<any>("/warehouse/meta/"),
  createWarehousePart: (data:any) => request("/warehouse/parts/create/", {method:"POST",body:JSON.stringify(data)}),
  updateWarehousePart: (id:number,data:any) => request(`/warehouse/parts/${id}/`, {method:"PATCH",body:JSON.stringify(data)}),
  createWarehouseReceipt: (data:any) => request("/warehouse/receipts/create/", {method:"POST",body:JSON.stringify(data)}),
  updateWarehouseReceipt: (id:number,data:any) => request(`/warehouse/receipts/${id}/`, {method:"PATCH",body:JSON.stringify(data)}),
  createWarehouseIssue: (data:any) => request("/warehouse/issues/create/", {method:"POST",body:JSON.stringify(data)}),
  updateWarehouseIssue: (id:number,data:any) => request(`/warehouse/issues/${id}/`, {method:"PATCH",body:JSON.stringify(data)}),
  createWarehouseReturn: (data:any) => request("/warehouse/returns/create/", {method:"POST",body:JSON.stringify(data)}),
  createWarehouseAdjustment: (data:any) => request("/warehouse/adjustments/create/", {method:"POST",body:JSON.stringify(data)}),
  warehouseCard: (id:number) => request<any>(`/warehouse/card/${id}/`),
  warehouseExport: () => `${API}/warehouse/export/`,
  readNotification: (id:number) => request(`/notifications/${id}/read/`, {method:"POST"}),
  readAllNotifications: () => request("/notifications/read-all/", {method:"POST"}),
  routeMeta: () => request<{routes: any[];drivers:any[]}>("/trips/meta/"),
  tripMeta: () => request<{routes: any[];drivers:any[]}>("/trips/meta/"),
  createRoute: (data:any) => request("/routes/create/", {method:"POST",body:JSON.stringify(data)}),
  updateRoute: (id:number,data:any) => request(`/routes/${id}/`, {method:"PATCH",body:JSON.stringify(data)}),
  deleteRoute: (id:number) => request(`/routes/${id}/delete/`, {method:"DELETE"}),
  toggleRoute: (id:number) => request(`/routes/${id}/toggle/`, {method:"POST"}),
  createTrip: (data:any) => request("/trips/create/", {method:"POST",body:JSON.stringify(data)}),
  acceptTrip: (id:number) => request(`/trips/${id}/accept/`, {method:"POST"}),
  startTrip: (id:number) => request(`/trips/${id}/start/`, {method:"POST"}),
  cancelTrip: (id:number,reason:string) => request(`/trips/${id}/cancel/`, {method:"POST",body:JSON.stringify({reason})}),
  completeTrip: (id:number) => request(`/trips/${id}/complete/`, {method:"POST"}),
  deleteTrip: (id:number) => request(`/trips/${id}/delete/`, {method:"DELETE"}),
  reviewCancellation: (id:number,data:any) => request(`/trips/${id}/review-cancel/`, {method:"POST",body:JSON.stringify(data)}),
};

export function chatWebSocket(userId:number): WebSocket {
  const configured = (import.meta as any).env?.VITE_WS_URL as string | undefined;
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const host = window.location.host.includes(':5173') ? '127.0.0.1:8000' : window.location.host;
  const base = configured || `${protocol}//${host}`;
  return new WebSocket(`${base.replace(/\/$/, '')}/ws/chat/${userId}/`);
}

export const apiConfig = {
    baseURL: BASE_URL,
};

export default BASE_URL;
