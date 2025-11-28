import React, { useEffect, useState } from 'react';
import { client } from '../api/client';
import type { Vendor } from '../api/types';
import { Button } from '../components/ui/Button';
import { Card, CardHeader, CardTitle } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { Check, X, ShieldCheck, Mail, Phone, MapPin, FileText } from 'lucide-react';
import { motion } from 'framer-motion';

export const AdminDashboard: React.FC = () => {
    const [vendors, setVendors] = useState<Vendor[]>([]);
    const [loading, setLoading] = useState(true);

    const fetchVendors = async () => {
        try {
            const { data } = await client.get<Vendor[]>('/vendors/vendors/');
            setVendors(data);
        } catch (error) {
            console.error('Failed to fetch vendors', error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchVendors();
    }, []);

    const handleApprove = async (id: string) => {
        try {
            await client.post(`/vendors/vendors/${id}/approve`);
            fetchVendors();
        } catch (error) {
            console.error('Failed to approve', error);
        }
    };

    const handleReject = async (id: string) => {
        try {
            await client.post(`/vendors/vendors/${id}/reject`);
            fetchVendors();
        } catch (error) {
            console.error('Failed to reject', error);
        }
    };

    if (loading) return <div className="p-8 text-center text-secondary">Loading admin panel...</div>;

    return (
        <div className="space-y-8">
            <div className="flex items-center gap-4">
                <div className="p-3 bg-primary/10 rounded-xl">
                    <ShieldCheck className="h-8 w-8 text-primary" />
                </div>
                <div>
                    <h1 className="text-3xl font-bold text-white tracking-tight">Admin Dashboard</h1>
                    <p className="text-secondary">Manage vendor applications and platform settings</p>
                </div>
            </div>

            <Card>
                <CardHeader className="border-b border-border">
                    <CardTitle>Vendor Applications</CardTitle>
                </CardHeader>
                <div className="divide-y divide-border">
                    {vendors.map((vendor) => (
                        <motion.div
                            key={vendor.id}
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            className="p-6 flex flex-col md:flex-row md:items-center justify-between gap-6 hover:bg-surface-hover/50 transition-colors"
                        >
                            <div className="space-y-2">
                                <div className="flex items-center gap-3">
                                    <h3 className="font-bold text-white text-lg">{vendor.official_name}</h3>
                                    <Badge variant={
                                        vendor.status === 'approved' ? 'success' :
                                            vendor.status === 'rejected' ? 'error' : 'warning'
                                    }>
                                        {vendor.status}
                                    </Badge>
                                </div>

                                <div className="grid grid-cols-1 md:grid-cols-2 gap-x-8 gap-y-1 text-sm text-secondary">
                                    <div className="flex items-center gap-2">
                                        <Mail className="h-3 w-3" /> {vendor.email}
                                    </div>
                                    <div className="flex items-center gap-2">
                                        <Phone className="h-3 w-3" /> {vendor.phone}
                                    </div>
                                    <div className="flex items-center gap-2">
                                        <FileText className="h-3 w-3" /> GST: {vendor.gst_number}
                                    </div>
                                    <div className="flex items-center gap-2">
                                        <MapPin className="h-3 w-3" /> {vendor.city}
                                    </div>
                                </div>
                            </div>

                            {vendor.status === 'pending' && (
                                <div className="flex items-center gap-3 shrink-0">
                                    <Button
                                        size="sm"
                                        onClick={() => handleApprove(vendor.id)}
                                        className="bg-success hover:bg-success/90 text-white border-none"
                                    >
                                        <Check className="h-4 w-4 mr-2" />
                                        Approve
                                    </Button>
                                    <Button
                                        size="sm"
                                        onClick={() => handleReject(vendor.id)}
                                        variant="danger"
                                    >
                                        <X className="h-4 w-4 mr-2" />
                                        Reject
                                    </Button>
                                </div>
                            )}
                        </motion.div>
                    ))}

                    {vendors.length === 0 && (
                        <div className="p-8 text-center text-secondary">
                            No vendor applications found.
                        </div>
                    )}
                </div>
            </Card>
        </div>
    );
};
