import React, { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { client } from '../api/client';
import type { Cart as CartType } from '../api/types';
import { Button } from '../components/ui/Button';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/Card';
import { motion, AnimatePresence } from 'framer-motion';
import { Trash2, ShoppingBag, CreditCard } from 'lucide-react';

export const Cart: React.FC = () => {
    const [cart, setCart] = useState<CartType | null>(null);
    const [loading, setLoading] = useState(true);
    const navigate = useNavigate();

    const fetchCart = async () => {
        try {
            const { data } = await client.get<CartType>('/checkout/cart');
            setCart(data);
        } catch (error) {
            console.error('Failed to fetch cart', error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchCart();
    }, []);

    const removeItem = async (itemId: string) => {
        try {
            await client.delete(`/checkout/cart/items/${itemId}`);
            fetchCart();
        } catch (error) {
            console.error('Failed to remove item', error);
        }
    };

    const checkout = async () => {
        if (!cart) return;
        try {
            await client.post('/checkout/checkout/session', {
                cart_id: cart.id
            });
            // In a real app, redirect to Stripe/Payment Gateway
            // For this demo, we'll simulate success and go to orders
            alert('Payment Successful! (Simulated)');
            navigate('/orders');
        } catch (error) {
            console.error('Checkout failed', error);
            alert('Checkout failed');
        }
    };

    if (loading) return <div className="p-8 text-center text-secondary">Loading cart...</div>;

    if (!cart || cart.items.length === 0) {
        return (
            <div className="min-h-[60vh] flex flex-col items-center justify-center text-center space-y-6">
                <div className="h-24 w-24 bg-surface-hover rounded-full flex items-center justify-center">
                    <ShoppingBag className="h-10 w-10 text-muted" />
                </div>
                <div>
                    <h2 className="text-2xl font-bold text-white">Your cart is empty</h2>
                    <p className="text-secondary mt-2">Looks like you haven't added any items yet.</p>
                </div>
                <Link to="/schools">
                    <Button size="lg">Start Shopping</Button>
                </Link>
            </div>
        );
    }

    return (
        <div className="max-w-4xl mx-auto space-y-8">
            <h1 className="text-3xl font-bold text-white tracking-tight">Shopping Cart</h1>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                <div className="lg:col-span-2 space-y-4">
                    <AnimatePresence>
                        {cart.items.map((item) => (
                            <motion.div
                                key={item.id}
                                initial={{ opacity: 0, height: 0 }}
                                animate={{ opacity: 1, height: 'auto' }}
                                exit={{ opacity: 0, height: 0 }}
                                layout
                            >
                                <Card className="flex items-center p-4 gap-4">
                                    <div className="h-20 w-20 bg-surface-hover rounded-lg flex items-center justify-center shrink-0">
                                        <ShoppingBag className="h-8 w-8 text-muted" />
                                    </div>
                                    <div className="flex-1 min-w-0">
                                        <h3 className="font-bold text-white truncate">{item.listing_sku}</h3>
                                        <p className="text-sm text-secondary truncate">{item.vendor_name}</p>
                                        <div className="mt-1 flex items-center gap-4 text-sm">
                                            <span className="text-primary font-medium">${item.listing_price}</span>
                                            <span className="text-secondary">Qty: {item.qty}</span>
                                        </div>
                                    </div>
                                    <Button
                                        variant="ghost"
                                        size="sm"
                                        className="text-error hover:bg-error/10 hover:text-error shrink-0"
                                        onClick={() => removeItem(item.id)}
                                    >
                                        <Trash2 className="h-4 w-4" />
                                    </Button>
                                </Card>
                            </motion.div>
                        ))}
                    </AnimatePresence>
                </div>

                <div className="lg:col-span-1">
                    <Card className="sticky top-24">
                        <CardHeader>
                            <CardTitle>Order Summary</CardTitle>
                        </CardHeader>
                        <CardContent className="space-y-6">
                            <div className="space-y-2 text-sm">
                                <div className="flex justify-between text-secondary">
                                    <span>Subtotal</span>
                                    <span className="text-white">${cart.total_amount}</span>
                                </div>
                                <div className="flex justify-between text-secondary">
                                    <span>Shipping</span>
                                    <span className="text-white">Free</span>
                                </div>
                                <div className="pt-4 border-t border-border flex justify-between font-bold text-lg">
                                    <span className="text-white">Total</span>
                                    <span className="text-white">${cart.total_amount}</span>
                                </div>
                            </div>

                            <Button className="w-full" size="lg" onClick={checkout}>
                                Proceed to Checkout
                                <CreditCard className="ml-2 h-4 w-4" />
                            </Button>
                        </CardContent>
                    </Card>
                </div>
            </div>
        </div>
    );
};
