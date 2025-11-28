import React, { createContext, useContext, useState, useEffect } from 'react';
import type { User, AuthResponse, Vendor } from '../api/types';
import { client } from '../api/client';

interface AuthContextType {
    user: User | null;
    vendorProfile: Vendor | null;
    isAuthenticated: boolean;
    isLoading: boolean;
    login: (tokens: AuthResponse) => void;
    logout: () => void;
    checkAuth: () => Promise<void>;
    refreshVendorProfile: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
    const [user, setUser] = useState<User | null>(null);
    const [vendorProfile, setVendorProfile] = useState<Vendor | null>(null);
    const [isLoading, setIsLoading] = useState(true);

    const refreshVendorProfile = async () => {
        try {
            const { data } = await client.get<Vendor>('/vendors/vendors/me');
            setVendorProfile(data);
        } catch (error) {
            setVendorProfile(null);
        }
    };

    const login = (data: AuthResponse) => {
        localStorage.setItem('access_token', data.access);
        localStorage.setItem('refresh_token', data.refresh);
        setUser(data.user);
        // Fetch vendor profile after login
        client.get<Vendor>('/vendors/vendors/me')
            .then(res => setVendorProfile(res.data))
            .catch(() => setVendorProfile(null));
    };

    const logout = () => {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        setUser(null);
        setVendorProfile(null);
    };

    const checkAuth = async () => {
        const token = localStorage.getItem('access_token');
        if (!token) {
            setIsLoading(false);
            return;
        }
        try {
            const { data } = await client.get<User>('/auth/me');
            setUser(data);
            // Fetch vendor profile
            try {
                const { data: vendorData } = await client.get<Vendor>('/vendors/vendors/me');
                setVendorProfile(vendorData);
            } catch (e) {
                setVendorProfile(null);
            }
        } catch (error) {
            logout();
        } finally {
            setIsLoading(false);
        }
    };

    useEffect(() => {
        checkAuth();
    }, []);

    return (
        <AuthContext.Provider value={{
            user,
            vendorProfile,
            isAuthenticated: !!user,
            isLoading,
            login,
            logout,
            checkAuth,
            refreshVendorProfile
        }}>
            {children}
        </AuthContext.Provider>
    );
};

export const useAuth = () => {
    const context = useContext(AuthContext);
    if (context === undefined) {
        throw new Error('useAuth must be used within an AuthProvider');
    }
    return context;
};
