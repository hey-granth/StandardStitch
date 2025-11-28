import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { client } from '../api/client';
import type { School } from '../api/types';
import { Input } from '../components/ui/Input';
import { Card, CardContent } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import { motion } from 'framer-motion';
import { School as SchoolIcon, MapPin, Calendar, Search, ArrowRight } from 'lucide-react';

export const SchoolList: React.FC = () => {
    const [schools, setSchools] = useState<School[]>([]);
    const [search, setSearch] = useState('');
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchSchools = async () => {
            try {
                const { data } = await client.get<School[]>('/schools/schools/');
                setSchools(data);
            } catch (error) {
                console.error('Failed to fetch schools', error);
            } finally {
                setLoading(false);
            }
        };
        fetchSchools();
    }, []);

    const filteredSchools = schools.filter(school =>
        school.name.toLowerCase().includes(search.toLowerCase()) ||
        school.city.toLowerCase().includes(search.toLowerCase())
    );

    return (
        <div className="space-y-8">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                    <h1 className="text-3xl font-bold text-white tracking-tight">Find Your School</h1>
                    <p className="text-secondary mt-2">Browse schools to find uniforms and accessories</p>
                </div>
                <div className="relative w-full md:w-96">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted" />
                    <Input
                        placeholder="Search by name or city..."
                        value={search}
                        onChange={(e) => setSearch(e.target.value)}
                        className="pl-10 bg-surface border-border focus:bg-surface-hover"
                    />
                </div>
            </div>

            {loading ? (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {[1, 2, 3, 4, 5, 6].map((i) => (
                        <div key={i} className="h-64 bg-surface rounded-xl animate-pulse border border-border" />
                    ))}
                </div>
            ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {filteredSchools.map((school, index) => (
                        <motion.div
                            key={school.id}
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: index * 0.05 }}
                        >
                            <Link to={`/schools/${school.id}`}>
                                <Card hover className="h-full flex flex-col group">
                                    <div className="h-32 bg-surface-hover border-b border-border flex items-center justify-center group-hover:bg-surface-hover/80 transition-colors">
                                        <SchoolIcon className="h-12 w-12 text-muted group-hover:text-primary transition-colors" />
                                    </div>
                                    <CardContent className="flex-1 flex flex-col pt-6">
                                        <div className="flex items-start justify-between gap-2 mb-2">
                                            <h3 className="text-lg font-bold text-white line-clamp-2 group-hover:text-accent transition-colors">
                                                {school.name}
                                            </h3>
                                            {school.is_active && (
                                                <Badge variant="success" className="shrink-0">Active</Badge>
                                            )}
                                        </div>

                                        <div className="space-y-2 mb-6 flex-1">
                                            <div className="flex items-center text-sm text-secondary">
                                                <MapPin className="h-4 w-4 mr-2 shrink-0" />
                                                {school.city}
                                            </div>
                                            <div className="flex items-center text-sm text-secondary">
                                                <Calendar className="h-4 w-4 mr-2 shrink-0" />
                                                {school.board} Board
                                            </div>
                                        </div>

                                        <Button variant="secondary" className="w-full group-hover:bg-primary group-hover:text-black transition-all">
                                            View Catalog
                                            <ArrowRight className="ml-2 h-4 w-4" />
                                        </Button>
                                    </CardContent>
                                </Card>
                            </Link>
                        </motion.div>
                    ))}
                </div>
            )}

            {!loading && filteredSchools.length === 0 && (
                <div className="text-center py-20">
                    <div className="h-16 w-16 bg-surface-hover rounded-full flex items-center justify-center mx-auto mb-4">
                        <Search className="h-8 w-8 text-muted" />
                    </div>
                    <h3 className="text-lg font-medium text-white">No schools found</h3>
                    <p className="text-secondary">Try adjusting your search terms</p>
                </div>
            )}
        </div>
    );
};
