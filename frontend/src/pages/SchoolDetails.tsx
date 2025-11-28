import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { client } from '../api/client';
import type { School, UniformSpec } from '../api/types';
import { Button } from '../components/ui/Button';
import { Card } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { motion } from 'framer-motion';
import { ShoppingCart, ArrowLeft, Filter, Ruler } from 'lucide-react';

export const SchoolDetails: React.FC = () => {
    const { id } = useParams<{ id: string }>();
    const [school, setSchool] = useState<School | null>(null);
    const [specs, setSpecs] = useState<UniformSpec[]>([]);
    const [loading, setLoading] = useState(true);
    const [genderFilter, setGenderFilter] = useState<'M' | 'F' | 'Unisex' | 'All'>('All');

    useEffect(() => {
        const fetchData = async () => {
            try {
                const [schoolRes, specsRes] = await Promise.all([
                    client.get<School>(`/schools/schools/${id}`),
                    client.get<UniformSpec[]>(`/catalog/schools/${id}/catalog`)
                ]);
                setSchool(schoolRes.data);
                setSpecs(specsRes.data);
            } catch (error) {
                console.error('Failed to fetch data', error);
            } finally {
                setLoading(false);
            }
        };
        fetchData();
    }, [id]);

    const addToCart = async (listingId: string) => {
        try {
            await client.post('/checkout/cart/items', { listing: listingId, qty: 1 });
            alert('Added to cart'); // Replace with toast later
        } catch (error) {
            console.error('Failed to add to cart', error);
        }
    };

    const filteredSpecs = genderFilter === 'All'
        ? specs
        : specs.filter(s => s.gender === genderFilter || s.gender === 'Unisex');

    if (loading) return <div className="p-8 text-center text-secondary">Loading catalog...</div>;
    if (!school) return <div className="p-8 text-center text-error">School not found</div>;

    return (
        <div className="space-y-8">
            {/* Header */}
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-border pb-8">
                <div>
                    <Link to="/schools" className="inline-flex items-center text-sm text-secondary hover:text-white mb-4 transition-colors">
                        <ArrowLeft className="h-4 w-4 mr-1" /> Back to Schools
                    </Link>
                    <h1 className="text-3xl font-bold text-white tracking-tight">{school.name}</h1>
                    <p className="text-secondary mt-1">{school.city} • {school.board} Board</p>
                </div>

                <div className="flex items-center gap-2 bg-surface p-1 rounded-lg border border-border">
                    {(['All', 'M', 'F'] as const).map((g) => (
                        <button
                            key={g}
                            onClick={() => setGenderFilter(g)}
                            className={`px-4 py-2 rounded-md text-sm font-medium transition-all ${genderFilter === g
                                ? 'bg-primary text-black shadow-sm'
                                : 'text-secondary hover:text-white hover:bg-surface-hover'
                                }`}
                        >
                            {g === 'All' ? 'All Items' : g === 'M' ? 'Boys' : 'Girls'}
                        </button>
                    ))}
                </div>
            </div>

            {/* Catalog Grid */}
            <div className="grid grid-cols-1 gap-8">
                {filteredSpecs.map((spec) => (
                    <motion.div
                        key={spec.id}
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                    >
                        <div className="flex items-center gap-4 mb-4">
                            <h2 className="text-xl font-bold text-white">{spec.item_type}</h2>
                            <Badge variant="outline">{spec.gender}</Badge>
                            {spec.frozen && <Badge variant="warning">Frozen</Badge>}
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                            {spec.listings && spec.listings.length > 0 ? (
                                spec.listings.map((listing: any) => (
                                    <Card key={listing.id} className="group overflow-hidden">
                                        <div className="p-6 bg-surface-hover/50 border-b border-border">
                                            <div className="flex justify-between items-start mb-4">
                                                <div>
                                                    <h3 className="font-bold text-white text-lg">{listing.vendor_name}</h3>
                                                    <p className="text-xs text-secondary mt-1">SKU: {listing.sku}</p>
                                                </div>
                                                <div className="text-right">
                                                    <p className="text-xl font-bold text-white">${listing.price}</p>
                                                    {listing.mrp > listing.price && (
                                                        <p className="text-xs text-secondary line-through">${listing.mrp}</p>
                                                    )}
                                                </div>
                                            </div>

                                            <div className="space-y-2 text-sm text-secondary mb-6">
                                                <div className="flex items-center">
                                                    <Ruler className="h-4 w-4 mr-2" />
                                                    Specs: {spec.fabric_gsm} GSM, {spec.season}
                                                </div>
                                            </div>

                                            <Button
                                                className="w-full group-hover:bg-primary group-hover:text-black transition-all"
                                                onClick={() => addToCart(listing.id)}
                                            >
                                                <ShoppingCart className="h-4 w-4 mr-2" />
                                                Add to Cart
                                            </Button>
                                        </div>
                                    </Card>
                                ))
                            ) : (
                                <div className="col-span-full p-8 text-center border border-dashed border-border rounded-xl bg-surface/30">
                                    <p className="text-secondary">No vendors currently selling this item.</p>
                                </div>
                            )}
                        </div>
                    </motion.div>
                ))}

                {filteredSpecs.length === 0 && (
                    <div className="text-center py-20">
                        <Filter className="h-12 w-12 text-muted mx-auto mb-4" />
                        <h3 className="text-lg font-medium text-white">No items found</h3>
                        <p className="text-secondary">Try changing the gender filter</p>
                    </div>
                )}
            </div>
        </div>
    );
};
