import React, { useEffect, useState } from 'react';
import { client } from '../api/client';
import type { Order } from '../api/types';
import { Card, CardHeader } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { motion } from 'framer-motion';
import { Package, Clock, CheckCircle, XCircle } from 'lucide-react';

export const Orders: React.FC = () => {
    const [orders, setOrders] = useState<Order[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchOrders = async () => {
            try {
                const { data } = await client.get<Order[]>('/checkout/orders');
                setOrders(data);
            } catch (error) {
                console.error('Failed to fetch orders', error);
            } finally {
                setLoading(false);
            }
        };
        fetchOrders();
    }, []);

    if (loading) return <div className="p-8 text-center text-secondary">Loading orders...</div>;

    if (orders.length === 0) {
        return (
            <div className="min-h-[60vh] flex flex-col items-center justify-center text-center space-y-6">
                <div className="h-24 w-24 bg-surface-hover rounded-full flex items-center justify-center">
                    <Package className="h-10 w-10 text-muted" />
                </div>
                <div>
                    <h2 className="text-2xl font-bold text-white">No orders yet</h2>
                    <p className="text-secondary mt-2">When you place an order, it will appear here.</p>
                </div>
            </div>
        );
    }

    const getStatusColor = (status: string) => {
        switch (status) {
            case 'completed': return 'success';
            case 'pending': return 'warning';
            case 'cancelled': return 'error';
            default: return 'default';
        }
    };

    const getStatusIcon = (status: string) => {
        switch (status) {
            case 'completed': return <CheckCircle className="h-4 w-4" />;
            case 'pending': return <Clock className="h-4 w-4" />;
            case 'cancelled': return <XCircle className="h-4 w-4" />;
            default: return <Package className="h-4 w-4" />;
        }
    };

    return (
        <div className="space-y-8">
            <h1 className="text-3xl font-bold text-white tracking-tight">Order History</h1>

            <div className="space-y-4">
                {orders.map((order, index) => (
                    <motion.div
                        key={order.id}
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: index * 0.1 }}
                    >
                        <Card>
                            <CardHeader className="flex flex-row items-center justify-between py-4">
                                <div className="flex items-center gap-4">
                                    <div className="p-2 bg-surface-hover rounded-lg">
                                        <Package className="h-5 w-5 text-secondary" />
                                    </div>
                                    <div>
                                        <p className="font-bold text-white">Order #{order.id.slice(0, 8)}</p>
                                        <p className="text-xs text-secondary">
                                            {new Date(order.created_at).toLocaleDateString()}
                                        </p>
                                    </div>
                                </div>
                                <div className="flex items-center gap-4">
                                    <p className="font-bold text-white">${order.total_amount}</p>
                                    <Badge variant={getStatusColor(order.status) as any} className="flex items-center gap-1">
                                        {getStatusIcon(order.status)}
                                        <span className="capitalize">{order.status}</span>
                                    </Badge>
                                </div>
                            </CardHeader>
                        </Card>
                    </motion.div>
                ))}
            </div>
        </div>
    );
};
