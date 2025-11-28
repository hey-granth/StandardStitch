import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { client } from '../api/client';
import type { AuthResponse } from '../api/types';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { Card, CardContent } from '../components/ui/Card';
import { motion } from 'framer-motion';

export const Signup: React.FC = () => {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [phone, setPhone] = useState('');
    const [error, setError] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const { login } = useAuth();
    const navigate = useNavigate();

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setIsLoading(true);
        setError('');

        try {
            const { data } = await client.post<AuthResponse>('/auth/signup', {
                email,
                password,
                phone: phone || undefined
            });
            login(data);
            navigate('/role-selection');
        } catch (err: any) {
            const msg = err.response?.data?.email?.[0] || err.response?.data?.password?.[0] || 'Signup failed';
            setError(msg);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="min-h-screen flex items-center justify-center p-4 bg-background">
            <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                className="w-full max-w-md"
            >
                <div className="text-center mb-8">
                    <div className="h-12 w-12 bg-white rounded-xl mx-auto flex items-center justify-center mb-4 shadow-lg shadow-white/10">
                        <span className="text-black font-bold text-2xl">S</span>
                    </div>
                    <h1 className="text-3xl font-bold text-white tracking-tight">Create an account</h1>
                    <p className="text-secondary mt-2">Join StandardStitch to get started</p>
                </div>

                <Card className="border-border/50 shadow-2xl">
                    <CardContent className="pt-6">
                        <form onSubmit={handleSubmit} className="space-y-4">
                            <Input
                                label="Email address"
                                type="email"
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                                required
                                placeholder="name@example.com"
                            />
                            <Input
                                label="Phone number (optional)"
                                type="tel"
                                value={phone}
                                onChange={(e) => setPhone(e.target.value)}
                                placeholder="+1 (555) 000-0000"
                            />
                            <Input
                                label="Password"
                                type="password"
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                required
                                placeholder="Create a strong password"
                                minLength={8}
                            />

                            {error && (
                                <div className="p-3 rounded-md bg-error/10 border border-error/20 text-sm text-error">
                                    {error}
                                </div>
                            )}

                            <Button type="submit" className="w-full" size="lg" isLoading={isLoading}>
                                Create account
                            </Button>
                        </form>

                        <div className="mt-6 text-center text-sm text-secondary">
                            Already have an account?{' '}
                            <Link to="/login" className="font-medium text-primary hover:underline">
                                Sign in
                            </Link>
                        </div>
                    </CardContent>
                </Card>
            </motion.div>
        </div>
    );
};
