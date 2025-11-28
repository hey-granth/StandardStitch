import React, { useEffect, useState } from 'react';
import { client } from '../api/client';
import type { Vendor, Listing } from '../api/types';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { motion, AnimatePresence } from 'framer-motion';
import { Plus, Package, AlertCircle, DollarSign, Tag, Clock } from 'lucide-react';

export const VendorDashboard: React.FC = () => {
    const [vendor, setVendor] = useState<Vendor | null>(null);
    const [listings, setListings] = useState<Listing[]>([]);
    const [loading, setLoading] = useState(true);
    const [showCreate, setShowCreate] = useState(false);

    // Create form state
    const [newItem, setNewItem] = useState({
        sku: '',
        base_price: '',
        mrp: '',
        lead_time_days: 7,
        school_id: '',
        spec_id: '',
    });

    useEffect(() => {
        const fetchData = async () => {
            try {
                const { data: vendorData } = await client.get<Vendor>('/vendors/vendors/me');
                setVendor(vendorData);

                if (vendorData.status === 'approved') {
                    const { data: listingsData } = await client.get<Listing[]>(`/vendors/vendors/${vendorData.id}/listings`);
                    setListings(listingsData);
                }
            } catch (error) {
                console.error('Failed to fetch vendor data', error);
            } finally {
                setLoading(false);
            }
        };
        fetchData();
    }, []);

    const handleCreate = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!vendor) return;

        try {
            await client.post('/vendors/listings', {
                sku: newItem.sku,
                base_price: newItem.base_price,
                mrp: newItem.mrp,
                lead_time_days: newItem.lead_time_days,
                school: newItem.school_id,
                spec: newItem.spec_id,
                vendor: vendor.id,
                enabled: true
            }, {
                headers: {
                    'Idempotency-Key': crypto.randomUUID()
                }
            });
            // Refresh listings
            const { data } = await client.get<Listing[]>(`/vendors/vendors/${vendor.id}/listings`);
            setListings(data);
            setShowCreate(false);
            setNewItem({
                sku: '',
                base_price: '',
                mrp: '',
                lead_time_days: 7,
                school_id: '',
                spec_id: '',
            });
        } catch (error) {
            console.error('Failed to create listing', error);
            alert('Failed to create listing. Ensure you are approved and inputs are valid.');
        }
    };

    if (loading) return <div className="p-8 text-center text-secondary">Loading dashboard...</div>;
    if (!vendor) return <div className="p-8 text-center text-error">No vendor profile found.</div>;

    return (
        <div className="space-y-8">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                    <h1 className="text-3xl font-bold text-white tracking-tight">Vendor Dashboard</h1>
                    <div className="flex items-center gap-2 mt-2">
                        <span className="text-secondary">Status:</span>
                        <Badge variant={vendor.status === 'approved' ? 'success' : 'warning'}>
                            {vendor.status}
                        </Badge>
                    </div>
                </div>
                {vendor.status === 'approved' && (
                    <Button onClick={() => setShowCreate(!showCreate)} className="shrink-0">
                        <Plus className="h-4 w-4 mr-2" />
                        New Listing
                    </Button>
                )}
            </div>

            {vendor.status !== 'approved' && (
                <Card className="bg-warning/5 border-warning/20">
                    <CardContent className="flex items-center gap-4 py-4">
                        <AlertCircle className="h-5 w-5 text-warning shrink-0" />
                        <p className="text-warning">Your account is pending approval. You cannot create listings yet.</p>
                    </CardContent>
                </Card>
            )}

            <AnimatePresence>
                {showCreate && (
                    <motion.div
                        initial={{ opacity: 0, height: 0 }}
                        animate={{ opacity: 1, height: 'auto' }}
                        exit={{ opacity: 0, height: 0 }}
                        className="overflow-hidden"
                    >
                        <Card className="border-primary/20 bg-surface-hover/30">
                            <CardHeader>
                                <CardTitle>Create New Listing</CardTitle>
                            </CardHeader>
                            <CardContent>
                                <form onSubmit={handleCreate} className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                    <Input
                                        label="School ID"
                                        value={newItem.school_id}
                                        onChange={(e) => setNewItem({ ...newItem, school_id: e.target.value })}
                                        required
                                        placeholder="UUID"
                                    />
                                    <Input
                                        label="Spec ID"
                                        value={newItem.spec_id}
                                        onChange={(e) => setNewItem({ ...newItem, spec_id: e.target.value })}
                                        required
                                        placeholder="UUID"
                                    />
                                    <Input
                                        label="SKU"
                                        value={newItem.sku}
                                        onChange={(e) => setNewItem({ ...newItem, sku: e.target.value })}
                                        required
                                        placeholder="PROD-001"
                                    />
                                    <Input
                                        label="Base Price"
                                        type="number"
                                        value={newItem.base_price}
                                        onChange={(e) => setNewItem({ ...newItem, base_price: e.target.value })}
                                        required
                                        placeholder="0.00"
                                    />
                                    <Input
                                        label="MRP"
                                        type="number"
                                        value={newItem.mrp}
                                        onChange={(e) => setNewItem({ ...newItem, mrp: e.target.value })}
                                        required
                                        placeholder="0.00"
                                    />
                                    <Input
                                        label="Lead Time (Days)"
                                        type="number"
                                        value={newItem.lead_time_days}
                                        onChange={(e) => setNewItem({ ...newItem, lead_time_days: parseInt(e.target.value) })}
                                        required
                                        placeholder="7"
                                    />
                                    <div className="md:col-span-2 flex justify-end gap-4 pt-4">
                                        <Button type="button" variant="ghost" onClick={() => setShowCreate(false)}>Cancel</Button>
                                        <Button type="submit">Create Listing</Button>
                                    </div>
                                </form>
                            </CardContent>
                        </Card>
                    </motion.div>
                )}
            </AnimatePresence>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {listings.map((listing) => (
                    <motion.div
                        key={listing.id}
                        initial={{ opacity: 0, scale: 0.95 }}
                        animate={{ opacity: 1, scale: 1 }}
                    >
                        <Card hover>
                            <CardContent className="pt-6">
                                <div className="flex items-start justify-between mb-4">
                                    <div className="p-2 bg-surface-hover rounded-lg">
                                        <Package className="h-5 w-5 text-secondary" />
                                    </div>
                                    <Badge variant={listing.enabled ? 'success' : 'error'}>
                                        {listing.enabled ? 'Active' : 'Disabled'}
                                    </Badge>
                                </div>

                                <h3 className="font-bold text-white mb-1 truncate">{listing.sku}</h3>
                                <p className="text-sm text-secondary mb-4 line-clamp-2">
                                    {listing.school_name} - {listing.spec_item_type}
                                </p>

                                <div className="grid grid-cols-2 gap-4 text-sm border-t border-border pt-4">
                                    <div className="flex items-center text-secondary">
                                        <DollarSign className="h-3 w-3 mr-1" />
                                        ${listing.base_price}
                                    </div>
                                    <div className="flex items-center text-secondary">
                                        <Tag className="h-3 w-3 mr-1" />
                                        MRP: ${listing.mrp}
                                    </div>
                                    <div className="flex items-center text-secondary col-span-2">
                                        <Clock className="h-3 w-3 mr-1" />
                                        Lead Time: {listing.lead_time_days} days
                                    </div>
                                </div>
                            </CardContent>
                        </Card>
                    </motion.div>
                ))}
            </div>
        </div>
    );
};
