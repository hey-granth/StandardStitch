import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Button } from '../components/ui/Button';
import { Card } from '../components/ui/Card';
import { motion } from 'framer-motion';
import { User, Store, ShieldCheck, ArrowRight } from 'lucide-react';

export const RoleSelection: React.FC = () => {
    const { user, vendorProfile, isLoading } = useAuth();
    const navigate = useNavigate();

    useEffect(() => {
        if (!isLoading && user) {
            if (user.role === 'vendor') {
                navigate('/vendor/dashboard');
            } else if (user.role === 'school_admin' || user.role === 'ops') {
                navigate('/admin');
            }
        }
    }, [user, isLoading, navigate]);

    if (isLoading) return <div className="min-h-screen flex items-center justify-center text-white">Loading...</div>;

    if (vendorProfile && vendorProfile.status === 'pending') {
        return (
            <div className="min-h-screen flex items-center justify-center p-4 bg-background">
                <motion.div
                    initial={{ opacity: 0, scale: 0.95 }}
                    animate={{ opacity: 1, scale: 1 }}
                    className="max-w-md w-full"
                >
                    <Card className="p-8 text-center border-border/50">
                        <div className="mx-auto w-16 h-16 bg-warning/10 rounded-full flex items-center justify-center mb-6 ring-1 ring-warning/20">
                            <Store className="h-8 w-8 text-warning" />
                        </div>
                        <h2 className="text-2xl font-bold text-white mb-2">Application Pending</h2>
                        <p className="text-secondary mb-8">
                            Your vendor application is currently under review. We will notify you once it has been approved.
                        </p>
                        <Button variant="outline" onClick={() => navigate('/schools')} className="w-full">
                            Continue as Parent
                        </Button>
                    </Card>
                </motion.div>
            </div>
        );
    }

    if (vendorProfile && vendorProfile.status === 'rejected') {
        return (
            <div className="min-h-screen flex items-center justify-center p-4 bg-background">
                <motion.div
                    initial={{ opacity: 0, scale: 0.95 }}
                    animate={{ opacity: 1, scale: 1 }}
                    className="max-w-md w-full"
                >
                    <Card className="p-8 text-center border-border/50">
                        <div className="mx-auto w-16 h-16 bg-error/10 rounded-full flex items-center justify-center mb-6 ring-1 ring-error/20">
                            <ShieldCheck className="h-8 w-8 text-error" />
                        </div>
                        <h2 className="text-2xl font-bold text-white mb-2">Application Rejected</h2>
                        <p className="text-secondary mb-8">
                            Unfortunately, your vendor application was not approved.
                        </p>
                        <Button variant="outline" onClick={() => navigate('/schools')} className="w-full">
                            Continue as Parent
                        </Button>
                    </Card>
                </motion.div>
            </div>
        );
    }

    return (
        <div className="min-h-screen flex flex-col items-center justify-center p-4 space-y-12 bg-background">
            <div className="text-center space-y-4">
                <motion.h1
                    initial={{ opacity: 0, y: -20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="text-4xl font-bold text-white tracking-tight"
                >
                    Choose your path
                </motion.h1>
                <motion.p
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ delay: 0.1 }}
                    className="text-secondary text-lg"
                >
                    How would you like to use StandardStitch?
                </motion.p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 max-w-4xl w-full px-4">
                <motion.div
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.2 }}
                >
                    <button
                        onClick={() => navigate('/schools')}
                        className="w-full h-full group relative overflow-hidden rounded-2xl bg-surface border border-border p-8 text-left transition-all hover:border-primary/50 hover:shadow-2xl hover:shadow-primary/5"
                    >
                        <div className="absolute inset-0 bg-gradient-to-br from-primary/5 to-transparent opacity-0 transition-opacity group-hover:opacity-100" />
                        <div className="relative z-10">
                            <div className="w-14 h-14 bg-surface-hover rounded-xl flex items-center justify-center mb-6 group-hover:bg-primary group-hover:text-black transition-colors ring-1 ring-white/10">
                                <User className="h-7 w-7" />
                            </div>
                            <h3 className="text-2xl font-bold text-white mb-3">I am a Parent</h3>
                            <p className="text-secondary mb-6 leading-relaxed">
                                Browse schools, purchase uniforms, and manage orders for your children.
                            </p>
                            <div className="flex items-center text-primary font-medium group-hover:translate-x-1 transition-transform">
                                Get Started <ArrowRight className="ml-2 h-4 w-4" />
                            </div>
                        </div>
                    </button>
                </motion.div>

                <motion.div
                    initial={{ opacity: 0, x: 20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.3 }}
                >
                    <button
                        onClick={() => navigate('/vendor/onboard')}
                        className="w-full h-full group relative overflow-hidden rounded-2xl bg-surface border border-border p-8 text-left transition-all hover:border-accent/50 hover:shadow-2xl hover:shadow-accent/5"
                    >
                        <div className="absolute inset-0 bg-gradient-to-br from-accent/5 to-transparent opacity-0 transition-opacity group-hover:opacity-100" />
                        <div className="relative z-10">
                            <div className="w-14 h-14 bg-surface-hover rounded-xl flex items-center justify-center mb-6 group-hover:bg-accent group-hover:text-white transition-colors ring-1 ring-white/10">
                                <Store className="h-7 w-7" />
                            </div>
                            <h3 className="text-2xl font-bold text-white mb-3">I am a Vendor</h3>
                            <p className="text-secondary mb-6 leading-relaxed">
                                Register your business, list products, and sell directly to parents.
                            </p>
                            <div className="flex items-center text-accent font-medium group-hover:translate-x-1 transition-transform">
                                Join Now <ArrowRight className="ml-2 h-4 w-4" />
                            </div>
                        </div>
                    </button>
                </motion.div>
            </div>
        </div>
    );
};
