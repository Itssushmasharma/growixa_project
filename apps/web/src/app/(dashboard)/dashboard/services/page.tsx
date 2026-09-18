"use client";

import { useEffect, useState } from "react";
import { apiFetch } from "@/lib/api-client";
import { PlusIcon, CheckCircle2 } from "lucide-react";

interface SMMService {
  id: string;
  name: string;
  platform: string;
  rate: number;
  min_quantity: number;
  max_quantity: number;
}

interface SMMOrder {
  id: string;
  service_name: string;
  platform: string;
  target_url: string;
  quantity: number;
  status: string;
}

export default function SMMServicesPage() {
  const [services, setServices] = useState<SMMService[]>([]);
  const [orders, setOrders] = useState<SMMOrder[]>([]);
  const [loading, setLoading] = useState(true);
  
  const [selectedServiceId, setSelectedServiceId] = useState<string>("");
  const [targetUrl, setTargetUrl] = useState("");
  const [quantity, setQuantity] = useState(100);
  const [submitting, setSubmitting] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchServicesAndOrders = async () => {
    try {
      const [servicesData, ordersData] = await Promise.all([
        apiFetch<SMMService[]>("/smm/services"),
        apiFetch<SMMOrder[]>("/smm/orders")
      ]);
      setServices(servicesData);
      setOrders(ordersData);
      if (servicesData[0]?.id) setSelectedServiceId(servicesData[0].id);
    } catch (e) {
      console.error("Failed to fetch SMM data", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchServicesAndOrders();
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    setSuccess(false);
    try {
      await apiFetch("/smm/orders", {
        method: "POST",
        body: JSON.stringify({
          service_id: selectedServiceId,
          target_url: targetUrl,
          quantity: Number(quantity)
        })
      });
      setSuccess(true);
      setTargetUrl("");
      fetchServicesAndOrders();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to place order.");
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return <div className="p-8 text-slate-500">Loading Services...</div>;
  }

  const selectedService = services.find(s => s.id === selectedServiceId);
  const totalCost = selectedService ? (selectedService.rate / 1000) * quantity : 0;

  return (
    <div className="max-w-6xl mx-auto p-6 md:p-8 space-y-8">
      <div className="flex justify-between items-end">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">SMM Services</h1>
          <p className="text-slate-500 mt-1">Boost your social presence with targeted growth campaigns.</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Order Form */}
        <div className="lg:col-span-1">
          <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
            <h2 className="text-lg font-semibold text-slate-900 mb-4">New Campaign</h2>
            
            {success && (
              <div className="mb-6 p-4 bg-emerald-50 border border-emerald-100 rounded-lg flex gap-3 text-emerald-800">
                <CheckCircle2 className="w-5 h-5 text-emerald-500 shrink-0" />
                <p className="text-sm font-medium">Order placed successfully!</p>
              </div>
            )}

            {error && (
              <div className="mb-6 p-4 bg-red-50 text-red-600 rounded-lg text-sm font-medium">
                {error}
              </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Service</label>
                <select 
                  className="w-full rounded-lg border-slate-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                  value={selectedServiceId}
                  onChange={e => setSelectedServiceId(e.target.value)}
                >
                  {services.map(s => (
                    <option key={s.id} value={s.id}>
                      {s.platform} - {s.name} (${s.rate}/1k)
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Target Link</label>
                <input 
                  type="url"
                  required
                  placeholder="https://t.me/yourchannel"
                  className="w-full rounded-lg border-slate-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                  value={targetUrl}
                  onChange={e => setTargetUrl(e.target.value)}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Quantity</label>
                <input 
                  type="number"
                  required
                  min={selectedService?.min_quantity || 1}
                  max={selectedService?.max_quantity || 100000}
                  step={10}
                  className="w-full rounded-lg border-slate-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                  value={quantity}
                  onChange={e => setQuantity(Number(e.target.value))}
                />
                {selectedService && (
                  <p className="text-xs text-slate-500 mt-1">Min: {selectedService.min_quantity} | Max: {selectedService.max_quantity}</p>
                )}
              </div>

              <div className="pt-4 border-t border-slate-100 flex items-center justify-between">
                <div>
                  <span className="block text-xs text-slate-500 uppercase tracking-wider font-semibold">Total Cost</span>
                  <span className="text-xl font-bold text-slate-900">${totalCost.toFixed(2)}</span>
                </div>
                <button 
                  type="submit"
                  disabled={submitting}
                  className="bg-indigo-600 hover:bg-indigo-700 text-white px-5 py-2.5 rounded-lg font-medium shadow-sm flex items-center gap-2 disabled:opacity-50 transition-colors"
                >
                  <PlusIcon className="w-4 h-4" />
                  Place Order
                </button>
              </div>
            </form>
          </div>
        </div>

        {/* Order History */}
        <div className="lg:col-span-2">
          <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
            <div className="px-6 py-4 border-b border-slate-200">
              <h2 className="text-lg font-semibold text-slate-900">Order History</h2>
            </div>
            {orders.length === 0 ? (
              <div className="p-8 text-center text-slate-500">No orders placed yet.</div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse">
                  <thead>
                    <tr className="bg-slate-50 text-slate-500 text-xs uppercase tracking-wider">
                      <th className="px-6 py-3 font-semibold">Service</th>
                      <th className="px-6 py-3 font-semibold">Link</th>
                      <th className="px-6 py-3 font-semibold text-right">Quantity</th>
                      <th className="px-6 py-3 font-semibold">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 text-sm">
                    {orders.map(order => (
                      <tr key={order.id} className="hover:bg-slate-50">
                        <td className="px-6 py-4">
                          <p className="font-medium text-slate-900">{order.service_name}</p>
                          <p className="text-slate-500 text-xs mt-0.5">{order.platform}</p>
                        </td>
                        <td className="px-6 py-4">
                          <a href={order.target_url} target="_blank" rel="noreferrer" className="text-indigo-600 hover:underline truncate max-w-[200px] inline-block">
                            {order.target_url}
                          </a>
                        </td>
                        <td className="px-6 py-4 text-right font-medium text-slate-900">
                          {order.quantity.toLocaleString()}
                        </td>
                        <td className="px-6 py-4">
                          <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold ${
                            order.status === 'COMPLETED' ? 'bg-emerald-100 text-emerald-800' :
                            order.status === 'PROCESSING' ? 'bg-blue-100 text-blue-800' :
                            order.status === 'FAILED' ? 'bg-red-100 text-red-800' :
                            'bg-slate-100 text-slate-800'
                          }`}>
                            {order.status}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
