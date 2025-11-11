import React, { createContext, useContext, useState, ReactNode } from 'react';

export interface BetSlipData {
  sport?: string;
  homeTeam?: string;
  awayTeam?: string;
  gameId?: string;
  commenceTime?: string;
  betType?: 'spread' | 'total' | 'moneyline' | 'prop';
  betSide?: string;
  line?: number;
  odds?: number;
  bookmaker?: string;
  confidence?: 'HIGH' | 'MEDIUM' | 'LOW' | 'CRITICAL';
  edgePercent?: number;
  strategy?: string;
}

interface BetSlipContextType {
  isOpen: boolean;
  betData: BetSlipData | null;
  openBetSlip: (data?: BetSlipData) => void;
  closeBetSlip: () => void;
  updateBetData: (data: Partial<BetSlipData>) => void;
}

const BetSlipContext = createContext<BetSlipContextType | undefined>(undefined);

export function BetSlipProvider({ children }: { children: ReactNode }) {
  const [isOpen, setIsOpen] = useState(false);
  const [betData, setBetData] = useState<BetSlipData | null>(null);

  const openBetSlip = (data?: BetSlipData) => {
    setBetData(data || null);
    setIsOpen(true);
  };

  const closeBetSlip = () => {
    setIsOpen(false);
    // Clear data after animation
    setTimeout(() => setBetData(null), 300);
  };

  const updateBetData = (data: Partial<BetSlipData>) => {
    setBetData(prev => ({ ...prev, ...data }));
  };

  return (
    <BetSlipContext.Provider value={{ isOpen, betData, openBetSlip, closeBetSlip, updateBetData }}>
      {children}
    </BetSlipContext.Provider>
  );
}

export function useBetSlip() {
  const context = useContext(BetSlipContext);
  if (!context) {
    throw new Error('useBetSlip must be used within BetSlipProvider');
  }
  return context;
}
