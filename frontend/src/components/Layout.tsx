import React, { useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { motion, AnimatePresence } from 'framer-motion';
import {
    Menu, X, ShoppingCart, User, LogOut,
    School, ShieldCheck,
    ChevronDown, Store
} from 'lucide-react';
import { Button } from './ui/Button';
import { cn } from './ui/Card';

export const Layout: React.FC<{ children: React.ReactNode }> = ({ children }) => {
    const { user, logout, vendorProfile } = useAuth();
    const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
    const [isProfileOpen, setIsProfileOpen] = useState(false);
    const location = useLocation();
    const navigate = useNavigate();

    const isActive = (path: string) => location.pathname.startsWith(path);

    const navItems = [
        { label: 'Schools', path: '/schools', icon: School, show: true },
        { label: 'Vendor Dashboard', path: '/vendor/dashboard', icon: Store, show: user?.role === 'vendor' && vendorProfile?.status === 'approved' },
        { label: 'Admin', path: '/admin', icon: ShieldCheck, show: user?.role === 'school_admin' || user?.role === 'ops' },
    ];

    return (
        <div className="min-h-screen bg-background flex flex-col">
            {/* Navbar */}
            <nav className="sticky top-0 z-50 w-full border-b border-border bg-background/80 backdrop-blur-xl">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="flex h-16 items-center justify-between">
                        {/* Logo */}
                        <div className="flex items-center gap-8">
                            <Link to="/" className="flex items-center gap-2">
                                <div className="h-8 w-8 rounded-lg bg-white flex items-center justify-center">
                                    <span className="text-black font-bold text-lg">S</span>
                                </div>
                                <span className="text-lg font-bold text-white tracking-tight">StandardStitch</span>
                            </Link>

                            {/* Desktop Nav */}
                            <div className="hidden md:flex items-center gap-1">
                                {navItems.filter(item => item.show).map((item) => (
                                    <Link key={item.path} to={item.path}>
                                        <Button
                                            variant="ghost"
                                            size="sm"
                                            className={cn(
                                                "gap-2",
                                                isActive(item.path) && "bg-surface-hover text-white"
                                            )}
                                        >
                                            <item.icon className="h-4 w-4" />
                                            {item.label}
                                        </Button>
                                    </Link>
                                ))}
                            </div>
                        </div>

                        {/* Right Actions */}
                        <div className="hidden md:flex items-center gap-4">
                            {user ? (
                                <>
                                    <Link to="/cart">
                                        <Button variant="ghost" size="sm" className="relative">
                                            <ShoppingCart className="h-5 w-5" />
                                            {/* Add cart count badge here if needed */}
                                        </Button>
                                    </Link>

                                    <div className="relative">
                                        <Button
                                            variant="ghost"
                                            size="sm"
                                            className="gap-2"
                                            onClick={() => setIsProfileOpen(!isProfileOpen)}
                                        >
                                            <div className="h-6 w-6 rounded-full bg-surface-hover flex items-center justify-center border border-border">
                                                <User className="h-4 w-4 text-secondary" />
                                            </div>
                                            <span className="text-sm font-medium">{user.email.split('@')[0]}</span>
                                            <ChevronDown className={cn("h-4 w-4 transition-transform", isProfileOpen && "rotate-180")} />
                                        </Button>

                                        <AnimatePresence>
                                            {isProfileOpen && (
                                                <motion.div
                                                    initial={{ opacity: 0, y: 10, scale: 0.95 }}
                                                    animate={{ opacity: 1, y: 0, scale: 1 }}
                                                    exit={{ opacity: 0, y: 10, scale: 0.95 }}
                                                    className="absolute right-0 mt-2 w-56 rounded-xl border border-border bg-surface shadow-xl py-1 z-50"
                                                >
                                                    <div className="px-3 py-2 border-b border-border">
                                                        <p className="text-sm font-medium text-white">{user.email}</p>
                                                        <p className="text-xs text-secondary capitalize">{user.role}</p>
                                                    </div>
                                                    <div className="p-1">
                                                        <Link to="/orders" onClick={() => setIsProfileOpen(false)}>
                                                            <Button variant="ghost" size="sm" className="w-full justify-start">
                                                                My Orders
                                                            </Button>
                                                        </Link>
                                                        {user.role === 'parent' && (
                                                            <Link to="/vendor/onboard" onClick={() => setIsProfileOpen(false)}>
                                                                <Button variant="ghost" size="sm" className="w-full justify-start">
                                                                    Become a Vendor
                                                                </Button>
                                                            </Link>
                                                        )}
                                                        <Button
                                                            variant="ghost"
                                                            size="sm"
                                                            className="w-full justify-start text-error hover:text-error hover:bg-error/10"
                                                            onClick={() => {
                                                                logout();
                                                                setIsProfileOpen(false);
                                                                navigate('/login');
                                                            }}
                                                        >
                                                            <LogOut className="h-4 w-4 mr-2" />
                                                            Sign Out
                                                        </Button>
                                                    </div>
                                                </motion.div>
                                            )}
                                        </AnimatePresence>
                                    </div>
                                </>
                            ) : (
                                <div className="flex items-center gap-2">
                                    <Link to="/login">
                                        <Button variant="ghost" size="sm">Sign In</Button>
                                    </Link>
                                    <Link to="/signup">
                                        <Button size="sm">Get Started</Button>
                                    </Link>
                                </div>
                            )}
                        </div>

                        {/* Mobile Menu Button */}
                        <div className="md:hidden">
                            <Button variant="ghost" size="sm" onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}>
                                {isMobileMenuOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
                            </Button>
                        </div>
                    </div>
                </div>

                {/* Mobile Menu */}
                <AnimatePresence>
                    {isMobileMenuOpen && (
                        <motion.div
                            initial={{ height: 0, opacity: 0 }}
                            animate={{ height: 'auto', opacity: 1 }}
                            exit={{ height: 0, opacity: 0 }}
                            className="md:hidden border-b border-border bg-background"
                        >
                            <div className="px-4 py-4 space-y-2">
                                {navItems.filter(item => item.show).map((item) => (
                                    <Link key={item.path} to={item.path} onClick={() => setIsMobileMenuOpen(false)}>
                                        <Button variant="ghost" className="w-full justify-start gap-2">
                                            <item.icon className="h-4 w-4" />
                                            {item.label}
                                        </Button>
                                    </Link>
                                ))}
                                {user && (
                                    <>
                                        <div className="h-px bg-border my-2" />
                                        <Link to="/cart" onClick={() => setIsMobileMenuOpen(false)}>
                                            <Button variant="ghost" className="w-full justify-start gap-2">
                                                <ShoppingCart className="h-4 w-4" />
                                                Cart
                                            </Button>
                                        </Link>
                                        <Link to="/orders" onClick={() => setIsMobileMenuOpen(false)}>
                                            <Button variant="ghost" className="w-full justify-start gap-2">
                                                My Orders
                                            </Button>
                                        </Link>
                                        <Button
                                            variant="ghost"
                                            className="w-full justify-start gap-2 text-error"
                                            onClick={() => {
                                                logout();
                                                setIsMobileMenuOpen(false);
                                            }}
                                        >
                                            <LogOut className="h-4 w-4" />
                                            Sign Out
                                        </Button>
                                    </>
                                )}
                            </div>
                        </motion.div>
                    )}
                </AnimatePresence>
            </nav>

            {/* Main Content */}
            <main className="flex-1 w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.4 }}
                >
                    {children}
                </motion.div>
            </main>

            {/* Footer */}
            <footer className="border-t border-border bg-surface/30 py-8 mt-auto">
                <div className="max-w-7xl mx-auto px-4 text-center text-sm text-secondary">
                    <p>&copy; {new Date().getFullYear()} StandardStitch. All rights reserved.</p>
                </div>
            </footer>
        </div>
    );
};
