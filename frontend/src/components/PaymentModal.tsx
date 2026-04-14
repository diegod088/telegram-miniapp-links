import React, { useState } from 'react';
import { X, Check, Star, Shield, Zap, ExternalLink } from 'lucide-react';
import WebApp from '@twa-dev/sdk';
import { createInvoice } from '../api';

interface PaymentModalProps {
  isOpen: boolean;
  onClose: () => void;
  currentPlan: string;
}

const PaymentModal: React.FC<PaymentModalProps> = ({ isOpen, onClose, currentPlan }) => {
  const [loading, setLoading] = useState<string | null>(null);

  if (!isOpen) return null;

  const plans = [
    {
      id: 'pro',
      name: 'Pro',
      price: '100 Stars',
      description: 'Ideal para creadores en crecimiento',
      features: [
        'Hasta 50 enlaces',
        'Analíticas por 90 días',
        'Todos los tipos de bloqueo (Pass, Pay)',
        'Score Boost x1.2'
      ],
      color: 'blue'
    },
    {
      id: 'business',
      name: 'Business',
      price: '300 Stars',
      description: 'Para perfiles profesionales y marcas',
      features: [
        'Hasta 500 enlaces',
        'Analíticas por 365 días',
        'Dominio personalizado (Próximamente)',
        'Score Boost x1.5'
      ],
      color: 'purple'
    }
  ];

  const handleUpgrade = async (planId: string) => {
    try {
      setLoading(planId);
      const { invoice_link } = await createInvoice(planId);
      
      if (WebApp) {
        WebApp.openInvoice(invoice_link, (status: string) => {
          if (status === 'paid') {
            onClose();
            // Refresh page or state
            window.location.reload();
          }
        });
      } else {
        window.open(invoice_link, '_blank');
      }
    } catch (err) {
      console.error('Error creating invoice:', err);
      alert('Error al generar la factura. Inténtalo de nuevo.');
    } finally {
      setLoading(null);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="bg-[#1c1c1e] w-full max-w-md rounded-3xl overflow-hidden border border-white/10 shadow-2xl animate-in zoom-in-95 duration-200">
        <div className="p-6 border-b border-white/5 flex items-center justify-between">
          <div>
            <h2 className="text-xl font-bold text-white">Mejorar Plan</h2>
            <p className="text-white/40 text-sm">Elige el nivel de tu perfil</p>
          </div>
          <button 
            onClick={onClose}
            className="p-2 hover:bg-white/5 rounded-full text-white/40 transition-colors"
          >
            <X size={24} />
          </button>
        </div>

        <div className="p-6 space-y-4 max-h-[70vh] overflow-y-auto custom-scrollbar">
          {plans.map((plan) => (
            <div 
              key={plan.id}
              className={`p-5 rounded-2xl border ${
                currentPlan === plan.id 
                  ? 'border-[#007aff] bg-[#007aff]/5' 
                  : 'border-white/5 bg-white/[0.02]'
              } relative overflow-hidden group`}
            >
              <div className="flex justify-between items-start mb-4">
                <div>
                  <h3 className="text-lg font-bold text-white flex items-center gap-2">
                    {plan.id === 'pro' ? <Zap size={18} className="text-blue-400" /> : <Shield size={18} className="text-purple-400" />}
                    {plan.name}
                  </h3>
                  <p className="text-xs text-white/40">{plan.description}</p>
                </div>
                <div className="text-right">
                  <span className="text-lg font-black text-white">{plan.price}</span>
                  <div className="text-[10px] text-white/30">Pago único (30 días)</div>
                </div>
              </div>

              <ul className="space-y-2 mb-6">
                {plan.features.map((feature, i) => (
                  <li key={i} className="flex items-center gap-2 text-xs text-white/70">
                    <Check size={14} className="text-green-500 shrink-0" />
                    {feature}
                  </li>
                ))}
              </ul>

              <button
                onClick={() => handleUpgrade(plan.id)}
                disabled={currentPlan === plan.id || loading !== null}
                className={`w-full py-3 rounded-xl font-bold text-sm transition-all flex items-center justify-center gap-2 ${
                  currentPlan === plan.id
                    ? 'bg-green-500/20 text-green-500 cursor-default'
                    : loading === plan.id
                      ? 'bg-white/10 text-white/50 animate-pulse'
                      : plan.id === 'pro'
                        ? 'bg-[#007aff] hover:bg-[#007aff]/90 text-white shadow-lg shadow-blue-500/20'
                        : 'bg-gradient-to-r from-purple-600 to-indigo-600 hover:opacity-90 text-white shadow-lg shadow-purple-500/20'
                }`}
              >
                {currentPlan === plan.id ? (
                  <>Tu plan actual</>
                ) : loading === plan.id ? (
                  <>Generando invoice...</>
                ) : (
                  <>
                    Upgrade now
                    <ExternalLink size={14} />
                  </>
                )}
              </button>
            </div>
          ))}
          
          <div className="p-4 bg-yellow-500/10 border border-yellow-500/20 rounded-xl flex gap-3">
            <Star size={20} className="text-yellow-500 shrink-0" />
            <p className="text-[10px] text-yellow-500/80 leading-relaxed">
              Los pagos se realizan a través de <b>Telegram Stars</b>. 1 Star equivale aproximadamente a 0.02 USD. 
              Recibirás un mensaje de confirmación del bot una vez completado el pago.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PaymentModal;
