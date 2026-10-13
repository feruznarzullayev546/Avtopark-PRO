export type Role = "DIRECTOR" | "MANAGER" | "DRIVER" | "ACCOUNTANT" | "WAREHOUSE" | "DISPATCHER" | "VIEWER" | string | null;
export interface Me {
  authenticated: boolean;
  user?: { id:number; username:string; full_name:string; role:Role; avatar_url?:string|null };
  company?: { id:number; name:string; code?:string } | null;
  companies?: { id:number; name:string; code?:string; role:Role; is_default?:boolean }[];
  is_super?: boolean;
  organizations?: {id:number;name:string;code?:string;role:string;is_default?:boolean}[];
  active_organization_id?: number|null;
}
export interface CompanyMember { id:number; user_id:number; username:string; full_name:string; email:string; role:Role; role_label:string; status:string; is_default:boolean; permissions:Record<string,boolean>; }
export interface CompanyContext { active_company:any; companies:any[]; is_super:boolean; roles:Record<string,string>; permission_catalog:string[]; }
export interface Dashboard {
  vehicles:number; drivers:number; routes:number; trips:number;
  unread_notifications:number; fuel_total:number; warehouse_total?:number; other_total?:number;
}
