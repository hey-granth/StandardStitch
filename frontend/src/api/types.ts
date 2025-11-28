export interface User {
    id: string;
    email: string;
    phone: string;
    role: 'parent' | 'vendor' | 'school_admin' | 'ops';
    is_active: boolean;
}

export interface AuthResponse {
    access: string;
    refresh: string;
    user: User;
}

export interface Vendor {
    id: string;
    official_name: string;
    gst_number: string;
    email: string;
    phone: string;
    city: string;
    status: 'pending' | 'approved' | 'rejected';
    is_active: boolean;
}

export interface School {
    id: string;
    name: string;
    city: string;
    board: string;
    session_start: string;
    session_end: string;
    is_active: boolean;
}

export interface Listing {
    id: string;
    vendor_name: string;
    price: string; // Serializer returns string/decimal
    mrp: string;
    sku: string;
    lead_time_days: number;
    school_name?: string;
    spec_item_type?: string;
    enabled?: boolean;
    base_price?: string; // For vendor dashboard
}

export interface UniformSpec {
    id: string;
    item_type: string;
    gender: string;
    season: string;
    fabric_gsm: number;
    pantone: string;
    measurements: Record<string, any>;
    frozen: boolean;
    version: number;
    listings?: Listing[]; // We will re-add this to backend
}

export interface CartItem {
    id: string;
    listing: string; // UUID
    listing_sku: string;
    listing_price: string;
    vendor_name: string;
    qty: number;
    created_at: string;
    updated_at: string;
}

export interface Cart {
    id: string;
    user: string;
    items: CartItem[];
    total_amount: number; // We will ensure backend returns this
    created_at: string;
    updated_at: string;
}

export interface OrderItem {
    id: string;
    listing: string;
    qty: number;
    unit_price: string;
    subtotal: string;
}

export interface Order {
    id: string;
    user: string;
    total_amount: string;
    status: 'pending' | 'confirmed' | 'cancelled';
    created_at: string;
    updated_at: string;
}
