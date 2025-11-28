import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { client } from '../api/client';
import { useAuth } from '../context/AuthContext';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/Card';
import { motion } from 'framer-motion';
import { Store, ArrowLeft } from 'lucide-react';

export const VendorOnboard: React.FC = () => {
    const [formData, setFormData] = useState({
        official_name: '',
        gst_number: '',
        email: '',
        phone: '',
        city: '',
    });
    const [error, setError] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const { refreshVendorProfile, vendorProfile } = useAuth();
    const navigate = useNavigate();

    React.useEffect(() => {
        if (vendorProfile) {
            navigate('/role-selection');
        }
    }, [vendorProfile, navigate]);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setIsLoading(true);
        setError('');

        try {
            await client.post('/vendors/onboard', formData);
            await refreshVendorProfile();
            navigate('/role-selection');
        } catch (err: any) {
            setError(err.response?.data?.error || 'Onboarding failed. Please check your inputs.');
            if (err.response?.data?.gst_number) {
                setError(err.response.data.gst_number[0]);
            }
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="max-w-3xl mx-auto py-12 px-4">
            <Button
                variant="ghost"
                className="mb-8 pl-0 hover:bg-transparent hover:text-white"
                onClick={() => navigate('/role-selection')}
            >
                <ArrowLeft className="mr-2 h-4 w-4" />
                Back to Role Selection
            </Button>

            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
            >
                <Card className="border-border/50 shadow-2xl overflow-hidden">
                    <div className="h-2 bg-gradient-to-r from-primary to-accent" />
                    <CardHeader className="border-b border-border/50 pb-8">
                        <div className="flex items-center gap-4">
                            <div className="p-3 bg-primary/10 rounded-xl ring-1 ring-primary/20">
                                <Store className="h-8 w-8 text-primary" />
                            </div>
                            <div>
                                <CardTitle className="text-2xl">Vendor Registration</CardTitle>
                                <p className="text-secondary mt-1">Complete your business profile to start selling</p>
                            </div>
                        </div>
                    </CardHeader>

                    <CardContent className="pt-8">
                        <form onSubmit={handleSubmit} className="space-y-6">
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                <Input
                                    label="Legal Business Name"
                                    required
                                    value={formData.official_name}
                                    onChange={(e) => setFormData({ ...formData, official_name: e.target.value })}
                                    placeholder="e.g. Acme Uniforms Pvt Ltd"
                                />
                                <Input
                                    label="GSTIN"
                                    required
                                    maxLength={15}
                                    value={formData.gst_number}
                                    onChange={(e) => setFormData({ ...formData, gst_number: e.target.value })}
                                    placeholder="15-digit GST Number"
                                    className="uppercase"
                                />
                                <Input
                                    label="Business Email"
                                    type="email"
                                    required
                                    value={formData.email}
                                    onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                                    placeholder="contact@business.com"
                                />
                                <Input
                                    label="Business Phone"
                                    type="tel"
                                    required
                                    value={formData.phone}
                                    onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                                    placeholder="+91 98765 43210"
                                />
                                <div className="md:col-span-2">
                                    <Input
                                        label="City"
                                        required
                                        value={formData.city}
                                        onChange={(e) => setFormData({ ...formData, city: e.target.value })}
                                        placeholder="e.g. Mumbai"
                                    />
                                </div>
                            </div>

                            {error && (
                                <div className="p-4 rounded-lg bg-error/10 border border-error/20 text-sm text-error flex items-center gap-2">
                                    <span className="h-1.5 w-1.5 rounded-full bg-error" />
                                    {error}
                                </div>
                            )}

                            <div className="pt-6 border-t border-border/50">
                                <Button type="submit" className="w-full" size="lg" isLoading={isLoading}>
                                    Submit Application
                                </Button>
                                <p className="mt-4 text-xs text-center text-secondary">
                                    By submitting, you agree to our Vendor Terms of Service. Your application will be reviewed by our team within 24-48 hours.
                                </p>
                            </div>
                        </form>
                    </CardContent>
                </Card>
            </motion.div>
        </div>
    );
};
